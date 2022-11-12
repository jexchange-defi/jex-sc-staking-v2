#![no_std]

mod snapshots;
mod tokens;

elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[elrond_wasm::derive::contract]
pub trait ScStaking: snapshots::SnapshotsModule + tokens::TokensModule {
    #[only_owner]
    #[init]
    fn init(&self) {
        self.current_round().set_if_empty(1);
    }

    #[only_owner]
    #[endpoint(initRound)]
    fn init_round(&self) {
        self.require_distribution_complete();

        self.current_round().update(|x| *x += 1);
    }

    #[view(getCurrentRound)]
    #[storage_mapper("current_round")]
    fn current_round(&self) -> SingleValueMapper<u32>;
}
