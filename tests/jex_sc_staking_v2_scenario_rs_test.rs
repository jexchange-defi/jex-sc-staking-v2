use multiversx_sc_scenario::*;

fn world() -> ScenarioWorld {
    let mut blockchain = ScenarioWorld::new();
    // blockchain.set_current_dir_from_workspace("relative path to your workspace, if applicable");

    blockchain.register_contract(
        "mxsc:output/jex-sc-staking-v2.mxsc.json",
        jex_sc_staking_v2::ContractBuilder,
    );
    blockchain
}

#[test]
fn configure_rs() {
    world().run("scenarios/configure.scen.json");
}

#[test]
fn configure_not_owner_rs() {
    world().run("scenarios/configure_not_owner.scen.json");
}

#[test]
fn configure_token_rs() {
    world().run("scenarios/configure_token.scen.json");
}

#[test]
fn configure_token_not_owner_rs() {
    world().run("scenarios/configure_token_not_owner.scen.json");
}

#[test]
fn configure_token_replace_rs() {
    world().run("scenarios/configure_token_replace.scen.json");
}

#[test]
fn distribute_rewards_nominal_step_1_rs() {
    world().run("scenarios/distribute_rewards_nominal_step_1.scen.json");
}

#[test]
fn distribute_rewards_nominal_step_2_rs() {
    world().run("scenarios/distribute_rewards_nominal_step_2.scen.json");
}

#[test]
fn distribute_rewards_not_owner_rs() {
    world().run("scenarios/distribute_rewards_not_owner.scen.json");
}

#[test]
fn distribute_rewards_wrong_period_rs() {
    world().run("scenarios/distribute_rewards_wrong_period.scen.json");
}

#[test]
fn fund_rewards_wrong_period_rs() {
    world().run("scenarios/fund_rewards_wrong_period.scen.json");
}

#[test]
fn get_state_distribution_rs() {
    world().run("scenarios/get_state_distribution.scen.json");
}

#[test]
fn get_state_distribution_done_rs() {
    world().run("scenarios/get_state_distribution_done.scen.json");
}

#[test]
fn get_state_snapshot_rs() {
    world().run("scenarios/get_state_snapshot.scen.json");
}

#[test]
fn init_rs() {
    world().run("scenarios/init.scen.json");
}

#[test]
fn init_round_distrib_incomplete_rs() {
    world().run("scenarios/init_round_distrib_incomplete.scen.json");
}

#[test]
fn init_round_nominal_rs() {
    world().run("scenarios/init_round_nominal.scen.json");
}

#[test]
fn init_round_not_owner_rs() {
    world().run("scenarios/init_round_not_owner.scen.json");
}

#[test]
fn prepare_rewards_nominal_rs() {
    world().run("scenarios/prepare_rewards_nominal.scen.json");
}

#[test]
fn prepare_rewards_not_owner_rs() {
    world().run("scenarios/prepare_rewards_not_owner.scen.json");
}

#[test]
fn prepare_rewards_wrong_period_rs() {
    world().run("scenarios/prepare_rewards_wrong_period.scen.json");
}

#[test]
fn remove_rewards_nominal_rs() {
    world().run("scenarios/remove_rewards_nominal.scen.json");
}

#[test]
fn remove_rewards_not_owner_rs() {
    world().run("scenarios/remove_rewards_not_owner.scen.json");
}

#[test]
fn remove_rewards_wrong_period_rs() {
    world().run("scenarios/remove_rewards_wrong_period.scen.json");
}

#[test]
fn snapshot_holders_nominal_rs() {
    world().run("scenarios/snapshot_holders_nominal.scen.json");
}

#[test]
fn snapshot_holders_not_owner_rs() {
    world().run("scenarios/snapshot_holders_not_owner.scen.json");
}

#[test]
fn snapshot_holders_wrong_period_rs() {
    world().run("scenarios/snapshot_holders_wrong_period.scen.json");
}
