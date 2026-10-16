#!/usr/bin/env bash
# BUG-002: a missing order returns 200. Run from the repo root: bash docs/bug_reports/repro/BUG-002.sh
cd "$(dirname "$0")/../../.." && . docs/bug_reports/repro/_common.sh
start_app BUG-002 8802
c curl -s -i -X POST "$U/_reset"
c curl -s -i "$U/orders/DOES-NOT-EXIST"
