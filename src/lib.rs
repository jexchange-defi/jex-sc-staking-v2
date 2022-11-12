#![no_std]

mod tokens;

elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[elrond_wasm::derive::contract]
pub trait ScStaking: tokens::TokensModule {
    #[only_owner]
    #[init]
    fn init(&self) {}
}
