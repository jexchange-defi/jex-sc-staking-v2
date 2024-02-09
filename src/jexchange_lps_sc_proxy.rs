multiversx_sc::imports!();
multiversx_sc::derive_imports!();

#[multiversx_sc::proxy]
pub trait JexchangeLpsScProxy {
    #[payable("*")]
    #[endpoint(swapTokensFixedInput)]
    fn swap_tokens_fixed_input(&self, min_amount_out: BigUint);
}
