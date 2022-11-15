elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[derive(TopEncode, TopDecode, TypeAbi)]
pub struct TokenAndBalance<M: ManagedTypeApi> {
    token: TokenIdentifier<M>,
    nonce: u64,
    balance: BigUint<M>,
}

static DISTRIBUTION_ALREADY_COMPLETE: &[u8] = b"Distribution already complete";
static REWARDS_ALREADY_PREPARED: &[u8] = b"Rewards already prepared";
static REWARDS_NOT_PREPARED: &[u8] = b"Rewards are not prepared";

static REWARD_TREASURY_PERCENT: u32 = 30;
static REWARD_TEAM_A_PERCENT: u32 = 10;
static REWARD_TEAM_J_PERCENT: u32 = 5;
static REWARD_TEAM_P_PERCENT: u32 = 5;

#[elrond_wasm::module]
pub trait RewardsModule: crate::tokens::TokensModule + crate::snapshots::SnapshotsModule {
    fn fund_rewards_internal(&self, round: u32) {
        self.require_rewards_not_prepared(round);

        let payments = &self.call_value().all_esdt_transfers();
        for payment in payments {
            self.send().direct_esdt(
                &self.treasury_address().get(),
                &payment.token_identifier,
                payment.token_nonce,
                &(payment.amount.clone() * REWARD_TREASURY_PERCENT / 100u64),
            );
            self.send().direct_esdt(
                &self.team_a_address().get(),
                &payment.token_identifier,
                payment.token_nonce,
                &(payment.amount.clone() * REWARD_TEAM_A_PERCENT / 100u64),
            );
            self.send().direct_esdt(
                &self.team_j_address().get(),
                &payment.token_identifier,
                payment.token_nonce,
                &(payment.amount.clone() * REWARD_TEAM_J_PERCENT / 100u64),
            );
            self.send().direct_esdt(
                &self.team_p_address().get(),
                &payment.token_identifier,
                payment.token_nonce,
                &(payment.amount.clone() * REWARD_TEAM_P_PERCENT / 100u64),
            );
        }
    }

    fn prepare_rewards_internal(&self, round: u32) {
        self.require_rewards_not_prepared(round);

        let mut rewards = self.rewards_for_round(round);
        for token_and_threshold in self.token_thresholds().iter() {
            let sc_balance = self.blockchain().get_sc_balance(
                &EgldOrEsdtTokenIdentifier::esdt(token_and_threshold.token.clone()),
                token_and_threshold.nonce,
            );

            if sc_balance > token_and_threshold.threshold {
                let reward = TokenAndBalance::<Self::Api> {
                    token: token_and_threshold.token.clone(),
                    nonce: token_and_threshold.nonce,
                    balance: sc_balance,
                };
                rewards.push(&reward);
            }
        }
    }

    fn distribute_rewards_internal(&self, round: u32, limit: usize) {
        self.require_rewards_prepared(round);

        require!(
            !self.all_addresses().is_empty(),
            DISTRIBUTION_ALREADY_COMPLETE
        );

        for _ in 0..limit {
            let address = self.all_addresses().get_by_index(1);
            self.distribute_rewards_for_address(round, &address);
            self.snapshot_address_balance(&address).clear();
            self.all_addresses().swap_remove(&address);

            if self.all_addresses().is_empty() {
                break;
            }
        }
    }

    fn distribute_rewards_for_address(&self, round: u32, address: &ManagedAddress) {
        let address_balance = &self.snapshot_address_balance(address).get();
        let total_balance = &self.snapshot_total_balance().get();

        for reward in self.rewards_for_round(round).iter() {
            let amount_to_send = (&reward.balance * address_balance) / total_balance;

            self.send()
                .direct_esdt(&address, &reward.token, reward.nonce, &amount_to_send);

            self.rewards_distribution_event(
                round,
                address,
                &reward.token,
                reward.nonce,
                &amount_to_send,
            );
        }
    }

    fn require_rewards_prepared(&self, round: u32) {
        let rewards = self.rewards_for_round(round);
        require!(!rewards.is_empty(), REWARDS_NOT_PREPARED);
    }

    fn require_rewards_not_prepared(&self, round: u32) {
        let rewards = self.rewards_for_round(round);
        require!(rewards.is_empty(), REWARDS_ALREADY_PREPARED);
    }

    #[view(getRewardsForRound)]
    #[storage_mapper("rewards_for_round")]
    fn rewards_for_round(&self, round: u32) -> VecMapper<TokenAndBalance<Self::Api>>;

    #[storage_mapper("treasury_address")]
    fn treasury_address(&self) -> SingleValueMapper<ManagedAddress>;

    #[storage_mapper("team_a_address")]
    fn team_a_address(&self) -> SingleValueMapper<ManagedAddress>;

    #[storage_mapper("team_j_address")]
    fn team_j_address(&self) -> SingleValueMapper<ManagedAddress>;

    #[storage_mapper("team_p_address")]
    fn team_p_address(&self) -> SingleValueMapper<ManagedAddress>;

    #[event("rewards_distribution")]
    fn rewards_distribution_event(
        &self,
        #[indexed] round: u32,
        #[indexed] receiver: &ManagedAddress,
        #[indexed] token: &TokenIdentifier,
        #[indexed] nonce: u64,
        amount: &BigUint,
    );
}
