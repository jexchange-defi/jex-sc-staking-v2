import argparse
import getpass
import logging
from time import sleep

from multiversx_sdk_cli.accounts import Account
from multiversx_sdk_core import Address, TokenComputer
from multiversx_sdk_core.transaction_factories import (
    SmartContractTransactionsFactory, TransactionsFactoryConfig)
from multiversx_sdk_network_providers.proxy_network_provider import \
    ProxyNetworkProvider

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger()

GAS_LIMIT_BASE = 10_000_000
GAS_LIMIT_PER_ADDRESS = 4_000_000

SC_FACTORY = SmartContractTransactionsFactory(
    TransactionsFactoryConfig('1'),
    TokenComputer())


def _distribute(proxy: ProxyNetworkProvider,
                user: Account,
                sc_address: Address,
                limit: int):
    LOG.info('Distribute rewards')

    gas_limit = GAS_LIMIT_BASE + limit * GAS_LIMIT_PER_ADDRESS

    args = [limit]

    tx = SC_FACTORY.create_transaction_for_execute(
        sender=user.address,
        contract=sc_address,
        function='distributeRewards',
        gas_limit=gas_limit,
        arguments=args
    )

    tx.nonce = user.nonce

    user.nonce += 1

    tx.signature = bytes.fromhex(user.sign_transaction(tx))

    tx_hash = proxy.send_transaction(tx)

    logging.info(f"Transaction: {tx_hash}")


if __name__ == '__main__':
    LOG.info('Distribution tool')

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--sc_address', type=str,
                        default='erd1qqqqqqqqqqqqqpgqwkqnf30j7hj4r797kahr0p5t5nsksc8a73eqd732jd',
                        help='Staking smart contract address')
    parser.add_argument('--keyfile', type=str, required=True,
                        help='User key file')
    parser.add_argument('--gateway_url', type=str, default='https://gateway.multiversx.com',
                        help='MultiversX gateway')
    parser.add_argument('--repeat', type=int, default=1,
                        help='Iterate N times')
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

    sc_address = Address.from_bech32(args.sc_address)

    for i in range(0, args.repeat):
        LOG.info(f'Loop #{i}')
        _distribute(proxy,
                    user,
                    sc_address,
                    args.limit)
        sleep(1)
