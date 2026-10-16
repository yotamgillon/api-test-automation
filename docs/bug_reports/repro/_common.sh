# Shared helper, sourced by the BUG-00X.sh scripts. Run those from the repo root.
PY=${PY:-.venv/bin/python}
J="Content-Type: application/json"

start_app() { # $1 = bug id, $2 = port
  U=http://127.0.0.1:$2
  ENABLE_TEST_ENDPOINTS=1 BUGGY_MODE=$1 $PY -m uvicorn app.main:app --port "$2" --log-level warning &
  APP_PID=$!
  trap 'kill $APP_PID 2>/dev/null; wait $APP_PID 2>/dev/null' EXIT
  for _ in $(seq 1 50); do curl -s -o /dev/null "$U/orders" && break; sleep 0.2; done
  echo "# Reproduction run with BUGGY_MODE=$1 against $U"
}

c() { echo "\$ $*"; "$@"; echo; }
