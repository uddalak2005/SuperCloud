#!/bin/bash

set -e

#To be removed later
make -C agent setup-test-logs &
sleep 1
make -C agent write-test-logs &


make -C agent run-all &

sleep 1

python ./orchestrator/main.py