#!/bin/bash

set -e

#To be removed later
make -C telemeter/agent setup-test-logs &
sleep 1
make -C telemeter/agent write-test-logs &


make -C telemeter/agent run-all &

sleep 1

python ./telemeter/orchestrator/main.py