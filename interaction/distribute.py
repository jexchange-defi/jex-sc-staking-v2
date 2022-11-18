import argparse
import getpass
import logging
from time import sleep

from erdpy.accounts import Account
from erdpy.proxy.core import ElrondProxy, NetworkConfig
from erdpy.proxy.messages import TransactionOnNetwork
from erdpy.transactions import Transaction
from utils import ensure_even_length

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger()

GAS_LIMIT_BASE = 10_000_000
GAS_LIMIT_PER_ADDRESS = 2_000_000


def _distribute(proxy: ElrondProxy, network: NetworkConfig, user: Account, sc_address: str, limit: int, no_wait: False):
    LOG.info('Distribute rewards')

    gas_limit = GAS_LIMIT_BASE + limit * GAS_LIMIT_PER_ADDRESS
    data = 'distribute'
    data += f'@{ensure_even_length(hex(limit)[2:])}'

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

    if no_wait:
        tx_hash = transaction.send(proxy)
        logging.info(f"Transaction: {tx_hash}")
    else:
        tx: TransactionOnNetwork = transaction.send_wait_result(proxy, 60)
        logging.info(f"Transaction: {tx.hash} - status {tx.raw['status']}")


if __name__ == '__main__':
    LOG.info('Distribution tool')

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--sc_address', type=str, required=True,
                        help='Staking smart contract address')
    parser.add_argument('--keyfile', type=str, required=True,
                        help='User key file')
    parser.add_argument('--gateway_url', type=str, required=True,
                        help='Elrond gateway')
    parser.add_argument('--repeat', type=int, default=1,
                        help='Iterate N times')
    parser.add_argument('--no_wait', action='store_true', default=False,
                        help='Do not wait for end of transaction')
    parser.add_argument('limit', type=int,
                        help='max number of addresses to process')

    args = parser.parse_args()
    if args.debug:
        LOG.setLevel(logging.DEBUG)

    password = getpass.getpass(prompt='Keyfile password: ')

    proxy = ElrondProxy(args.gateway_url)
    network = proxy.get_network_config()
    user = Account(key_file=args.keyfile, password=password)
    user.sync_nonce(proxy)

    for i in range(0, args.repeat):
        LOG.info(f'Loop #{i}')
        _distribute(proxy, network, user, args.sc_address,
                    args.limit, args.no_wait)
        sleep(1)
