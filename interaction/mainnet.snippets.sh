PROJECT=..
USER="../wallets/owner.pem"
PROXY=https://gateway.elrond.com
SC_ADDRESS=$(erdpy data load --key=address-mainnet)
CHAIN=1
JEX_TOKEN_ID="0x$(echo -n "JEX-9040ca" | xxd -ps)"

echo "SC address: ${SC_ADDRESS}"

deploy() {
    echo 'You are about to deploy SC on mainnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract deploy --project=${PROJECT} --metadata-payable \
        --arguments "${JEX_TOKEN_ID}" \
        --pem=${USER} --gas-limit=40000000 --send --outfile="deploy-mainnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce  || return

    SC_ADDRESS=$(erdpy data parse --file="deploy-devnet.interaction.json" --expression="data['emitted_tx']['address']")

    erdpy data store --key=address-mainnet --value=${SC_ADDRESS}

    echo ""
    echo "Smart contract address: ${SC_ADDRESS}"
}

upgrade() {
    echo 'You are about to upgrade current SC on mainnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract upgrade --project=${PROJECT} --metadata-payable \
        --arguments "${JEX_TOKEN_ID}" \
        --pem=${USER} --gas-limit=40000000 --outfile="deploy-mainnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send ${SC_ADDRESS} || return

    echo ""
    echo "Smart contract upgraded: ${SC_ADDRESS}"
}


CMD=$1
shift

$CMD $*
