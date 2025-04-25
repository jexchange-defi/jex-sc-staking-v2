import argparse
import datetime
import getpass
import json
import logging
from itertools import chain, groupby
from typing import Any, Mapping

import requests
from more_itertools import grouper
from multiversx_sdk_cli.accounts import Account, Address
from multiversx_sdk_cli.contracts import QueryResult, SmartContract
from multiversx_sdk_network_providers.network_config import NetworkConfig
from multiversx_sdk_network_providers.proxy_network_provider import \
    ProxyNetworkProvider
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

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


def _is_valid_holder(address: str) -> bool:
    return not address.startswith('erd1qqqqqqqqqqq') \
        and not address in IGNORED_ADDRESS


def _parse_address_and_lock(hex_: str):
    offset = 0

    address = Address(hex_[offset: offset+64])
    offset += 64

    len_ = int(hex_[offset: offset+8], base=16)
    offset += 8

    locked_amount = int(hex_[offset: offset + 2*len_], base=16)
    offset += 2 * len_  # locked amount

    offset += 16  # unlock epoch

    remaining_epochs = int(hex_[offset: offset+16], base=16)
    offset += 16  # remaining_epochs

    remaining_epochs_maxxed = max(0, min(remaining_epochs, 180))
    reward_power = (locked_amount * remaining_epochs_maxxed * 4) // 180

    return {
        'address': address.bech32(),
        'reward_power': reward_power
    }


def _fetch_token_prices() -> Mapping[str, float]:
    LOG.info('Fetching token prices')

    api_key = input('Agg API key: ')

    url = 'https://agg-api.jexchange.io/tokens'
    LOG.debug(f'url={url}')
    resp = requests.get(url, headers={'x-api-key': api_key})
    assert resp.status_code == 200, 'Error fetching token prices'

    json_ = resp.json()

    return dict([x['identifier'], x['usdPrice']] for x in json_)


def _fetch_token_info(api_url: str, token_identifier: str):
    LOG.info(f'Fetching token {token_identifier} info')

    url = f'{api_url}/tokens/{token_identifier}'
    LOG.debug(f'url={url}')
    resp = requests.get(url)
    assert resp.status_code == 200, f'Error fetching token {token_identifier} info'

    json_ = resp.json()
    return {
        'identifier': token_identifier,
        'decimals': json_['decimals'],
        'usdPrice': json_['price']
    }


def _fetch_token_holders(api_url: str, token_identifier: str):
    from_ = 0
    size = 10000
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


def _fetch_rolling_ballz_holders_v2(api_url: str):
    holders = []

    from_ = 0
    size_ = 50
    while True:
        url = f'{api_url}/nfts/JAVIERD-47e517-16/accounts?from={from_}&size={size_}'
        LOG.info(url)
        response = requests.get(url)

        if response.status_code >= 204:
            break

        if response.status_code == 200:
            json_ = response.json()

            if len(json_) == 0:
                break

            for holder in json_:
                holder['ballz'] = holder['balance']
                holders.append({
                    'address': holder['address'],
                    'nb_ballz': int(holder['balance'])
                })

            if len(json_) < size_:
                break

        from_ += size_

    return holders


def _fetch_jex_lp_holders(api_url: str,
                          pools_info: list[Any]):
    LOG.info('Fetch LP holders')

    all_holders = []

    for pool_info in pools_info:
        token_id = pool_info['lp_token_identifier']
        multiplier = pool_info['earn_multiplier']

        LOG.info(f'Fetching holders of {token_id} (x{multiplier})')

        pool_info = next((p for p in pools_info
                          if p['lp_token_identifier'] == token_id))

        share_usd_value = pool_info['usd_value_per_lp_token']

        holders = _fetch_token_holders(api_url, token_id)
        holders = map(lambda x: {
            'address': x['address'],
            'usd_balance': int(x['balance']) * share_usd_value * multiplier / 10**pool_info['lp_token']['decimals']}, holders)

        all_holders.extend(holders)

    groups = groupby(all_holders, lambda x: x['address'])

    return [{
            'address': address,
            'usd_balance': sum((x['usd_balance'] for x in data))
            }
            for (address, data) in groups]


def _fetch_jex_lockers(proxy: ProxyNetworkProvider,
                       token_info: dict):
    LOG.info('Fetch JEX lockers')

    sc = SmartContract(
        'erd1qqqqqqqqqqqqqpgq05whpg29ggrrm9ww3ufsf9ud23f66msv6avs5s5xxy')

    from_ = 0
    size_ = 200

    lockers = []
    while True:
        resp = sc.query(proxy, 'getAllLocks', [from_, size_])

        if len(resp) > 0 and isinstance(resp[0], QueryResult):
            new_lockers = [_parse_address_and_lock(qr.hex) for qr in resp]
            lockers.extend(({
                'address': x['address'],
                'reward_power': x['reward_power'] / 10**token_info['decimals']
            } for x in new_lockers))
        elif resp == []:
            break
        else:
            LOG.error('Error while fetching lockers')
            LOG.info(resp)
            exit(1)

        from_ += size_

    return lockers


def _fetch_pools_info():
    LOG.info('Fetching pools info')

    resp = requests.get('https://api.jexchange.io/pools/v3')
    assert resp.status_code == 200, 'Error while fetching pools info'

    json_ = resp.json()

    return [p for p in json_
            if p['earn_multiplier'] > 0]


def _export_holders(api_url: str,
                    proxy: ProxyNetworkProvider,
                    token_identifier: str,
                    min_amount: int):
    LOG.info(f'Export holders of {token_identifier}')

    ##

    token_prices = _fetch_token_prices()
    LOG.info(f'Token prices ({len(token_prices)})')
    input('Press Enter to continue')

    ##

    token_info = _fetch_token_info(api_url, token_identifier)
    token_decimals = token_info['decimals']

    LOG.info(f'Token: {token_identifier}')
    LOG.info(f'Decimals: {token_decimals}')
    input('Press Enter to continue')

    ##

    pools_info = _fetch_pools_info()

    LOG.info(f'Pools ({len(pools_info)})')

    LOG.info('Fix USD value of LP tokens')
    pools_info = [_fix_pool_usd_value(p,
                                      token_prices=token_prices)
                  for p in pools_info
                  if int(p['lp_token_supply']) > 0
                  and sum(p['reserves_usd_value']) >= 10]

    LOG.info(f'Pools ({len(pools_info)})')

    for p in pools_info:
        sum_usd_values = sum(p['reserves_usd_value'])
        sum_usd_values_from_lp_token = p['usd_value_per_lp_token'] * \
            int(p['lp_token_supply']) / 10**p['lp_token']['decimals']
        diff = abs(sum_usd_values_from_lp_token - sum_usd_values)
        diff_percent = diff / sum_usd_values

        LOG.info(f"{p['lp_token_identifier']}"
                 f" :: {['{:.2f}'.format(x) for x in p['reserves_usd_value']]}"
                 f" :: {sum_usd_values:.2f}"
                 f" :: {sum_usd_values_from_lp_token:.2f}"
                 f" :: {p['usd_value_per_lp_token']:.2f}"
                 f" :: X{p['earn_multiplier']}"
                 f" :: {'OK' if diff_percent < 1 else 'CHECK ****'}")

    input('Press Enter to continue')

    nb = 0

    with open(HOLDERS_FILENAME, 'wt') as out:

        jex_ballz_holders_v2 = _fetch_rolling_ballz_holders_v2(api_url)

        total_nb_ballz = sum(h["nb_ballz"] for h in jex_ballz_holders_v2)

        LOG.info(f'Nb ballz holders: {len(jex_ballz_holders_v2)}')
        LOG.info(f'Nb ballz: {total_nb_ballz:,}')

        input('Press Enter to continue')

        jex_lockers = _fetch_jex_lockers(proxy,
                                         token_info=token_info)

        total_reward_power = sum([l['reward_power']
                                  for l in jex_lockers])

        LOG.info(f'Nb lockers: {len(jex_lockers)}')
        LOG.info('Total reward power from lockers: '
                 f'{int(total_reward_power):,}')

        input('Press Enter to continue')

        jex_lp_holders = _fetch_jex_lp_holders(api_url,
                                               pools_info)

        total_lp_holders_usd_value = sum((l['usd_balance']
                                          for l in jex_lp_holders))

        LOG.info(f'Nb LP holders: {len(jex_lp_holders)}')
        LOG.info('Total LP USD value: '
                 f'{int(total_lp_holders_usd_value):,}')

        input('Press Enter to continue')

        all_holders = chain(
            jex_ballz_holders_v2,
            jex_lp_holders,
            jex_lockers
        )

        all_holders = (h
                       for h in all_holders
                       if _is_valid_holder(h['address']))

        all_holders = sorted(all_holders,
                             key=lambda x: x['address'])

        groups = groupby(all_holders, lambda x: x['address'])

        all_holders = []

        for address, data in groups:
            data = list(data)

            nb_ballz = sum((x.get('nb_ballz', 0) for x in data))
            reward_power = sum((x.get('reward_power', 0) for x in data))
            usd_balance = sum((x.get('usd_balance', 0) for x in data))
            points = (nb_ballz * NFT_HOLDING_JEX_EQIV) \
                + reward_power \
                + (total_reward_power * usd_balance / total_lp_holders_usd_value)

            if points >= min_amount:
                all_holders.append({
                    'address': address,
                    'nb_ballz': nb_ballz,
                    'reward_power': reward_power,
                    'usd_balance': usd_balance,
                    'points': points
                })

        all_holders = sorted(all_holders,
                             key=lambda x: x['points'],
                             reverse=True)

        total_points = 0

        for h in all_holders:
            nb += 1
            points = int(h['points'])
            line = f"{nb};{h['address']};{points};{h['nb_ballz']};{h['reward_power']:.2f};{h['usd_balance']:.2f}"
            # print(line)
            out.write(line)
            out.write("\n")
            total_points += points

    LOG.info(f'Nb ballz: {total_nb_ballz:,}')

    LOG.info('Total reward power from lockers: '
             f'{int(total_reward_power):,}')

    LOG.info('Total LP USD value: '
             f'{int(total_lp_holders_usd_value):,}')

    LOG.info(f'Total points: {int(total_points):,}')


def _fix_pool_usd_value(pool_info: Any,
                        token_prices: dict[str, float]) -> Any:
    lp_token_supply = int(pool_info['lp_token_supply'])

    pool_info['reserves_usd_value'] = [token_prices[t['identifier']] * int(r) / 10**t['decimals']
                                       for t, r in zip(pool_info['tokens'],
                                                       pool_info['reserves'])]

    total_usd_value = sum(pool_info['reserves_usd_value'])

    pool_info['usd_value_per_lp_token'] = total_usd_value * \
        10**pool_info['lp_token']['decimals'] / lp_token_supply

    return pool_info


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
    parser.add_argument('--token_identifier', type=str, default='JEX-9040ca',
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
                        args.min_amount)

    if args.action == 'register_holders':
        assert args.sc_address is not None, '--sc_address is mandatory for "register_holders" action"'
        assert args.keyfile is not None, '--keyfile is mandatory for "register_holders" action"'

        password = getpass.getpass(prompt='Keyfile password: ')

        user = Account(key_file=args.keyfile, password=password)
        _register_all_holders(proxy, user, args.sc_address)
