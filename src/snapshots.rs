elrond_wasm::imports!();
elrond_wasm::derive_imports!();

static DISTRIB_INCOMPLETE_ERR: &[u8] = b"Distribution is not complete";

#[elrond_wasm::module]
pub trait SnapshotsModule {
    fn require_distribution_complete(&self) {
        require!(self.all_addresses().is_empty(), DISTRIB_INCOMPLETE_ERR);
    }

    #[view(getAllAddresses)]
    #[storage_mapper("all_addresses")]
    fn all_addresses(&self) -> UnorderedSetMapper<ManagedAddress<Self::Api>>;
}
