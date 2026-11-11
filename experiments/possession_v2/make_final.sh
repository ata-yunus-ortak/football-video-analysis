#!/bin/bash
set -e
cd /home/claude/sc
python3 -m possession.train --config possession-v2-config.json --dfl-prepared /mnt/user-data/uploads/sportec-development-20261107/prepared-v1 --out models/possession-v2.npz > /home/claude/work/final_train.log 2>&1
sha256sum models/possession-v2.npz >> /home/claude/work/final_train.log
cd /home/claude/work
python3 test_reserved.py /home/claude/sc/models/possession-v2.npz /home/claude/work/reserved_test_v2.json > reserved_test.log 2>&1
echo ALLDONE >> reserved_test.log
