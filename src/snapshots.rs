elrond_wasm::imports!();
elrond_wasm::derive_imports!();

static DISTRIB_INCOMPLETE_ERR: &[u8] = b"Distribution is incomplete";
static SNAPSHOT_NOT_ENABLED_ERR: &[u8] = b"Snapshots are disabled";

#[elrond_wasm::module]
pub trait SnapshotsModule {
    #[only_owner]
    #[endpoint]
    fn snapshot(
        &self,
        addresses_and_balances: MultiValueEncoded<MultiValue2<ManagedAddress, BigUint>>,
    ) {
        require!(self.snapshots_enabled().get(), SNAPSHOT_NOT_ENABLED_ERR);

        for address_and_balance in addresses_and_balances {
            let (address, balance) = address_and_balance.clone().into_tuple();

            self.snapshot_address_balance(&address)
                .set_if_empty(&BigUint::zero());
            self.snapshot_address_balance(&address)
                .update(|x| *x += balance.clone());

            self.snapshot_total_balance().update(|x| *x += balance);

            self.all_addresses().insert(address);
        }
    }

    fn enable_snapshots(&self) {
        self.snapshots_enabled().set(&true);
    }

    fn disable_snapshots(&self) {
        self.snapshots_enabled().set(&false);
    }

    fn reset_snapshots(&self) {
        self.snapshot_total_balance().set(&BigUint::zero());
    }

    fn require_distribution_complete(&self) {
        require!(self.all_addresses().is_empty(), DISTRIB_INCOMPLETE_ERR);
    }

    #[view(getAllAddresses)]
    #[storage_mapper("all_addresses")]
    fn all_addresses(&self) -> UnorderedSetMapper<ManagedAddress>;

    #[storage_mapper("snapshot_address_balance")]
    fn snapshot_address_balance(&self, address: &ManagedAddress) -> SingleValueMapper<BigUint>;

    #[storage_mapper("snapshots_enabled")]
    fn snapshots_enabled(&self) -> SingleValueMapper<bool>;

    #[view(getSnapshotTotalBalance)]
    #[storage_mapper("snapshot_total_balance")]
    fn snapshot_total_balance(&self) -> SingleValueMapper<BigUint>;
}
