#![no_std]

mod rewards;
mod snapshots;
mod tokens;

elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[elrond_wasm::derive::contract]
pub trait ScStaking:
    rewards::RewardsModule + snapshots::SnapshotsModule + tokens::TokensModule
{
    #[only_owner]
    #[init]
    fn init(&self) {
        self.current_round().set_if_empty(1);
        self.enable_snapshots();
    }

    #[only_owner]
    #[endpoint(initRound)]
    fn init_round(&self) {
        self.require_distribution_complete();

        self.current_round().update(|x| *x += 1);

        self.reset_snapshots();
        self.enable_snapshots();
    }
    #[only_owner]
    #[endpoint(prepareRewards)]
    fn prepare_rewards(&self) {
        let current_round = self.current_round().get();
        self.prepare_rewards_internal(current_round);
    }

    #[view(getCurrentRound)]
    #[storage_mapper("current_round")]
    fn current_round(&self) -> SingleValueMapper<u32>;
}
