use multiversx_sc::hex_literal::hex;

multiversx_sc::imports!();

#[multiversx_sc::module]
pub trait SwapModule {
    fn swap_wegld_to_jex(&self) {
        let wegld_identifier = TokenIdentifier::from_esdt_bytes(b"WEGLD-bd4d79");

        let wegld_balance = self.blockchain().get_sc_balance(
            &EgldOrEsdtTokenIdentifier::esdt(wegld_identifier.clone()),
            0u64,
        );

        if wegld_balance > 1 {
            // erd1qqqqqqqqqqqqqpgq7u4y0qle773mcelvnkapjv36pn2whzy36avs2qccja
            let swap_sc_address = ManagedAddress::from(hex!(
                "00000000000000000500f72a4783f9f7a3bc67ec9dba19323a0cd4eb8891d759"
            ));

            let payment = EsdtTokenPayment::new(wegld_identifier, 0u64, wegld_balance);

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
