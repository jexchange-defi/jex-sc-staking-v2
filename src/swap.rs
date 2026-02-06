use multiversx_sc::hex_literal::hex;

multiversx_sc::imports!();

#[multiversx_sc::module]
pub trait SwapModule {
    fn swap_usdc_to_jex(&self) {
        let usdc_identifier = TokenIdentifier::from_esdt_bytes(b"USDC-c76f1f");

        let usdc_balance = self.blockchain().get_sc_balance(
            &EgldOrEsdtTokenIdentifier::esdt(usdc_identifier.clone()),
            0u64,
        );

        if usdc_balance > 1 {
            // erd1qqqqqqqqqqqqqpgqxwl3zmftzrvkpphx4wx2z7mgl09ncgcl6avsnp4z0w
            let swap_sc_address = ManagedAddress::from(hex!(
                "0000000000000000050033bf116d2b10d96086e6ab8ca17b68fbcb3c231fd759"
            ));

            let payment = EsdtTokenPayment::new(usdc_identifier, 0u64, usdc_balance);

            self.jexchange_lps_sc_proxy(swap_sc_address)
                .swap_tokens_fixed_input(BigUint::from(2u64))
                .with_esdt_transfer(payment)
                .async_call_and_exit();
        }
    }

    #[proxy]
    fn jexchange_lps_sc_proxy(
        &self,
        sc_address: ManagedAddress,
    ) -> crate::jexchange_lps_sc_proxy::Proxy<Self::Api>;
}
