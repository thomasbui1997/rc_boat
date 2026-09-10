#!/usr/bin/env bash
# Start/stop the shore-side web app's static file server (web/).
# Usage: scripts/web_server.sh {start|stop|restart|status} [port]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$REPO_ROOT/.web_server.pid"
PORT_FILE="$REPO_ROOT/.web_server.port"
LOG_FILE="$REPO_ROOT/.web_server.log"
DEFAULT_PORT=8000

is_running() {
    [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

start() {
    local port="${1:-$DEFAULT_PORT}"

    if is_running; then
        echo "Web server already running (PID $(cat "$PID_FILE")) at http://localhost:$(cat "$PORT_FILE" 2>/dev/null || echo "?")/"
        return 0
    fi

    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "Port $port is already in use by another process. Pick a different port:" >&2
        echo "  scripts/web_server.sh start <port>" >&2
        return 1
    fi

    # cd as its own statement (not "cd ... && nohup ... &") so bash
    # backgrounds nohup directly instead of forking a wrapper subshell to
    # run the "&&" chain — otherwise $! is that wrapper's PID, not the
    # server's, and `stop` kills the wrong process and leaves the server
    # orphaned on the port.
    (
        cd "$REPO_ROOT"
        nohup python3 -m http.server "$port" --directory web \
            >"$LOG_FILE" 2>&1 &
        echo $! >"$PID_FILE"
    )
    echo "$port" >"$PORT_FILE"

    sleep 0.3
    if is_running; then
        echo "Web server started (PID $(cat "$PID_FILE")) at http://localhost:$port/"
        echo "Logs: $LOG_FILE"
    else
        echo "Web server failed to start; see $LOG_FILE" >&2
        rm -f "$PID_FILE" "$PORT_FILE"
        return 1
    fi
}

stop() {
    if ! is_running; then
        echo "Web server is not running."
        rm -f "$PID_FILE"
        return 0
    fi

    local pid
    pid="$(cat "$PID_FILE")"
    kill "$pid"
    for _ in $(seq 1 20); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.1
    done
    if kill -0 "$pid" 2>/dev/null; then
        echo "Process $pid did not stop gracefully; sending SIGKILL." >&2
        kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE" "$PORT_FILE"
    echo "Web server stopped."
}

status() {
    if is_running; then
        echo "Web server running (PID $(cat "$PID_FILE"))."
    else
        echo "Web server is not running."
    fi
}

cmd="${1:-}"
case "$cmd" in
    start)
        start "${2:-}"
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start "${2:-}"
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} [port]" >&2
        exit 1
        ;;
esac
