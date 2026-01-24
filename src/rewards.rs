multiversx_sc::imports!();
multiversx_sc::derive_imports!();

#[type_abi]
#[derive(Clone, ManagedVecItem, NestedEncode, TopEncode, TopDecode)]
pub struct TokenAndBalance<M: ManagedTypeApi> {
    token: TokenIdentifier<M>,
    nonce: u64,
    balance: BigUint<M>,
}

static REWARD_TREASURY_PERCENT: u32 = 30;
static REWARD_TEAM_A_PERCENT: u32 = 10;
static REWARD_TEAM_J_PERCENT: u32 = 5;
static REWARD_TEAM_P_PERCENT: u32 = 5;

#[multiversx_sc::module]
pub trait RewardsModule: crate::tokens::TokensModule + crate::snapshots::SnapshotsModule {
    // owner endpoints

    fn fund_rewards_internal(&self) {
        let jex_id = TokenIdentifier::from_esdt_bytes(b"JEX-9040ca");

        let payments = &self.call_value().all_esdt_transfers();
        for payment in payments.iter() {
            let treasury_amount = payment.amount.clone() * REWARD_TREASURY_PERCENT / 100u64;
            let receiver = if payment.token_identifier == jex_id {
                self.burn_wallet().get()
            } else {
                self.treasury_address().get()
            };

            self.tx()
                .to(receiver)
                .with_esdt_transfer(EsdtTokenPayment::new(
                    payment.token_identifier.clone(),
                    payment.token_nonce,
                    treasury_amount,
                ))
                .transfer();

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
        let mut rewards = self.rewards_for_round(round);

        let calculated_rewards = &mut ManagedVec::<Self::Api, TokenAndBalance<Self::Api>>::new();
        self.calculate_current_rewards(calculated_rewards);

        for reward in calculated_rewards.iter() {
            rewards.push(&reward);
        }
    }

    fn distribute_rewards_internal(&self, round: u32, limit: usize) -> bool {
        let mut distribution_complete = false;

        for _ in 0..limit {
            let address = self.all_addresses().get_by_index(1);
            self.distribute_rewards_for_address(round, &address);
            self.snapshot_address_balance(&address).clear();
            self.all_addresses().swap_remove(&address);

            if self.all_addresses().is_empty() {
                distribution_complete = true;
                break;
            }
        }

        distribution_complete
    }

    fn remove_rewards_internal(
        &self,
        token_identifier: &TokenIdentifier,
        token_nonce: u64,
        receiver: &ManagedAddress,
    ) {
        let balance = self.blockchain().get_sc_balance(
            &EgldOrEsdtTokenIdentifier::esdt(token_identifier.clone()),
            token_nonce,
        );

        self.send()
            .direct_esdt(receiver, token_identifier, token_nonce, &balance);
    }

    // functions

    fn calculate_current_rewards(
        &self,
        rewards: &mut ManagedVec<Self::Api, TokenAndBalance<Self::Api>>,
    ) {
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
                rewards.push(reward.clone());
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

    // storage & views

    #[view(getBurnWallet)]
    #[storage_mapper("burn_wallet")]
    fn burn_wallet(&self) -> SingleValueMapper<ManagedAddress>;

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

    #[event("rewards")]
    fn rewards_distribution_event(
        &self,
        #[indexed] round: u32,
        #[indexed] receiver: &ManagedAddress,
        #[indexed] token: &TokenIdentifier,
        #[indexed] nonce: u64,
        amount: &BigUint,
    );
}
