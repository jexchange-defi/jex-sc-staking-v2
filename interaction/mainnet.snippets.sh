BYTECODE=../output/jex-sc-staking-v2.wasm
KEYFILE="../../wallets/deployer.json"
PROXY=https://gateway.multiversx.com
SC_ADDRESS=$(mxpy data load --key=address-mainnet)
CHAIN=1
JEX_TOKEN_ID="0x$(echo -n "JEX-9040ca" | xxd -ps)"
SCRIPT_DIR=$(dirname $0)

source "${SCRIPT_DIR}/_common.snippets.sh"

deploy() {
    echo 'You are about to deploy SC on mainnet (Ctrl-C to abort)'
    read answer

    mxpy contract deploy --bytecode=${BYTECODE} --metadata-payable \
        --keyfile=${KEYFILE} --gas-limit=70000000 --outfile="deploy-mainnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send || return

    SC_ADDRESS=$(mxpy data parse --file="deploy-mainnet.interaction.json" --expression="data['contractAddress']")

    mxpy data store --key=address-mainnet --value=${SC_ADDRESS}

    echo ""
    echo "Smart contract address: ${SC_ADDRESS}"
}

upgrade() {
    echo 'You are about to upgrade current SC on mainnet (Ctrl-C to abort)'
    read answer

    mxpy contract upgrade --bytecode=${BYTECODE} --metadata-payable \
        --keyfile=${KEYFILE} --gas-limit=70000000 --outfile="deploy-mainnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send ${SC_ADDRESS} || return

    echo ""
    echo "Smart contract upgraded: ${SC_ADDRESS}"
}

CMD=$1
shift

$CMD $*
