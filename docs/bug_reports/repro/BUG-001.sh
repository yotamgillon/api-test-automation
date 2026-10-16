#!/usr/bin/env bash
# BUG-001: zero or negative quantity is accepted. Run from the repo root: bash docs/bug_reports/repro/BUG-001.sh
cd "$(dirname "$0")/../../.." && . docs/bug_reports/repro/_common.sh
start_app BUG-001 8801
c curl -s -i -X POST "$U/_reset"
c curl -s -i -X POST -H "$J" -d '{"customer":"Ann","item":"Pen","quantity":-5}' "$U/orders"
c curl -s -i "$U/orders/ORD-0001"
