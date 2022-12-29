import argparse
import datetime
import getpass
import logging

import requests
from erdpy.accounts import Account, Address
from erdpy.proxy.core import ElrondProxy, NetworkConfig
from erdpy.proxy.messages import TransactionOnNetwork
from erdpy.transactions import Transaction
from more_itertools import grouper
from utils import ensure_even_length

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger()

IGNORED_ADDRESS = [
    # treasury
    'erd1hmfwpvsqn8ktzw3dqd0ltpcyfyasgv8mr9w0qecnmpexyp280y8q47ca9d',
    # DAO
    'erd1ysc7l52t6pg0rkedwwwrld6zu55y2326dfx0maat68sapkl7c58q6kmvyt',
    # team
    'erd1ysrm0kwsy3def8dmfwzrw68atepk0qadnu5sm2z6hv9e0ym2qwrsffuwjk',
    'erd19g9fa6tkqlvn5x2nuqvwlcmz943vpt5q3a92fkdsngu0zz62qpasyelgws',
    'erd155xlkeyqatck0qay99qk7qwerxc0efergug9k588uql4efm7yhwqqwkcsq'
]

HOLDERS_FILENAME = '.holders.csv'
REPORT_FILENAME = '.report.txt'
SNAPSHOT_CHUNK_SIZE = 100
GAS_LIMIT_BASE = 10_000_000
GAS_LIMIT_PER_ADDRESS = 1_500_000


def _is_valid_holder(address: str) -> bool:
    return not address.startswith('erd1qqqqqqqqqqq') \
        and not address in IGNORED_ADDRESS


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


def _export_holders(api_url: str, token_identifier: str, min_amount: int):
    LOG.info(f'Export holders of {token_identifier}')

    token_info = _fetch_token_info(api_url, token_identifier)
    token_decimals = token_info['decimals']

    from_ = 0
    size = 100
    nb = 0
    total_hbal = 0

    with open(HOLDERS_FILENAME, 'wt') as out:
        while True:
            resp = requests.get(
                f'{api_url}/tokens/{token_identifier}/accounts?from={from_}&size={size}')

            if resp.status_code >= 204:
                return

            json_ = resp.json()
            if len(json_) == 0:
                break

            holders = json_
            holders = filter(lambda x: _is_valid_holder(x['address']), holders)
            holders = filter(lambda x: int(
                x['balance']) / 10**token_decimals >= min_amount, holders)
            holders = list(holders)

            if len(holders) == 0:
                break

            for holder in holders:
                nb += 1
                bal = int(holder['balance'])
                hbal = int(bal / 10**token_decimals)
                line = f"{nb};{holder['address']};{bal};{hbal};"
                print(line)
                out.write(line)
                out.write("\n")
                total_hbal += hbal

            from_ += size

    LOG.info(f'Total {token_identifier} held: {int(total_hbal):,}')


def _register_holders(proxy: ElrondProxy, network: NetworkConfig, sc_address, holders):
    LOG.info('Register holders chunk')

    gas_limit = GAS_LIMIT_BASE
    data = 'snapshotHolders'
    processed_holders = []
    for holder in holders:
        LOG.info(holder['address'])

        hexbal = hex(int(holder['balance']))[2:]
        data += f"@{Address(holder['address']).hex()}"
        data += f'@{ensure_even_length(hexbal)}'

        gas_limit += GAS_LIMIT_PER_ADDRESS
        processed_holders.append(holder['address'])
    LOG.debug(f'data={data}')

    transaction = Transaction()
    transaction.nonce = user.nonce
    transaction.sender = user.address.bech32()
    transaction.receiver = sc_address
    transaction.data = data
    transaction.gasPrice = network.min_gas_price
    transaction.gasLimit = gas_limit
    transaction.chainID = network.chain_id
    transaction.version = network.min_tx_version
    transaction.sign(user)
    user.nonce += 1

    tx: TransactionOnNetwork = transaction.send_wait_result(proxy, 60)
    logging.info(f"Transaction: {tx.get_hash()}")

    if tx.is_done():
        status = tx.raw['status']
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


def _register_all_holders(proxy: ElrondProxy, user: Account, sc_address: str):
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
    parser.add_argument('--api_url', type=str,
                        help='Elrond API (mandatory for "export_holders" action)')
    parser.add_argument('--debug',
                        action='store_true')
    parser.add_argument('--token_identifier', type=str,
                        help='(mandatory for "export_holders" action)')
    parser.add_argument('--min_amount', type=int,
                        help='minimum amount of tokens to hold (mandatory for "export_holders" action)')
    parser.add_argument('--sc_address', type=str,
                        help='Staking smart contract address (mandatory for "register_holders" action)')
    parser.add_argument('--keyfile', type=str,
                        help='User key file (mandatory for "register_holders" action)')
    parser.add_argument('--gateway_url', type=str,
                        help='Elrond gateway (mandatory for "register_holders" action)')
    parser.add_argument('action', type=str,
                        help='"export_holders" or "register_holders"')

    args = parser.parse_args()
    if args.debug:
        LOG.setLevel(logging.DEBUG)

    if args.action == 'export_holders':
        assert args.api_url is not None, '--api_url is mandatory for "export_holders action"'
        assert args.token_identifier is not None, '--token_identifier is mandatory for "export_holders action"'
        assert args.min_amount is not None, '--min_amount is mandatory for "export_holders action"'
        _export_holders(args.api_url, args.token_identifier, args.min_amount)

    if args.action == 'register_holders':
        assert args.sc_address is not None, '--sc_address is mandatory for "register_holders" action"'
        assert args.gateway_url is not None, '--gateway_url is mandatory for "register_holders" action"'
        assert args.keyfile is not None, '--keyfile is mandatory for "register_holders" action"'

        password = getpass.getpass(prompt='Keyfile password: ')

        proxy = ElrondProxy(args.gateway_url)
        user = Account(key_file=args.keyfile, password=password)
        _register_all_holders(proxy, user, args.sc_address)
