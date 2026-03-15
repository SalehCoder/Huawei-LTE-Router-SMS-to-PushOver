# Huawei Router SMS to PushOver Notifications

Forward SMS messages from your Huawei LTE/5G router to your mobile device via PushOver push notifications.

## Quick Deploy

### Docker (Recommended)

```bash
git clone https://github.com/SalehCoder/Huawei-LTE-Router-SMS-to-PushOver.git
cd Huawei-Router-SMS-PushOver-Notifications
cp .env.example .env
nano .env  # Add credentials and set POLL_INTERVAL
docker compose up -d
```

### Script (Bare Metal)

```bash
git clone https://github.com/SalehCoder/Huawei-LTE-Router-SMS-to-PushOver.git
cd Huawei-Router-SMS-PushOver-Notifications
./setup.sh
cp .env.example .env
nano .env  # Add credentials
./check-sms.sh
```

## Configuration

Edit `.env` with your settings:

```bash
# Required
HUAWEI_ROUTER_PASSWORD="your_password"
PUSHOVER_TOKEN="your_app_token"
PUSHOVER_USER="your_user_key"

# Optional
HUAWEI_ROUTER_IP_ADDRESS="192.168.8.1"
ROUTER_NAME="Home Router"
SMS_RETENTION_DAYS="30"
LOG_LEVEL="INFO"

# Docker only
POLL_INTERVAL="10"
RUN_ON_START="true"
```

Get PushOver credentials at [pushover.net](https://pushover.net)

## Usage

### Docker
```bash
# Start
docker compose up -d

# Logs
docker compose logs -f

# Stop
docker compose down
```

### Script
```bash
# Manual run
./check-sms.sh

# Dry run (reads router, prints what would be sent — no PushOver, no state change)
./check-sms.sh --dry-run

# Automated with cron (every 5 minutes)
*/5 * * * * /full/path/to/check-sms.sh
```

## How It Works

1. Connect to Huawei router via HiLink API
2. Read unread SMS messages
3. Send notifications to PushOver
4. Verify notification delivered successfully
5. Mark SMS as read only after confirmation
6. Auto-delete old read messages based on retention policy

## Features

- Reliable delivery — marks SMS read only after PushOver confirms receipt
- Automatic retries, smart filtering (phone/keyword), custom priority and sounds
- Dry-run mode — reads router and prints what would be sent, no PushOver or state changes
- Auto-cleanup — prevent inbox overflow by deleting old messages
- Docker support — built-in poll loop (sub-minute intervals), no host dependencies

## Tested Devices

Huawei H112-372, H112-370, H158-381, E3372, E5573Cs-322, E5373s-155, E8372 · Raspberry Pi 4

## Troubleshooting

**Can't connect to router?** → `ping 192.168.8.1` and check router is on HiLink mode

**PushOver not working?** → Test with `curl -s --form-string "token=X" --form-string "user=Y" --form-string "message=Test" https://api.pushover.net/1/messages.json`

**Docker: container can't reach router?** → Ensure `network_mode: host` is set in `compose.yaml`

**Virtual environment issues?** → `rm -rf venv && ./setup.sh`

**Enable detailed logging:** → `LOG_LEVEL=DEBUG ./check-sms.sh`

## Requirements

Docker Engine (recommended) · Python 3.6+ for bare metal · PushOver account · Huawei HiLink router

## Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed configuration, filtering, Docker guide, and architecture.

## License

[MIT License](LICENSE)
