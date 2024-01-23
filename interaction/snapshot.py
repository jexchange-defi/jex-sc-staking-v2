import argparse
import datetime
import getpass
import logging
import os
from itertools import chain, groupby
from typing import Tuple

import requests
from more_itertools import grouper
from multiversx_sdk_cli.accounts import Account, Address
from multiversx_sdk_cli.contracts import QueryResult, SmartContract
from multiversx_sdk_network_providers.network_config import NetworkConfig
from multiversx_sdk_network_providers.proxy_network_provider import \
    ProxyNetworkProvider
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork
from utils import hex2dec, str2hex

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger()

IGNORED_ADDRESS = [
    # treasury
    'erd1hmfwpvsqn8ktzw3dqd0ltpcyfyasgv8mr9w0qecnmpexyp280y8q47ca9d',
    # DAO
    'erd1ysc7l52t6pg0rkedwwwrld6zu55y2326dfx0maat68sapkl7c58q6kmvyt',
    # Fees wallet
    'erd1272et87h3sa7hlg5keuswh50guz2ngmd6lhmjxkwwu0ah6gdds5qhka964',
    # team (vested tokens)
    'erd1ysrm0kwsy3def8dmfwzrw68atepk0qadnu5sm2z6hv9e0ym2qwrsffuwjk',
    'erd19g9fa6tkqlvn5x2nuqvwlcmz943vpt5q3a92fkdsngu0zz62qpasyelgws',
    'erd155xlkeyqatck0qay99qk7qwerxc0efergug9k588uql4efm7yhwqqwkcsq',
    'erd1fx5rq2hllw4m8l5a2ax9a2cfyljhrf86t3r0c52858p233h9ekrsspj2wp',
    # JEX bot
    'erd1n83c3vhdsl7gac6xeuf5waf94x9tl6u552ajzckfygx9mkp69p6src9tjv',
    # LP deployer
    'erd1j770k2n46wzfn5g63gjthhqemu9r23n9tp7seu95vpz5gk5s6avsk5aams',
    # Raffle deployer
    'erd1063jk642gwa6whaqqhd4cz79kaxd4n2rwu35lq4924e7gwmr73eqhfxsgw',
    # Burn wallet
    'erd1rn79sxfs2ytqg60jy7mmu8gs37562ze7stm0tplrwglk7nnjm5uqzzmnc4',
    # Raffle receiver
    'erd1n0y5vzjv7hvuh4nj3acjcgh7frsfxjc3gq6nucx2numfjkhja0fqn7w3us'
]

HOLDERS_FILENAME = '.holders.csv'
REPORT_FILENAME = '.report.txt'
SNAPSHOT_CHUNK_SIZE = 100
GAS_LIMIT_BASE = 20_000_000
GAS_LIMIT_PER_ADDRESS = 1_500_000
NFT_HOLDING_JEX_EQIV = 100_000

# USD value of 1 LP token / 100 = multiplier
LP_MULTIPLIERS = [("LPETHBTC-8b8a1f", 0.88),
                  ("LPETHEGLD-bcb4ac", 0.93),
                  ("LPJEXUSDT-732142", 0.83),
                  ("LPJEXWEGLD-2bccc4", 0.87),
                  ("LPJEXWETH-2a2e52", 0.80),
                  ("LPJEXBEE-a6fd37", 66.15),
                  ("LPJEXRARE-518166", 1.07),
                  ("LPJACKCOAT-d49dd4", 0.12),
                  ("LPUSDCUSDT-fd8cf1", 0.01)]
LPS_POOL_SIZE = 100_000_000 * 10**18


def _is_valid_holder(address: str) -> bool:
    return not address.startswith('erd1qqqqqqqqqqq') \
        and not address in IGNORED_ADDRESS


def _parse_address_and_lock(hex_: str):
    offset = 0

    address = Address(hex_[offset: offset+64])
    offset += 64

    len_ = int(hex_[offset: offset+8], base=16)
    offset += 8

    # locked_amount = int(hex_[offset: offset + 2*len_], base=16)
    offset += 2 * len_  # locked amount

    offset += 16  # unlock epoch
    offset += 16  # remaining_epochs
    offset += 8  # len reward power

    reward_power = int(hex_[offset:], base=16)

    return {
        'address': address.bech32(),
        'balance': reward_power
    }


def _fetch_token_info(api_url: str, token_identifier: str):
    LOG.info(f'Fetching token {token_identifier} info')

    url = f'{api_url}/tokens/{token_identifier}'
    LOG.debug(f'url={url}')
    resp = requests.get(url)
    assert resp.status_code == 200, f'Error fetching token {token_identifier} info'

    json_ = resp.json()
    return {
        'token_identifier': token_identifier,
        'decimals': json_['decimals']
    }


def _fetch_token_holders(api_url: str, token_identifier: str):
    from_ = 0
    size = 1000
    while True:
        url = f'{api_url}/tokens/{token_identifier}/accounts?from={from_}&size={size}'
        LOG.info(url)
        resp = requests.get(url)

        if resp.status_code >= 204:
            return

        if resp.status_code == 200:
            json_ = resp.json()
            if len(json_) == 0:
                return
            for holder in json_:
                yield holder
            if len(json_) < size:
                return

        from_ += size


def _fetch_rolling_ballz_holders(api_url: str, jex_token_decimals: int):
    from_ = 0
    size_ = 50
    while True:
        url = f'{api_url}/nfts/JAVIERD-47e517-15/accounts?from={from_}&size={size_}'
        LOG.info(url)
        response = requests.get(url)

        if response.status_code >= 204:
            return

        if response.status_code == 200:
            json_ = response.json()
            if len(json_) == 0:
                return
            for holder in json_:
                holder['balance'] = int(holder['balance']) * NFT_HOLDING_JEX_EQIV * \
                    10**jex_token_decimals
                yield holder
            if len(json_) < size_:
                return
        from_ += size_


def _fetch_one_dex_dual_farming(proxy: ProxyNetworkProvider, onedex_farming_sc_address: str):
    """ Stakers of LP token on OneDex (dual farming) """

    pool_id = '0000000e'
    url = f'{proxy.url}/address/{onedex_farming_sc_address}/keys'
    pairs = requests.get(url).json()['data']['pairs']
    prefix = f"{str2hex('pool_user_stake_amount')}{pool_id}"
    for key, value in pairs.items():
        if key.startswith(prefix):
            address = Address(key[len(prefix):])
            balance = hex2dec(value)
            # print(f'{address.bech32()}: {balance}')
            yield {
                'address': address.bech32(),
                'balance': str(balance)
            }


def _fetch_onedex_lp_holders(proxy: ProxyNetworkProvider, api_url: str, lp_token_identifier: str,
                             onedex_sc_address: str, onedex_farming_sc_address: str):
    """ Just holders of LP token (not staked) """

    pool_id = '00000010'
    jex_reserve_key = f"{str2hex('pair_first_token_reserve')}{pool_id}"
    lp_supply_key = f"{str2hex('pair_lp_token_supply')}{pool_id}"

    url = f'{proxy.url}/address/{onedex_sc_address}/key/{jex_reserve_key}'
    jex_reserve = hex2dec(requests.get(url).json()['data']['value'])

    url = f'{proxy.url}/address/{onedex_sc_address}/key/{lp_supply_key}'
    lp_supply = hex2dec(requests.get(url).json()['data']['value'])

    lp_holders = _fetch_token_holders(api_url, lp_token_identifier)
    stakers = _fetch_one_dex_dual_farming(proxy, onedex_farming_sc_address)

    for lp_holder in chain(lp_holders, stakers):
        jex_bal = jex_reserve * int(lp_holder['balance']) / lp_supply
        jex_bal = round(jex_bal)
        yield {
            'address': lp_holder['address'],
            'balance': str(jex_bal)
        }


def _fetch_jex_lp_holders(api_url: str):
    """
    Fetch JEX LP token holders.
    All holders will share a pool of 100M JEX (this number may evolve) based on their balance of LP tokens * multiplier.
    """

    all_holders = []
    for (token_id, multiplier) in LP_MULTIPLIERS:
        LOG.info(f'Fetching holders of {token_id} (x{multiplier})')

        holders = _fetch_token_holders(api_url, token_id)
        holders = map(lambda x: {
            'address': x['address'],
            'balance': int(x['balance']) * multiplier}, holders)

        all_holders.extend(holders)

    sum_balances = sum(map(lambda x: x['balance'], all_holders))
    groups = groupby(all_holders, lambda x: x['address'])

    for (address, data) in groups:
        yield {
            'address': address,
            'balance': sum(map(lambda x: LPS_POOL_SIZE * x['balance'] / sum_balances, data))
        }


def _fetch_jex_lockers(proxy: ProxyNetworkProvider, token_decimals: int):
    LOG.info('Fetch JEX lockers')

    sc = SmartContract(
        'erd1qqqqqqqqqqqqqpgq05whpg29ggrrm9ww3ufsf9ud23f66msv6avs5s5xxy')

    from_ = 0
    size_ = 200

    lockers = []
    while True:
        resp = sc.query(proxy, 'getAllLocks', [from_, size_])

        if len(resp) > 0 and isinstance(resp[0], QueryResult):
            lockers.extend([_parse_address_and_lock(qr.hex) for qr in resp])
        elif resp == []:
            break
        else:
            LOG.error('Error while fetching lockers')
            LOG.info(resp)
            exit(1)

        from_ += size_

    total_points = sum([l["balance"] for l in lockers]) // 10**token_decimals
    LOG.info(f'Nb lockers: {len(lockers)}')
    LOG.info(f'Total reward power from lockers: {total_points:,}')

    return lockers


def _export_holders(api_url: str,
                    proxy: ProxyNetworkProvider,
                    token_identifier: str,
                    min_amount: int,
                    lp_token_identifier: str,
                    onedex_sc_address: str,
                    onedex_farming_sc_address: str):
    LOG.info(f'Export holders of {token_identifier}')

    token_info = _fetch_token_info(api_url, token_identifier)
    token_decimals = token_info['decimals']

    nb = 0
    total_hbal = 0

    with open(HOLDERS_FILENAME, 'wt') as out:

        jex_holders = _fetch_token_holders(api_url, token_identifier)

        jex_ballz_holders = _fetch_rolling_ballz_holders(
            api_url, token_decimals)

        onedex_lp_holders = _fetch_onedex_lp_holders(
            proxy, api_url, lp_token_identifier, onedex_sc_address, onedex_farming_sc_address)

        jex_lp_holders = _fetch_jex_lp_holders(api_url)

        jex_lockers = _fetch_jex_lockers(proxy, token_decimals)

        all_holders = chain(
            jex_holders,
            jex_ballz_holders,
            onedex_lp_holders,
            jex_lp_holders,
            jex_lockers)

        # print([h for h in all_holders if h['address'] == ''])

        all_holders = filter(
            lambda x: _is_valid_holder(x['address']), all_holders)
        all_holders = sorted(all_holders, key=lambda x: x['address'])

        groups = groupby(all_holders, lambda x: x['address'])
        all_holders = [{
            'address': address,
            'balance': sum(map(lambda x: int(x['balance']), data))
        } for (address, data) in groups]

        all_holders = filter(lambda x: int(
            x['balance']) / 10**token_decimals >= min_amount, all_holders)

        all_holders = sorted(
            all_holders, key=lambda x: x['balance'], reverse=True)

        for holder in all_holders:
            bal = holder['balance']
            nb += 1
            hbal = int(bal / 10**token_decimals)
            line = f"{nb};{holder['address']};{bal};{hbal};"
            # print(line)
            out.write(line)
            out.write("\n")
            total_hbal += hbal

    LOG.info(f'Total points: {int(total_hbal):,}')


def _register_holders(proxy: ProxyNetworkProvider, network: NetworkConfig, sc_address, holders):
    LOG.info('Register holders chunk')

    gas_limit = GAS_LIMIT_BASE
    data = 'snapshotHolders'
    processed_holders = []
    args = []
    for holder in holders:
        LOG.info(holder['address'])

        args.append(Address(holder['address']))
        args.append(int(holder['balance']))

        gas_limit += GAS_LIMIT_PER_ADDRESS
        processed_holders.append(holder['address'])
    LOG.debug(f'data={data}')

    sc = SmartContract(sc_address)
    tx = sc.execute(user, 'snapshotHolders', args, network.min_gas_price,
                    gas_limit, 0, network.chain_id, network.min_transaction_version,
                    guardian='', options=0)

    user.nonce += 1

    tx: TransactionOnNetwork = tx.send_wait_result(
        proxy, 60)
    logging.info(f"Transaction: {tx.hash}")

    if tx.is_completed:
        status = tx.status.status
    else:
        status = 'Unknown'
    _report_add(processed_holders, status)


def _report_init():
    with open(REPORT_FILENAME, 'a') as out:
        out.write("\n\n")
        out.write('---------------\n')
        out.write('Snapshot report\n')
        out.write(f"{datetime.datetime.utcnow().isoformat()}\n")
        out.write('---------------\n')
        out.write("\n\n")


def _report_add(addresses, status):
    LOG.info('Updating report')

    with open(REPORT_FILENAME, mode='a') as out:
        out.write('------- CHUNK -------\n')
        for address in addresses:
            out.write(f"{address};{status};\n")


def _parse_csv_line(line: str) -> dict:
    arr_ = line.split(';')
    return {
        'address': arr_[1],
        'balance': arr_[2]
    }


def _register_all_holders(proxy: ProxyNetworkProvider, user: Account, sc_address: str):
    LOG.info(f'Register holders to SC {sc_address}')

    network = proxy.get_network_config()
    user.sync_nonce(proxy)

    _report_init()

    with open(HOLDERS_FILENAME, 'rt') as holders_file:
        lines = holders_file.readlines()
        lines = map(_parse_csv_line, lines)
        chunks = grouper(lines, SNAPSHOT_CHUNK_SIZE, fillvalue=None)
        for chunk in chunks:
            chunk = filter(lambda x: x is not None, chunk)
            _register_holders(proxy, network, sc_address, chunk)


if __name__ == '__main__':
    LOG.info('Snapshot tool')

    parser = argparse.ArgumentParser()
    parser.add_argument('--api_url', type=str, default='https://api.multiversx.com',
                        help='MultiversX API (mandatory for "export_holders" action)')
    parser.add_argument('--debug',
                        action='store_true')
    parser.add_argument('--lp_token_identifier', type=str, default='JEXWEGLD-15791b',
                        help='(mandatory for "export_holders" action)')
    parser.add_argument('--token_identifier', type=str, default='JEX-9040ca',
                        help='(mandatory for "export_holders" action)')
    parser.add_argument('--onedex_sc_address', type=str, default='erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc',
                        help='(mandatory for "export_holders" action)')
    parser.add_argument('--onedex_farming_sc_address', type=str, default='erd1qqqqqqqqqqqqqpgq5774jcntdqkzv62tlvvhfn2y7eevpty6mvlszk3dla',
                        help='(mandatory for "export_holders" action)')
    parser.add_argument('--min_amount', type=int, default=5000,
                        help='minimum amount of tokens to hold (mandatory for "export_holders" action)')
    parser.add_argument('--gateway_url', type=str, default='https://gateway.multiversx.com',
                        help='MultiversX gateway')
    parser.add_argument('--sc_address', type=str,
                        help='Staking smart contract address (mandatory for "register_holders" action)')
    parser.add_argument('--keyfile', type=str,
                        help='User key file (mandatory for "register_holders" action)')
    parser.add_argument('action', type=str,
                        help='"export_holders" or "register_holders"')

    args = parser.parse_args()
    if args.debug:
        LOG.setLevel(logging.DEBUG)

    proxy = ProxyNetworkProvider(args.gateway_url)

    if args.action == 'export_holders':
        assert args.api_url is not None, '--api_url is mandatory for "export_holders action"'
        assert args.token_identifier is not None, '--token_identifier is mandatory for "export_holders action"'
        assert args.min_amount is not None, '--min_amount is mandatory for "export_holders action"'
        _export_holders(args.api_url, proxy,
                        args.token_identifier,
                        args.min_amount,
                        args.lp_token_identifier,
                        args.onedex_sc_address,
                        args.onedex_farming_sc_address)

    if args.action == 'register_holders':
        assert args.sc_address is not None, '--sc_address is mandatory for "register_holders" action"'
        assert args.keyfile is not None, '--keyfile is mandatory for "register_holders" action"'

        password = getpass.getpass(prompt='Keyfile password: ')

        user = Account(key_file=args.keyfile, password=password)
        _register_all_holders(proxy, user, args.sc_address)
