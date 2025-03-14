#!/bin/sh

. .venv/bin/activate

python snapshot.py $* export_holders
