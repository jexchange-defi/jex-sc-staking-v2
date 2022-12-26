elrond_wasm::imports!();
elrond_wasm::derive_imports!();

#[derive(TopEncode, TopDecode, TypeAbi)]
pub struct TokenAndThreshold<M: ManagedTypeApi> {
    pub token: TokenIdentifier<M>,
    pub nonce: u64,
    pub threshold: BigUint<M>,
}

#[elrond_wasm::module]
pub trait TokensModule {
    #[only_owner]
    #[endpoint(configureToken)]
    fn configure_token(&self, token_identifier: TokenIdentifier, nonce: u64, threshold: BigUint) {
        let mut found = false;
        for (idx, mut token_threshold) in self.token_thresholds().iter().enumerate() {
            if token_threshold.token == token_identifier && token_threshold.nonce == nonce {
                token_threshold.threshold = threshold.clone();
                found = true;
                self.token_thresholds().set(idx + 1, &token_threshold);
                break;
            }
        }

        if !found {
            let token_threshold = TokenAndThreshold::<Self::Api> {
                token: token_identifier,
                nonce,
                threshold,
            };
            self.token_thresholds().push(&token_threshold);
        }
    }

    #[view(getTokenThresholds)]
    #[storage_mapper("token_thresholds")]
    fn token_thresholds(&self) -> VecMapper<TokenAndThreshold<Self::Api>>;
}
