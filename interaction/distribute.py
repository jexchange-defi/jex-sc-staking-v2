import argparse
import getpass
import logging
from time import sleep

from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_cli.contracts import SmartContract
from multiversx_sdk_network_providers.network_config import NetworkConfig
from multiversx_sdk_network_providers.proxy_network_provider import \
    ProxyNetworkProvider
from multiversx_sdk_network_providers.transactions import TransactionOnNetwork

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger()

GAS_LIMIT_BASE = 10_000_000
GAS_LIMIT_PER_ADDRESS = 4_000_000


def _distribute(proxy: ProxyNetworkProvider, network: NetworkConfig, user: Account, sc_address: str, limit: int, no_wait: False):
    LOG.info('Distribute rewards')

    gas_limit = GAS_LIMIT_BASE + limit * GAS_LIMIT_PER_ADDRESS

    sc = SmartContract(sc_address)

    args = [limit]
    tx = sc.execute(user, 'distributeRewards', args, network.min_gas_price,
                    gas_limit, 0, network.chain_id, network.min_transaction_version,
                    guardian='', options=0)

    user.nonce += 1

    if no_wait:
        tx_hash = tx.send(proxy)
        logging.info(f"Transaction: {tx_hash}")
    else:
        transaction_on_network: TransactionOnNetwork = tx.send_wait_result(
            proxy, 60)
        logging.info(f"Transaction: {transaction_on_network.hash}")
        if transaction_on_network.is_completed:
            status = transaction_on_network.status.status
        else:
            status = 'Unknown'
        logging.info(f"Transaction: {tx.hash} - status {status}")


if __name__ == '__main__':
    LOG.info('Distribution tool')

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--sc_address', type=str, required=True,
                        help='Staking smart contract address')
    parser.add_argument('--keyfile', type=str, required=True,
                        help='User key file')
    parser.add_argument('--gateway_url', type=str, default='https://gateway.multiversx.com',
                        help='MultiversX gateway')
    parser.add_argument('--repeat', type=int, default=1,
                        help='Iterate N times')
    parser.add_argument('--no_wait', action='store_true', default=False,
                        help='Do not wait for end of transaction')
    parser.add_argument('limit', type=int,
                        help='max number of addresses to process (eg 25 for 4 tokens)')

    args = parser.parse_args()
    if args.debug:
        LOG.setLevel(logging.DEBUG)

    password = getpass.getpass(prompt='Keyfile password: ')

    proxy = ProxyNetworkProvider(args.gateway_url)
    network = proxy.get_network_config()
    user = Account(key_file=args.keyfile, password=password)
    user.sync_nonce(proxy)

    for i in range(0, args.repeat):
        LOG.info(f'Loop #{i}')
        _distribute(proxy, network, user, args.sc_address,
                    args.limit, args.no_wait)
        sleep(1)
