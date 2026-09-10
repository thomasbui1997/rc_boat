#!/usr/bin/env bash
# Stop/check the boat-side telemetry sender running on the Pi over SSH.
# Usage: scripts/gps_sender.sh {stop|status}

set -euo pipefail

PI_HOST="thomasbui@boat-pi.local"
PROCESS_PATTERN="src.telemetry_sender"

remote_pids() {
    # pgrep exits 1 when no process matches, which is a normal "nothing
    # to report" outcome here, not a failure — don't let set -e treat it
    # as one (an unguarded `var=$(remote_pids)` would abort the script).
    ssh -o ConnectTimeout=5 "$PI_HOST" "pgrep -f '$PROCESS_PATTERN'" 2>/dev/null | tr '\n' ' ' || true
}

status() {
    local pids
    pids="$(remote_pids)"
    if [[ -n "${pids// /}" ]]; then
        echo "Telemetry sender running on $PI_HOST (PID(s): $pids)."
    else
        echo "Telemetry sender is not running on $PI_HOST."
    fi
}

stop() {
    local pids
    pids="$(remote_pids)"
    if [[ -z "${pids// /}" ]]; then
        echo "Telemetry sender is not running on $PI_HOST."
        return 0
    fi

    ssh -o ConnectTimeout=5 "$PI_HOST" "kill $pids"
    for _ in $(seq 1 20); do
        pids="$(remote_pids)"
        [[ -z "${pids// /}" ]] && break
        sleep 0.2
    done

    pids="$(remote_pids)"
    if [[ -n "${pids// /}" ]]; then
        echo "Process(es) did not stop gracefully; sending SIGKILL." >&2
        ssh -o ConnectTimeout=5 "$PI_HOST" "kill -9 $pids" || true
    fi
    echo "Telemetry sender stopped on $PI_HOST."
}

cmd="${1:-}"
case "$cmd" in
    stop)
        stop
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {stop|status}" >&2
        exit 1
        ;;
esac
