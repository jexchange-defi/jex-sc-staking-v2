elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[derive(TopEncode, TopDecode, TypeAbi)]
pub struct TokenAndBalance<M: ManagedTypeApi> {
    token: TokenIdentifier<M>,
    nonce: u64,
    balance: BigUint<M>,
}

static REWARDS_ALREADY_PREPARED: &[u8] = b"Rewards already prepared";

#[elrond_wasm::module]
pub trait RewardsModule: crate::tokens::TokensModule {
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

    #[view(getRewardsForRound)]
    #[storage_mapper("rewards_for_round")]
    fn rewards_for_round(&self, round: u32) -> VecMapper<TokenAndBalance<Self::Api>>;
}
