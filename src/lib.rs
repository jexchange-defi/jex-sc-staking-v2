#![no_std]

elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[elrond_wasm::derive::contract]
pub trait ScStaking {
    #[only_owner]
    #[init]
    fn init(&self) {}
}
