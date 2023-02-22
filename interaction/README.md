# Interaction

This file describes how to operate the smart contract and the whole staking process.

## Prerequisites

* Python 3.10+ installed
* Python dependencies installed (`pip install -r requirements.txt`)
* keyfile: `../wallets/deployer.json`


## SC deployment

Use the followinf command to deploy the smart contract:

```shell
./xxxnet.snippets.sh deploy
```

Note that the smart contract address will be saved in `erdpy.data-storage.json`

or upgrade is it's already deployed

```shell
./xxxnet.snippets.sh upgrade
```


## SC configuration

The accepted tokens must be configured in ordered to be distributed as rewards.

```shell
./xxxnet.snippets.sh configureToken
```

You will be prompted the following data:
```
Token identifier: <-- token identifier (eg: JEX-9040ca)
Token nonce (decimal): <-- token nonce (0 for ESDT)
Threshold: <-- threshold for this token+nonce (rewards will not be enabled if the balance is below this threshold) (eg: 10000000000000000000000 which is 10,000 * 10^18. Token has 18 decimals)
```

## SC lifecycle and operations

### A. deploy

Staking round #1 is initialized. Snapshots are enabled.

### B. accumulation period

During the accumulation period, rewards can be sent to the SC.

Snapshots must be taken during this period.

#### Snapshots

Use `snapshot.py` with `export_holders` action to create a list of holders and balances to snapshot.

Example:

```shell
# Export holders of at least 10K JEX on mainnet

python snapshot.py --api_url https://api.multiversx.com \
    --gateway_utl https://gateway.multiversx.com \
    --token_identifier JEX-9040ca \
    --min_amount 10000
```

The list of holders with the minimum required amount of tokens is exported in `.holders.csv` file.

Use `snapshot.py` with `register_holders` action to import the snapshot if the smart contract.

Example:

```shell
# Import the previously generated snapshot in the SC on mainnet

python snapshot.py --gateway_url https://gateway.multiversx.com \
    --keyfile ../wallets/operator.json \
    --sc_address erd1qqqqqqqqqqqqqxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
    register_holders
```

Run `python snapshot.py --help` for more information.

A report is generated in `.report.txt` with a status for every address of the snapshot.

**You MUST check that all registered address has the successful state**

Note that snapshot registration is disabled during reward distribution period.

### C. rewards distribution period

During this period, rewards are settled, snapshots are disabled.

#### Rewards preparation

To trigger distribution period, rewards must be setlled.

To do so run the following script:

```shell
./xxxnet.snippets.sh prepareRewards
```

You can verify the prepared rewards with:
```shell
./xxxnet.snippets.sh getRewardsForRound

Round: <-- the current round number
```

#### Rewards distribution

Once rewards are prepared, distribution can start.

The distribute is made by batches of N addresses. The addresses are put in a queue, distribution is made until this quere is empty.

Use `distribute.py` script to launch distribution.

Example:

```shell
# Example to distribute rewards to 100 holders

python distribute.py --gateway_url https://gateway.multiversx.com \
    --keyfile ../wallets/operator.json \
    --sc_address erd1qqqqqqqqqqqqqxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
    100
```

Run `python distribute.py --help` for more information.

### D. Initialize next round

Once the reward distribution is complete, it's time to initialize the next round.

Use the following command to initialize the next round:

```shell
./xxxnet.snippets.sh initRound
```

Note that this will fail if the rewards distribution is not complete.

Then accumulation begins (go to [B](#b-accumulation-period))


## SC monitoring

A bunch of views are available in the SC to expose some data.

Look at the dedicated [section](../README.md#views) in the main README.
