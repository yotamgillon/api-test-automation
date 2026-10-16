#!/usr/bin/env bash
# BUG-004: an invalid status transition is accepted. Run from the repo root: bash docs/bug_reports/repro/BUG-004.sh
cd "$(dirname "$0")/../../.." && . docs/bug_reports/repro/_common.sh
start_app BUG-004 8804
c curl -s -X POST "$U/_reset"
c curl -s -X POST -H "$J" -d '{"customer":"Ann","item":"Pen","quantity":1}' "$U/orders"
c curl -s -i -X PUT -H "$J" -d '{"status":"delivered"}' "$U/orders/ORD-0001"
