# Introduction

Fees collected are redistributed to JEX holders, treasury and team members.

jex-sc-staking-v2 is a smart contract used to manage the distribution of these fees.

Staking is soft, users just need to hold their tokens to earn the rewards.

Smart Contract addresses do not take part of this soft staking.

Workflow:

* initialize staking round
* accumulation period with unpredictible snapshots
* rewards calculation
* distribution
* (start over)

Here is a sequence that sums up the snapshot/reward process:

![](doc/jex-staking-v2-sequence.png)

Regular (manual) snapshots of holders are taken. Balances of holders are accumulating at each snapshot.

In order to prevent speculation, snapshots are taken randomly.

Upon distribution, each holder receives its share of the rewards based on its accumulated balance out of the sum of all the balances.

See [interaction](./interaction/README.md) for more information about how to operate the smart contract.

# Init

## init

Parameters:

* ...


# Owner endpoints

## configure

Callable by owner only.

Parameters:

* treasury_address: ManagedAddress - will earn 30% of fees
* team_a_address: ManagedAddress - will earn 10% of fees
* team_j_address: ManagedAddress - will earn 5% of fees
* team_p_address: ManagedAddress - will earn 5% of fees

## configureToken

Allow token as rewards.

Parameters:
* token_identifier: token identifier
* nonce: token nonce
* threshold: BigUint - minimum amount to consider the token as rewards during rewards calculation.

## initRound

Initialize a new round.

Fail if snapshots are present.

## snapshot

Add a list of addresses + their snapshot balance.

Fail if in not in accumulation period.

Parameters:

* List of Address + balance

## prepareRewards

Iterate over all configured tokens and freeze the current SC balance if greater than threshold.

See `tokens` storage.

Can be called only once per round (be careful then).

Rewards can be seen using `getRewardsForRound` view.

## distribute

Distribute rewards to all snapshot addresses.

Iterate over `all_addresses` storage (with `limit` parameter):
* calculate shares
* distribute rewards
* set snapshot balance to zero
* remove address from `all_addresses`.

Parameters:

* limit: u32 - max addresses to process


# Public endpoints

None


# Views

## getCurrentRound

Return the current staking round (integer)

## getState

Return the current state of staking (Accumulation or Distribution)

## getCurrentRoundRewards

Return the rewards of the current round.

If rewards are not prepared yet, current balances (over the [configured thresholds](#configuretoken)) are returned.

## getRewardsForRound

Return the rewards for the given round.

Parameters:
* round: integer - round number.

## getNbAddresses

Return the current number of addresses.

## getSnapshotTotalBalance

Return the total of snapshot balances

## getSharesOfAddress

Return the shares of an address.

Parameters:
* address: ManagedAddress.

Returns:

* address_balance: BigUint
* total_balance: BigUint

# Storage

## current_round

u32

## total_snapshot_balance

BigUint

## tokens

VecMapper of TokenAndThreshold

TokenAndThreshold {
    token: TokenIdentifer;
    nonce: u64;
    threshold: BigUint;
}

## snapshot_address_balance

SingleValueMapper: ManagedAddress -> BigUint

## all_addresses

UnorderedSet of ManagedAddress

## rewards_for_round

SingleValueMapper: int -> ManagedVec<TokenAndBalance>

TokenAndBalance {
    token: TokenIdentifer;
    nonce: u64;
    balance: BigUint;
}
