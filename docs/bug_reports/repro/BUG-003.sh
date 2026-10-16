#!/usr/bin/env bash
# BUG-003: the list drops the last order. Run from the repo root: bash docs/bug_reports/repro/BUG-003.sh
cd "$(dirname "$0")/../../.." && . docs/bug_reports/repro/_common.sh
start_app BUG-003 8803
c curl -s -X POST "$U/_reset"
for q in 1 2 3; do
  c curl -s -X POST -H "$J" -d "{\"customer\":\"C$q\",\"item\":\"Pen\",\"quantity\":$q}" "$U/orders"
done
c curl -s "$U/orders"
