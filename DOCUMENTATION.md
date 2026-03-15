# Huawei Router SMS to PushOver - Complete Documentation

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Docker](#docker)
- [Configuration](#configuration)
- [Usage](#usage)
- [Advanced Features](#advanced-features)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)

## Overview

This Python script reads SMS messages from Huawei routers with HiLink enabled and forwards them to your devices via PushOver push notifications. Forked from [chenwei791129/Huawei-LTE-Router-SMS-to-E-mail-Sender](https://github.com/chenwei791129/Huawei-LTE-Router-SMS-to-E-mail-Sender) with extensive enhancements.

### Key Features

- **PushOver Integration** - Send SMS notifications to Android, iOS, and Desktop devices
- **Reliable Delivery** - Ensures PushOver received notification before marking SMS as read
- **Retry Mechanism** - Automatically retries failed notifications with configurable attempts and delays
- **Multiple SMS Processing** - Process multiple unread messages in a single run
- **Auto-Delete Old Messages** - Automatically removes processed messages after grace period
- **Smart Filtering** - Filter SMS by phone numbers or keywords
- **Dry Run Mode** - Sends a test PushOver notification with last SMS preview to verify full pipeline, then reads SMS without marking as read or deleting
- **Custom Notifications** - Configure PushOver priority levels and notification sounds
- **Comprehensive Logging** - Detailed logging with configurable log levels
- **Modular Design** - Clean, maintainable code with proper error handling
- **Environment Validation** - Validates required configuration before running

### Tested Devices

* Huawei H112-372
* Huawei H112-370
* Huawei H158-381
* Huawei E3372
* Huawei E5573Cs-322
* Huawei E5373s-155
* Huawei E8372 (requires several minutes to initialize)
* Raspberry Pi 4 Bullseye 64-bit

## Installation

### Prerequisites

Ensure you have Python 3.6+ and required system packages:

```bash
# On Debian/Ubuntu/Raspberry Pi OS
sudo apt update
sudo apt install -y python3-venv python3-pip
```

### Quick Setup (Recommended)

Use the automated setup script:

```bash
# 1. Clone the repository
git clone https://github.com/SalehCoder/Huawei-LTE-Router-SMS-to-PushOver.git
cd Huawei-Router-SMS-PushOver-Notifications

# 2. Run setup script (creates virtual environment and installs dependencies)
./setup.sh

# 3. Configure your settings
cp .env.example .env
nano .env
```

### Manual Setup

If you prefer manual setup:

```bash
# 1. Clone the repository
git clone https://github.com/SalehCoder/Huawei-LTE-Router-SMS-to-PushOver.git
cd Huawei-Router-SMS-PushOver-Notifications

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment variables
cp .env.example .env
nano .env
```

**Note:** This project uses a Python virtual environment to isolate dependencies and avoid conflicts.

## Docker

Docker is the recommended deployment method — no Python or system dependencies required on the host.

### Quick Start

```bash
cp .env.example .env
nano .env  # Add credentials and set POLL_INTERVAL
docker compose up -d
```

### Environment Variables (Docker-specific)

* `POLL_INTERVAL` - How often to check for SMS, in seconds (e.g. `10` for every 10 seconds, `300` for every 5 minutes)
* `RUN_ON_START` - Set to `"true"` to run once immediately when the container starts

### Build Locally

```bash
# Build image
docker build -t huawei-sms-pushover .

# Run once (no cron)
docker run --rm --network host --env-file .env huawei-sms-pushover

# Run with cron
docker compose up -d
```

### View Logs

```bash
docker compose logs -f
```

### Build and Push to container registry (Multi-arch)

```bash
./build.sh           # Push latest
./build.sh v1.0.0    # Push specific tag
```

Builds for `linux/amd64` and `linux/arm64` and pushes to:
`your-registry.example.com/your-image`

### Network Note

The container uses `network_mode: host` so it can reach the router on your LAN (default `192.168.8.1`). This is set in `compose.yaml`.

### One-shot Mode

If `POLL_INTERVAL` is not set, the container runs the script once and exits — useful for testing or manual runs from an external scheduler.

## Configuration

### Required Environment Variables

* `HUAWEI_ROUTER_PASSWORD` - Router admin password (leave empty if no password set)
* `PUSHOVER_TOKEN` - API Token from creating an application at [pushover.net](https://pushover.net)
* `PUSHOVER_USER` - Your user key from PushOver dashboard

### Optional Environment Variables

#### Router Settings

* `HUAWEI_ROUTER_IP_ADDRESS` - Router IP address (default: `192.168.8.1`)
* `HUAWEI_ROUTER_ACCOUNT` - Router login username (default: `admin`)
* `ROUTER_NAME` - Friendly name shown in notifications (default: `Unknown Router`)

#### Retry & Processing Settings

* `MAX_RETRIES` - Number of retry attempts for failed notifications (default: `3`)
* `RETRY_DELAY` - Delay in seconds between retries (default: `5`)
* `MAX_MESSAGES` - Maximum messages to process per run (default: `10`)
* `SMS_RETENTION_DAYS` - Auto-delete successfully sent messages older than X days (default: `30`, set to `0` to disable)

#### Dry Run Mode

* `DRY_RUN` - Set to `"true"` to connect to router, read SMS, send a test PushOver notification with last SMS preview (verifies full pipeline), without marking as read or deleting (default: `"false"`)

#### Filtering Options

* `FILTER_PHONES` - Comma-separated phone numbers to filter (only process SMS from these numbers)
  * Example: `FILTER_PHONES="+1234567890,+0987654321"`
* `FILTER_KEYWORDS` - Comma-separated keywords to filter (only process SMS containing these keywords, case-insensitive)
  * Example: `FILTER_KEYWORDS="urgent,important,alert"`

#### PushOver Advanced Options

* `PUSHOVER_PRIORITY` - Notification priority from -2 (lowest) to 2 (emergency) (default: `0`)
  * `-2`: No notification/alert
  * `-1`: Silent notification
  * `0`: Normal priority
  * `1`: High priority
  * `2`: Emergency (requires acknowledgment)
* `PUSHOVER_SOUND` - Custom notification sound (see [PushOver API docs](https://pushover.net/api#sounds))
  * Examples: `pushover`, `bike`, `bugle`, `cashregister`, `classical`, `cosmic`, `falling`, `gamelan`, `incoming`, `intermission`, `magic`, `mechanical`, `pianobar`, `siren`, `spacealarm`, `tugboat`, `alien`, `climb`, `persistent`, `echo`, `updown`, `none`

#### Logging

* `LOG_LEVEL` - Logging verbosity (default: `INFO`)
  * Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Usage

### Manual Execution

Using the shell script (automatically activates virtual environment):

```bash
./check-sms.sh
```

Or activate virtual environment and run directly:

```bash
source venv/bin/activate
python3 check-sms.py
```

### Test with Dry Run Mode

Dry run connects to the router, reads and filters SMS, sends a single test PushOver notification with last SMS preview (verifies full pipeline), then prints what would be notified — normal PushOver notifications are skipped and the router state is **not** touched (no mark-as-read, no deletion).

```bash
# CLI flag (recommended for one-off tests)
./check-sms.sh --dry-run

# Environment variable (Docker-friendly)
DRY_RUN=true ./check-sms.sh

# With debug logging
DRY_RUN=true LOG_LEVEL=DEBUG ./check-sms.sh

# Or set in .env file
# DRY_RUN="true"
```

### Automated Execution with Crontab

1. Make the shell script executable:
```bash
chmod +x check-sms.sh
```

2. Edit your crontab:
```bash
crontab -e
```

3. Add scheduling configuration:

**Run every 5 minutes:**
```
*/5 * * * * /full/path/to/Huawei-Router-SMS-PushOver-Notifications/check-sms.sh
```

**Run every minute:**
```
* * * * * /full/path/to/Huawei-Router-SMS-PushOver-Notifications/check-sms.sh
```

**Run every 20 seconds:**
```
* * * * * /full/path/to/Huawei-Router-SMS-PushOver-Notifications/check-sms.sh
* * * * * ( sleep 20 ; /full/path/to/Huawei-Router-SMS-PushOver-Notifications/check-sms.sh )
* * * * * ( sleep 40 ; /full/path/to/Huawei-Router-SMS-PushOver-Notifications/check-sms.sh )
```

**Note:** Replace `/full/path/to/` with your actual installation path.

### With Output Logging

Capture script output to log file:

```bash
# In crontab
*/5 * * * * /full/path/to/check-sms.sh >> /var/log/sms-checker.log 2>&1
```

## Advanced Features

### SMS Filtering

#### Filter by Phone Numbers (Whitelist)

Only process SMS from specific numbers:

```bash
# In .env
FILTER_PHONES="+1234567890,+0987654321,+1122334455"
```

#### Filter by Keywords

Only process SMS containing specific keywords:

```bash
# In .env
FILTER_KEYWORDS="urgent,important,OTP,verification,alert"
```

**Note:** Keyword filtering is case-insensitive.

### SMS Retention and Auto-Deletion

Prevent inbox overflow by automatically deleting old read messages:

```bash
# Delete messages older than 7 days
SMS_RETENTION_DAYS="7"

# Delete messages older than 30 days (default)
SMS_RETENTION_DAYS="30"

# Never delete messages
SMS_RETENTION_DAYS="0"
```

**Important:** Only read messages are deleted. Unread messages are never deleted automatically.

### Custom PushOver Notifications

#### Priority Levels

```bash
# Silent notifications (no sound/vibration)
PUSHOVER_PRIORITY="-1"

# Normal priority (default)
PUSHOVER_PRIORITY="0"

# High priority (bypasses quiet hours)
PUSHOVER_PRIORITY="1"

# Emergency priority (requires acknowledgment)
PUSHOVER_PRIORITY="2"
```

#### Custom Sounds

```bash
# Set custom notification sound
PUSHOVER_SOUND="siren"

# Available sounds: pushover, bike, bugle, cashregister, classical,
# cosmic, falling, gamelan, incoming, intermission, magic, mechanical,
# pianobar, siren, spacealarm, tugboat, alien, climb, persistent,
# echo, updown, none
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Temporary debug logging
LOG_LEVEL=DEBUG ./check-sms.sh

# Or set in .env file
LOG_LEVEL="DEBUG"
```

Debug logging shows:
- Configuration values (excluding sensitive data)
- Router connection details
- SMS message details
- PushOver API responses
- Retry attempts
- Deletion operations

## Use Cases

### Example 1: Filter Important Messages Only

Only process SMS containing specific keywords:

```bash
# In .env
FILTER_KEYWORDS="urgent,important,OTP,verification"
```

### Example 2: Monitor Specific Numbers

Only process SMS from specific phone numbers:

```bash
# In .env
FILTER_PHONES="+1234567890,+0987654321"
```

### Example 3: High Priority Emergency Alerts

Send emergency priority notifications with custom sound:

```bash
# In .env
PUSHOVER_PRIORITY="2"
PUSHOVER_SOUND="siren"
FILTER_KEYWORDS="emergency,alert,critical"
```

### Example 4: Silent Monitoring

Receive silent notifications for all SMS:

```bash
# In .env
PUSHOVER_PRIORITY="-1"
```

### Example 5: Testing Configuration

Test setup without touching the router or sending notifications:

```bash
# One-off CLI test
./check-sms.sh --dry-run

# Or set in .env for repeated dry tests
DRY_RUN="true"
LOG_LEVEL="DEBUG"
```

### Example 6: Prevent Inbox Overflow

Automatically delete old messages to keep inbox clean:

```bash
# In .env
SMS_RETENTION_DAYS="7"
```

### Example 7: Never Delete Messages

Keep all messages indefinitely:

```bash
# In .env
SMS_RETENTION_DAYS="0"
```

## Troubleshooting

### Virtual Environment Issues

**Virtual environment not found:**

```bash
# Run the setup script
./setup.sh
```

**Recreate virtual environment:**

```bash
# Remove existing venv
rm -rf venv

# Run setup again
./setup.sh
```

### Router Connection Issues

**Can't connect to router:**

```bash
# Test network connectivity
ping 192.168.8.1

# Test router web interface
curl -I http://192.168.8.1

# Check router IP in .env
grep HUAWEI_ROUTER_IP_ADDRESS .env
```

**Authentication failed:**

- Verify `HUAWEI_ROUTER_PASSWORD` in `.env`
- Check router web interface manually with same password
- Some routers have no password (leave empty)

**Connection timeout:**

- Check network connectivity to router
- Verify router is powered on and accessible
- Check if firewall is blocking connection

### PushOver Issues

**Notifications not arriving:**

```bash
# Test PushOver API manually
curl -s \
  --form-string "token=YOUR_TOKEN" \
  --form-string "user=YOUR_USER" \
  --form-string "message=Test from CLI" \
  https://api.pushover.net/1/messages.json

# Expected response: {"status":1,"request":"..."}
```

**Invalid token or user key:**

- Verify credentials at [pushover.net](https://pushover.net)
- Ensure PushOver app is installed on your device
- Check API token from your application dashboard
- Verify user key from account dashboard

### Message Processing Issues

**Messages not being marked as read:**

- Check logs for errors (`LOG_LEVEL=DEBUG`)
- Verify PushOver notification sent successfully
- Check script doesn't run in dry-run mode
- Ensure router API allows marking messages

**Messages being deleted unexpectedly:**

- Check `SMS_RETENTION_DAYS` setting
- Only read messages are deleted
- Set to `0` to disable deletion
- Check logs for deletion operations

### Configuration Issues

**Missing required variables:**

The script validates configuration on startup and provides clear error messages:

```bash
# Run with debug logging
LOG_LEVEL=DEBUG ./check-sms.sh

# Check configuration file
cat .env
```

**Configuration not loading:**

- Ensure `.env` file exists
- Check file permissions (`ls -l .env`)
- Verify no syntax errors in `.env`

### Python Version Issues

Check Python version:

```bash
python3 --version
# Should be 3.6 or higher
```

Install Python 3 if needed:

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### Scheduling Issues

**Docker: container not polling:**

```bash
# Check container is running
docker compose ps

# Check POLL_INTERVAL is set in .env
grep POLL_INTERVAL .env

# View logs
docker compose logs -f
```

**Bare metal cron not running:**

```bash
# Check crontab
crontab -l

# Test script manually first
./check-sms.sh

# Use absolute paths in crontab
*/1 * * * * /home/user/Huawei-Router-SMS-PushOver-Notifications/check-sms.sh
```

## Architecture

### Components

1. **check-sms.py** - Main Python script
   - Connects to Huawei router via HiLink API (30s timeout, URL-encoded auth)
   - Reads unread SMS messages, normalizes phone numbers
   - In dry-run mode: sends test notification with last SMS preview, prints what would be notified, skips normal PushOver
   - Sends PushOver notifications with retry logic
   - Marks messages as read only after confirmed delivery
   - Deletes old messages based on retention policy
   - Exit codes: 0=success, 1=fatal (stop container), 2=retryable (continue loop)

2. **entrypoint.sh** - Docker entrypoint
   - Validates required config on startup
   - Validates `POLL_INTERVAL` is a positive integer
   - Clears `/tmp/healthy` at the start of each run
   - Runs once immediately if `RUN_ON_START=true`
   - Starts poll loop with `POLL_INTERVAL` seconds between checks
   - If `POLL_INTERVAL` not set, runs once and exits
   - Handles exit code 1 (stop container) vs 2 (log warning, continue)

3. **Dockerfile** - Container image (Alpine 3.21 + tini + python3)

4. **compose.yaml** - Production deployment with healthcheck and host networking

5. **build.sh** - Multi-arch build for container registry (`linux/amd64` + `linux/arm64`)
6. **check-sms.sh** - Bare-metal wrapper
   - Activates Python virtual environment
   - Executes main script
   - Use this for direct cron jobs without Docker

7. **setup.sh** - Bare-metal setup
   - Creates Python virtual environment
   - Installs dependencies from requirements.txt

### Processing Flow

```
1. Load configuration from .env (+ --dry-run CLI flag)
2. Validate required settings
3. Connect to Huawei router (30s timeout)
4. Fetch unread SMS messages
5. Normalize phone numbers (strip spaces/dashes, ensure + prefix)
6. Apply filters (normalized phone exact match, keyword match)
7. For each message:
   a. Dry-run: print notification content, skip to step b
   b. Send to PushOver API (retry up to MAX_RETRIES)
   c. Mark as read only if notification succeeded
8. Check for old read messages (up to max_messages*20 or 200, whichever is greater)
9. Delete messages older than SMS_RETENTION_DAYS
10. Log summary and exit (code 0=ok, 1=fatal, 2=retryable)
```

**Docker poll loop:**
```
entrypoint.sh starts
  → RUN_ON_START=true → run immediately
  → loop: sleep POLL_INTERVAL → run → touch /tmp/healthy → repeat
```

### Design Principles

- **Safety First**: Messages only marked read after confirmed notification delivery
- **Reliability**: Automatic retry mechanism with configurable attempts
- **Isolation**: Virtual environment prevents dependency conflicts
- **Configurability**: All settings via environment variables
- **Error Handling**: Comprehensive error handling and logging
- **Modularity**: Clean separation of concerns with classes

### Dependencies

- `huawei-lte-api` - Python library for Huawei router API
- `python-dotenv` - Load environment variables from .env file

Minimal dependencies reduce attack surface and maintenance burden.

## Related Projects

- [Salamek/huawei-lte-api](https://github.com/Salamek/huawei-lte-api) - Huawei LTE router API library
- [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management
- [PushOver API](https://pushover.net/api) - Push notification service

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test thoroughly
4. Submit a pull request

## License

Open-source software licensed under the [MIT License](LICENSE).
