#!/bin/sh

KEYFILE="../../wallets/deployer.json"

. .venv/bin/activate

python distribute.py --keyfile ${KEYFILE} $*
