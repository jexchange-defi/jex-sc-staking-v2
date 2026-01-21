multiversx_sc::imports!();
multiversx_sc::derive_imports!();

#[type_abi]
#[derive(TopEncode)]
pub struct SharesOfAddress<M: ManagedTypeApi> {
    address_balance: BigUint<M>,
    total_balance: BigUint<M>,
}

#[multiversx_sc::module]
pub trait SnapshotsModule {
    // owner endpoints

    fn snapshot_internal(
        &self,
        addresses_and_balances: MultiValueEncoded<MultiValue2<ManagedAddress, BigUint>>,
    ) {
        let mut total_diff = BigUint::zero();

        for address_and_balance in addresses_and_balances {
            let (address, balance) = address_and_balance.clone().into_tuple();

            self.snapshot_address_balance(&address)
                .update(|x| *x += &balance);

            total_diff += &balance;

            self.all_addresses().insert(address);
        }

        self.snapshot_total_balance().update(|x| *x += total_diff);
    }

    // functions

    fn reset_snapshots(&self) {
        self.snapshot_total_balance().set(&BigUint::zero());
    }

    // storage & views

    #[view(getAllAddresses)]
    fn get_all_addresses(&self, from: usize, size: usize) -> MultiValueEncoded<ManagedAddress> {
        self.all_addresses().iter().skip(from).take(size).collect()
    }

    #[storage_mapper("all_addresses")]
    fn all_addresses(&self) -> UnorderedSetMapper<ManagedAddress>;

    #[view(getNbAddresses)]
    fn nb_addresses(&self) -> usize {
        self.all_addresses().len()
    }

    #[storage_mapper("snap_bal")]
    fn snapshot_address_balance(&self, address: &ManagedAddress) -> SingleValueMapper<BigUint>;

    #[view(getSnapshotTotalBalance)]
    #[storage_mapper("snapshot_total_balance")]
    fn snapshot_total_balance(&self) -> SingleValueMapper<BigUint>;

    #[view(getSharesOfAddress)]
    fn get_shares_of_address(&self, address: ManagedAddress) -> SharesOfAddress<Self::Api> {
        let balance = self.snapshot_address_balance(&address).get();

        SharesOfAddress::<Self::Api> {
            address_balance: balance,
            total_balance: self.snapshot_total_balance().get(),
        }
    }
}
