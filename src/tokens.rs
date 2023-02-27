multiversx_sc::imports!();
multiversx_sc::derive_imports!();

#[derive(TopEncode, TopDecode, TypeAbi)]
pub struct TokenAndThreshold<M: ManagedTypeApi> {
    pub token: TokenIdentifier<M>,
    pub nonce: u64,
    pub threshold: BigUint<M>,
}

#[multiversx_sc::module]
pub trait TokensModule {
    // owner endpoints

    fn configure_token_inner(
        &self,
        token_identifier: &TokenIdentifier,
        nonce: u64,
        threshold: &BigUint,
    ) {
        let mut found = false;
        for (idx, mut token_threshold) in self.token_thresholds().iter().enumerate() {
            if &token_threshold.token == token_identifier && token_threshold.nonce == nonce {
                token_threshold.threshold = threshold.clone();
                found = true;
                self.token_thresholds().set(idx + 1, &token_threshold);
                break;
            }
        }

        if !found {
            let token_threshold = TokenAndThreshold::<Self::Api> {
                token: token_identifier.clone(),
                nonce,
                threshold: threshold.clone(),
            };
            self.token_thresholds().push(&token_threshold);
        }
    }

    // storage & views

    #[view(getTokenThresholds)]
    #[storage_mapper("token_thresholds")]
    fn token_thresholds(&self) -> VecMapper<TokenAndThreshold<Self::Api>>;
}
