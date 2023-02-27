##
# Info
##

echo "Proxy: ${PROXY}"
echo "SC address: ${SC_ADDRESS:-Not deployed}"

##
# Transactions
##

configure() {
    # erd1hmfwpvsqn8ktzw3dqd0ltpcyfyasgv8mr9w0qecnmpexyp280y8q47ca9d
    read -p "Treasury address: " TREASURY_ADDRESS
    TREASURY_ADDRESS="0x$(mxpy wallet bech32 --decode ${TREASURY_ADDRESS})"
    # erd1ssruj9rjy529ajqpqfmtkyq422fh2m4zhkp4pmfng3aad2h7ua2quydm30
    read -p "Team A address: " TEAM_A_ADDRESS
    TEAM_A_ADDRESS="0x$(mxpy wallet bech32 --decode ${TEAM_A_ADDRESS})"
    # erd19g9fa6tkqlvn5x2nuqvwlcmz943vpt5q3a92fkdsngu0zz62qpasyelgws
    read -p "Team J address: " TEAM_J_ADDRESS
    TEAM_J_ADDRESS="0x$(mxpy wallet bech32 --decode ${TEAM_J_ADDRESS})"
    # erd155xlkeyqatck0qay99qk7qwerxc0efergug9k588uql4efm7yhwqqwkcsq
    read -p "Team P address: " TEAM_P_ADDRESS
    TEAM_P_ADDRESS="0x$(mxpy wallet bech32 --decode ${TEAM_P_ADDRESS})"
    mxpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=6000000 \
        --function="configure" \
        --arguments ${TREASURY_ADDRESS} ${TEAM_A_ADDRESS} ${TEAM_J_ADDRESS} ${TEAM_P_ADDRESS} \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

configureToken() {
    read -p "Token identifier: " TOKEN_IDENTIFIER
    TOKEN_IDENTIFIER="0x$(echo -n "${TOKEN_IDENTIFIER}" | xxd -ps)"

    read -p "Token nonce (decimal): " TOKEN_NONCE
    read -p "Threshold: " THRESHOLD

    mxpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=5000000 \
        --function="configureToken" \
        --arguments "${TOKEN_IDENTIFIER}" "${TOKEN_NONCE}" "${THRESHOLD}" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

distributeRewards() {
    read -p "Limit (decimal): " LIMIT
    GAS_LIMIT=$((5000000 * LIMIT))

    mxpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=${GAS_LIMIT} \
        --function="distributeRewards" \
        --arguments "${LIMIT}" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

initRound() {
    mxpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=3000000 \
        --function="initRound" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

prepareRewards() {
    mxpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=10000000 \
        --function="prepareRewards" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

removeRewards() {
    read -p "Token identifier: " TOKEN_IDENTIFIER
    read -p "Token nonce (decimal): " TOKEN_NONCE
    read -p "Address: " RECEIVER

    TOKEN_IDENTIFIER="0x$(echo -n "${TOKEN_IDENTIFIER}" | xxd -ps)"
    RECEIVER="0x$(mxpy wallet bech32 --decode ${RECEIVER})"

    mxpy contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=5000000 \
        --function="removeRewards" \
        --arguments "${TOKEN_IDENTIFIER}" "${TOKEN_NONCE}" "${RECEIVER}" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

snapshot() {
    read -p "Address: " ADDRESS
    ADDRESS="0x$(mxpy wallet bech32 --decode ${ADDRESS})"
    read -p "Balance: " BALANCE

    mxpy --verbose contract call ${SC_ADDRESS} --recall-nonce --keyfile=${KEYFILE} --gas-limit=5000000 \
        --function="snapshot" \
        --arguments "${ADDRESS}" "${BALANCE}" \
        --proxy=${PROXY} --chain=${CHAIN} --send || return
}

##
# Views
##

getAllAddresses() {
    mxpy --verbose contract query ${SC_ADDRESS} --function "getAllAddresses" --proxy=${PROXY}
}

getCurrentRoundRewards() {
    mxpy --verbose contract query ${SC_ADDRESS} --function "getCurrentRoundRewards" --proxy=${PROXY}
}

getNbAddresses() {
    mxpy --verbose contract query ${SC_ADDRESS} --function "getNbAddresses" --proxy=${PROXY}
}

getRewardsForRound() {
    read -p "Round: " ROUND
    mxpy --verbose contract query ${SC_ADDRESS} \
        --function "getRewardsForRound" --arguments "${ROUND}" \
        --proxy=${PROXY}
}

getSharesOfAddress() {
    read -p "Address: " ADDRESS
    HEX_ADDRESS="0x$(mxpy wallet bech32 --decode ${ADDRESS})"
    mxpy --verbose contract query ${SC_ADDRESS} \
        --function "getSharesOfAddress" --arguments "${HEX_ADDRESS}" \
        --proxy=${PROXY}
}

getSnapshotTotalBalance() {
    mxpy --verbose contract query ${SC_ADDRESS} --function "getSnapshotTotalBalance" --proxy=${PROXY}
}

getState() {
    mxpy --verbose contract query ${SC_ADDRESS} --function "getState" --proxy=${PROXY}
}

getTokenThresholds() {
    mxpy --verbose contract query ${SC_ADDRESS} --function "getTokenThresholds" --proxy=${PROXY}
}
