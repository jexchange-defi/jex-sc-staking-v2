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
* min_amount: BigUint - minimum threshold to consider the token as rewards during rewards calculation.

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

Can be called multiple times as long as the claim period is not started.

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

## getRewardsForRound

Return the rewards for the given round.

Parameters:
* round: integer - round number.


# Storage

## current_round

u32

## total_snapshot_balance

BigUint

## tokens

VecMapper of TokenAndThreshold

TokenAndThreshold {
    token: TokenIdentifer;
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
    balance: BigUint;
}
