#!/bin/sh
set -e

echo "========================================"
echo "Huawei SMS to PushOver starting..."
echo "========================================"

# Validate required config
if [ -z "$PUSHOVER_TOKEN" ] || [ -z "$PUSHOVER_USER" ]; then
    echo "ERROR: PUSHOVER_TOKEN and PUSHOVER_USER are required"
    exit 1
fi

# Run check-sms.py and handle exit codes:
#   0 = success
#   1 = fatal (config/auth error) — stop container
#   2 = retryable (network/transient) — log and continue
run_check() {
    rm -f /tmp/healthy
    EXIT_CODE=0
    python3 /app/check-sms.py || EXIT_CODE=$?
    if [ "$EXIT_CODE" = "0" ]; then
        touch /tmp/healthy
    elif [ "$EXIT_CODE" = "1" ]; then
        echo "FATAL ERROR (exit 1): stopping container"
        exit 1
    else
        echo "WARNING: transient error (exit $EXIT_CODE), will retry next interval"
    fi
}

if [ -z "$POLL_INTERVAL" ]; then
    echo "POLL_INTERVAL not set, running once and exiting"
    run_check
    exit 0
fi

# Validate POLL_INTERVAL is a positive integer
case "$POLL_INTERVAL" in
    ''|*[!0-9]*)
        echo "ERROR: POLL_INTERVAL must be a positive integer (got: '$POLL_INTERVAL')"
        exit 1
        ;;
esac
if [ "$POLL_INTERVAL" -le 0 ]; then
    echo "ERROR: POLL_INTERVAL must be greater than 0 (got: $POLL_INTERVAL)"
    exit 1
fi

echo "Router:   ${HUAWEI_ROUTER_IP_ADDRESS:-192.168.8.1} (${ROUTER_NAME:-Unknown Router})"
echo "Interval: every ${POLL_INTERVAL}s"
echo ""

# Optional: run once immediately on startup
if [ "$RUN_ON_START" = "true" ]; then
    echo "Running initial execution..."
    run_check
    echo ""
fi

echo "Starting poll loop..."
while true; do
    sleep "$POLL_INTERVAL"
    run_check
done
