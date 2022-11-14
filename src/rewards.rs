elrond_wasm::imports!();
elrond_wasm::derive_imports!();

use elrond_wasm::types::heap::Vec;

#[derive(TopEncode, TopDecode, TypeAbi)]
pub struct TokenAndBalance<M: ManagedTypeApi> {
    token: TokenIdentifier<M>,
    nonce: u64,
    balance: BigUint<M>,
}

static DISTRIBUTION_ALREADY_COMPLETE: &[u8] = b"Distribution already complete";
static REWARDS_ALREADY_PREPARED: &[u8] = b"Rewards already prepared";
static REWARDS_NOT_PREPARED: &[u8] = b"Rewards are not prepared";

#[elrond_wasm::module]
pub trait RewardsModule: crate::tokens::TokensModule + crate::snapshots::SnapshotsModule {
    fn prepare_rewards_internal(&self, round: u32) {
        let mut rewards = self.rewards_for_round(round);
        require!(rewards.is_empty(), REWARDS_ALREADY_PREPARED);

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
        let rewards = self.rewards_for_round(round);
        require!(!rewards.is_empty(), REWARDS_NOT_PREPARED);

        require!(
            !self.all_addresses().is_empty(),
            DISTRIBUTION_ALREADY_COMPLETE
        );

        let addresses: Vec<ManagedAddress> = self.all_addresses().iter().take(limit).collect();
        for address in addresses {
            self.distribute_rewards_for_address(round, &address);
            self.snapshot_address_balance(&address).clear();
            self.all_addresses().swap_remove(&address);
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

    #[view(getRewardsForRound)]
    #[storage_mapper("rewards_for_round")]
    fn rewards_for_round(&self, round: u32) -> VecMapper<TokenAndBalance<Self::Api>>;

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
