#!/bin/bash
# Verifier entry script for task-java-race-condition (Python service)
set -uo pipefail

mkdir -p /logs/verifier
echo "0.0" > /logs/verifier/reward.txt

cd /app
pytest /tests/test_outputs.py > /logs/verifier/test_output.log 2>&1

if [ $? -eq 0 ]; then
    echo "1.0" > /logs/verifier/reward.txt
else
    echo "0.0" > /logs/verifier/reward.txt
fi
