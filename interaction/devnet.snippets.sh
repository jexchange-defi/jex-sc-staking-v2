PROJECT=..
KEYFILE="../../wallets/deployer-deprecated.json"
PROXY=https://devnet-gateway.elrond.com
SC_ADDRESS=$(erdpy data load --key=address-devnet)
CHAIN=D
JEX_TOKEN_ID="0x$(echo -n "XJEX-899465" | xxd -ps)"
SCRIPT_DIR=$(dirname $0)

source "${SCRIPT_DIR}/_common.snippets.sh"

deploy() {
    echo 'You are about to deploy SC on devnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract deploy --project=${PROJECT} --metadata-payable \
        --keyfile=${KEYFILE} --gas-limit=70000000 --outfile="deploy-devnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send || return

    SC_ADDRESS=$(erdpy data parse --file="deploy-devnet.interaction.json" --expression="data['contractAddress']")

    erdpy data store --key=address-devnet --value=${SC_ADDRESS}

    echo ""
    echo "Smart contract address: ${SC_ADDRESS}"
}

upgrade() {
    echo 'You are about to upgrade current SC on devnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract upgrade --project=${PROJECT} --metadata-payable \
        --keyfile=${KEYFILE} --gas-limit=70000000 --outfile="deploy-devnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send ${SC_ADDRESS} || return

    echo ""
    echo "Smart contract upgraded: ${SC_ADDRESS}"
}

CMD=$1
shift

$CMD $*
