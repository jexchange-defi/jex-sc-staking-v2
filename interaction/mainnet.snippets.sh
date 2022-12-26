PROJECT=..
KEYFILE="../wallets/deployer.json"
PROXY=https://gateway.elrond.com
SC_ADDRESS=$(erdpy data load --key=address-mainnet)
CHAIN=1
JEX_TOKEN_ID="0x$(echo -n "JEX-9040ca" | xxd -ps)"
SCRIPT_DIR=$(dirname $0)

source "${SCRIPT_DIR}/_common.snippets.sh"

deploy() {
    echo 'You are about to deploy SC on mainnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract deploy --project=${PROJECT} --metadata-payable \
        --keyfile=${KEYFILE} --gas-limit=70000000 --outfile="deploy-mainnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send || return

    SC_ADDRESS=$(erdpy data parse --file="deploy-mainnet.interaction.json" --expression="data['contractAddress']")

    erdpy data store --key=address-mainnet --value=${SC_ADDRESS}

    echo ""
    echo "Smart contract address: ${SC_ADDRESS}"
}

upgrade() {
    echo 'You are about to upgrade current SC on mainnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract upgrade --project=${PROJECT} --metadata-payable \
        --keyfile=${KEYFILE} --gas-limit=70000000 --outfile="deploy-mainnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send ${SC_ADDRESS} || return

    echo ""
    echo "Smart contract upgraded: ${SC_ADDRESS}"
}

CMD=$1
shift

$CMD $*
