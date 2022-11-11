PROJECT=..
USER="../wallets/owner.pem"
PROXY=https://devnet-gateway.elrond.com
ADDRESS=$(erdpy data load --key=address-devnet)
CHAIN=D
JEX_TOKEN_ID="0x$(echo -n "XJEX-899465" | xxd -ps)"

echo "SC address: ${ADDRESS}"

deploy() {
    echo 'You are about to deploy SC on devnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract deploy --project=${PROJECT} \
        --arguments "${JEX_TOKEN_ID}" \
        --pem=${USER} --gas-limit=40000000 --outfile="deploy-devnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send || return

    ADDRESS=$(erdpy data parse --file="deploy-devnet.interaction.json" --expression="data['emitted_tx']['address']")

    erdpy data store --key=address-devnet --value=${ADDRESS}

    echo ""
    echo "Smart contract address: ${ADDRESS}"
}

upgrade() {
    echo 'You are about to upgrade current SC on devnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract upgrade --project=${PROJECT} --metadata-payable \
        --arguments "${JEX_TOKEN_ID}" \
        --pem=${USER} --gas-limit=40000000 --outfile="deploy-devnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send ${ADDRESS} || return

    echo ""
    echo "Smart contract upgraded: ${ADDRESS}"
}

CMD=$1
shift

$CMD $*
