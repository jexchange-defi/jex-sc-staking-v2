PROJECT=..
KEYFILE="../wallets/deployer.json"
PROXY=https://devnet-gateway.elrond.com
SC_ADDRESS=$(erdpy data load --key=address-devnet)
CHAIN=D
JEX_TOKEN_ID="0x$(echo -n "XJEX-899465" | xxd -ps)"

echo "SC address: ${SC_ADDRESS}"

deploy() {
    echo 'You are about to deploy SC on devnet (Ctrl-C to abort)'
    read answer

    erdpy --verbose contract deploy --project=${PROJECT} --metadata-payable \
        --keyfile=${KEYFILE} --gas-limit=50000000 --outfile="deploy-devnet.interaction.json" \
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
        --keyfile=${KEYFILE} --gas-limit=50000000 --outfile="deploy-devnet.interaction.json" \
        --proxy=${PROXY} --chain=${CHAIN} --recall-nonce --send ${SC_ADDRESS} || return

    echo ""
    echo "Smart contract upgraded: ${SC_ADDRESS}"
}

configure() {
    # erd1hmfwpvsqn8ktzw3dqd0ltpcyfyasgv8mr9w0qecnmpexyp280y8q47ca9d
    read -p "Treasury address: " TREASURY_ADDRESS
    TREASURY_ADDRESS="0x$(erdpy wallet bech32 --decode ${TREASURY_ADDRESS})"
    # erd1ssruj9rjy529ajqpqfmtkyq422fh2m4zhkp4pmfng3aad2h7ua2quydm30
    read -p "Team A address: " TEAM_A_ADDRESS
    TEAM_A_ADDRESS="0x$(erdpy wallet bech32 --decode ${TEAM_A_ADDRESS})"
    # erd19g9fa6tkqlvn5x2nuqvwlcmz943vpt5q3a92fkdsngu0zz62qpasyelgws
    read -p "Team J address: " TEAM_J_ADDRESS
    TEAM_J_ADDRESS="0x$(erdpy wallet bech32 --decode ${TEAM_J_ADDRESS})"
    # erd155xlkeyqatck0qay99qk7qwerxc0efergug9k588uql4efm7yhwqqwkcsq
    read -p "Team P address: " TEAM_P_ADDRESS
    TEAM_P_ADDRESS="0x$(erdpy wallet bech32 --decode ${TEAM_P_ADDRESS})"
    erdpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=4000000 \
        --function="configure" \
        --arguments ${TREASURY_ADDRESS} ${TEAM_A_ADDRESS} ${TEAM_J_ADDRESS} ${TEAM_P_ADDRESS} \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

initRound() {
    erdpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=3000000 \
        --function="initRound" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

configureToken() {
    read -p "Token identifier: " TOKEN_IDENTIFIER
    TOKEN_IDENTIFIER="0x$(echo -n "${TOKEN_IDENTIFIER}" | xxd -ps)"

    read -p "Token nonce (decimal): " TOKEN_NONCE
    read -p "Threshold: " THRESHOLD

    erdpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=4000000 \
        --function="configureToken" \
        --arguments "${TOKEN_IDENTIFIER}" "${TOKEN_NONCE}" "${THRESHOLD}" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

snapshot() {
    read -p "Address: " ADDRESS
    ADDRESS="0x$(erdpy wallet bech32 --decode ${ADDRESS})"
    read -p "Balance: " BALANCE

    erdpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=5000000 \
        --function="snapshot" \
        --arguments "${ADDRESS}" "${BALANCE}" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

prepareRewards() {
    erdpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=5000000 \
        --function="prepareRewards" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

distribute() {
    read -p "Limit (decimal): " LIMIT
    GAS_LIMIT=$((5000000 * LIMIT))

    erdpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=${GAS_LIMIT} \
        --function="distribute" \
        --arguments "${LIMIT}" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

getState() {
    erdpy --verbose contract query ${SC_ADDRESS} --function "getState" --proxy=${PROXY}
}

getTokenThresholds() {
    erdpy --verbose contract query ${SC_ADDRESS} --function "getTokenThresholds" --proxy=${PROXY}
}

getRewardsForRound() {
    read -p "Round: " ROUND
    erdpy --verbose contract query ${SC_ADDRESS} \
        --function "getRewardsForRound" --arguments "${ROUND}" \
        --proxy=${PROXY}
}

getSnapshotTotalBalance() {
    erdpy --verbose contract query ${SC_ADDRESS} --function "getSnapshotTotalBalance" --proxy=${PROXY}
}

getAllAddresses() {
    erdpy --verbose contract query ${SC_ADDRESS} --function "getAllAddresses" --proxy=${PROXY}
}

getNbAddresses() {
    erdpy --verbose contract query ${SC_ADDRESS} --function "getNbAddresses" --proxy=${PROXY}
}

CMD=$1
shift

$CMD $*
