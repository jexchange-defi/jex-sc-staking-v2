use multiversx_sc_scenario::*;

fn world() -> ScenarioWorld {
    ScenarioWorld::vm_go()
}

#[test]
fn configure_go() {
    world().run("scenarios/configure.scen.json");
}

#[test]
fn configure_not_owner_go() {
    world().run("scenarios/configure_not_owner.scen.json");
}

#[test]
fn configure_token_go() {
    world().run("scenarios/configure_token.scen.json");
}

#[test]
fn configure_token_not_owner_go() {
    world().run("scenarios/configure_token_not_owner.scen.json");
}

#[test]
fn configure_token_replace_go() {
    world().run("scenarios/configure_token_replace.scen.json");
}

#[test]
fn distribute_rewards_nominal_step_1_go() {
    world().run("scenarios/distribute_rewards_nominal_step_1.scen.json");
}

#[test]
fn distribute_rewards_nominal_step_2_go() {
    world().run("scenarios/distribute_rewards_nominal_step_2.scen.json");
}

#[test]
fn distribute_rewards_not_owner_go() {
    world().run("scenarios/distribute_rewards_not_owner.scen.json");
}

#[test]
fn distribute_rewards_wrong_period_go() {
    world().run("scenarios/distribute_rewards_wrong_period.scen.json");
}

#[test]
fn fund_rewards_wrong_period_go() {
    world().run("scenarios/fund_rewards_wrong_period.scen.json");
}

#[test]
fn get_state_distribution_go() {
    world().run("scenarios/get_state_distribution.scen.json");
}

#[test]
fn get_state_distribution_done_go() {
    world().run("scenarios/get_state_distribution_done.scen.json");
}

#[test]
fn get_state_snapshot_go() {
    world().run("scenarios/get_state_snapshot.scen.json");
}

#[test]
fn init_go() {
    world().run("scenarios/init.scen.json");
}

#[test]
fn init_round_distrib_incomplete_go() {
    world().run("scenarios/init_round_distrib_incomplete.scen.json");
}

#[test]
fn init_round_nominal_go() {
    world().run("scenarios/init_round_nominal.scen.json");
}

#[test]
fn init_round_not_owner_go() {
    world().run("scenarios/init_round_not_owner.scen.json");
}

#[test]
fn prepare_rewards_nominal_go() {
    world().run("scenarios/prepare_rewards_nominal.scen.json");
}

#[test]
fn prepare_rewards_not_owner_go() {
    world().run("scenarios/prepare_rewards_not_owner.scen.json");
}

#[test]
fn prepare_rewards_wrong_period_go() {
    world().run("scenarios/prepare_rewards_wrong_period.scen.json");
}

#[test]
fn remove_rewards_nominal_go() {
    world().run("scenarios/remove_rewards_nominal.scen.json");
}

#[test]
fn remove_rewards_not_owner_go() {
    world().run("scenarios/remove_rewards_not_owner.scen.json");
}

#[test]
fn remove_rewards_wrong_period_go() {
    world().run("scenarios/remove_rewards_wrong_period.scen.json");
}

#[test]
fn snapshot_holders_nominal_go() {
    world().run("scenarios/snapshot_holders_nominal.scen.json");
}

#[test]
fn snapshot_holders_not_owner_go() {
    world().run("scenarios/snapshot_holders_not_owner.scen.json");
}

#[test]
fn snapshot_holders_wrong_period_go() {
    world().run("scenarios/snapshot_holders_wrong_period.scen.json");
}
