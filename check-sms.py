import os
import json
import time
import sys
import http.client
import urllib.parse
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip('"\'')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from huawei_lte_api.Client import Client
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.enums.sms import BoxTypeEnum
import huawei_lte_api.exceptions


@dataclass
class Config:
    """Configuration class for router and PushOver settings."""
    router_ip: str
    router_account: str
    router_password: str
    pushover_token: str
    pushover_user: str
    router_name: str
    max_retries: int = 3
    retry_delay: int = 5
    max_messages: int = 10
    sms_retention_days: int = 30
    dry_run: bool = False
    filter_phones: Optional[List[str]] = None
    filter_keywords: Optional[List[str]] = None
    pushover_priority: int = 0
    pushover_sound: Optional[str] = None

    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        def env(key, default=""):
            return os.getenv(key, default).strip('"\'')

        # Required fields
        router_ip = env("HUAWEI_ROUTER_IP_ADDRESS", "192.168.8.1")
        router_account = env("HUAWEI_ROUTER_ACCOUNT", "admin")
        router_password = env("HUAWEI_ROUTER_PASSWORD")
        pushover_token = env("PUSHOVER_TOKEN")
        pushover_user = env("PUSHOVER_USER")
        router_name = env("ROUTER_NAME", "Unknown Router")

        # Optional fields
        max_retries = int(env("MAX_RETRIES", "3"))
        retry_delay = int(env("RETRY_DELAY", "5"))
        max_messages = int(env("MAX_MESSAGES", "10"))
        sms_retention_days = int(env("SMS_RETENTION_DAYS", "30"))
        dry_run = env("DRY_RUN", "false").lower() == "true" or "--dry-run" in sys.argv

        # Filtering options
        filter_phones_str = env("FILTER_PHONES")
        filter_phones = [p.strip() for p in filter_phones_str.split(",")] if filter_phones_str else None

        filter_keywords_str = env("FILTER_KEYWORDS")
        filter_keywords = [k.strip() for k in filter_keywords_str.split(",")] if filter_keywords_str else None

        # PushOver options
        pushover_priority = int(env("PUSHOVER_PRIORITY", "0"))
        pushover_sound = env("PUSHOVER_SOUND") or None

        return cls(
            router_ip=router_ip,
            router_account=router_account,
            router_password=router_password,
            pushover_token=pushover_token,
            pushover_user=pushover_user,
            router_name=router_name,
            max_retries=max_retries,
            retry_delay=retry_delay,
            max_messages=max_messages,
            sms_retention_days=sms_retention_days,
            dry_run=dry_run,
            filter_phones=filter_phones,
            filter_keywords=filter_keywords,
            pushover_priority=pushover_priority,
            pushover_sound=pushover_sound
        )

    def validate(self) -> None:
        """Validate required configuration fields."""
        errors = []

        if not self.pushover_token:
            errors.append("PUSHOVER_TOKEN is required")
        if not self.pushover_user:
            errors.append("PUSHOVER_USER is required")
        if not self.router_ip:
            errors.append("HUAWEI_ROUTER_IP_ADDRESS is required")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        logger.info(f"Configuration loaded successfully for router: {self.router_name}")

        if self.dry_run:
            logger.warning("DRY RUN MODE - Router will be read but PushOver will NOT be called and messages will NOT be marked as read or deleted")

        if self.sms_retention_days > 0:
            logger.info(f"SMS retention enabled: Messages older than {self.sms_retention_days} days will be deleted")
        else:
            logger.info("SMS retention disabled: Messages will not be automatically deleted")

        if self.filter_phones:
            logger.info(f"Phone filter ENABLED: Only processing messages from: {self.filter_phones}")
            logger.warning("Messages from other numbers will be IGNORED")
        else:
            logger.debug("Phone filter disabled: Processing messages from all numbers")

        if self.filter_keywords:
            logger.info(f"Keyword filter ENABLED: Only processing messages containing: {self.filter_keywords}")
            logger.warning("Messages without these keywords will be IGNORED")
        else:
            logger.debug("Keyword filter disabled: Processing all message content")


@dataclass
class ProcessingStats:
    """Statistics for message processing."""
    total_messages: int = 0
    filtered_messages: int = 0
    processed_messages: int = 0
    failed_messages: int = 0
    filter_reasons: List[str] = field(default_factory=list)


class HuaweiSMSReader:
    """Class to handle reading SMS from Huawei router."""

    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[Client] = None
        self.connection = None

    def connect(self) -> bool:
        """Establish connection to the Huawei router."""
        try:
            if self.config.router_password == "":
                self.connection = AuthorizedConnection(
                    f'http://{self.config.router_ip}/',
                    timeout=30
                )
            else:
                password_encoded = urllib.parse.quote(self.config.router_password, safe='')
                self.connection = AuthorizedConnection(
                    f'http://{self.config.router_account}:{password_encoded}@{self.config.router_ip}/',
                    timeout=30
                )
            self.client = Client(self.connection)
            logger.info(f"Connected to router at {self.config.router_ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to router: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the router."""
        try:
            if self.client:
                self.client.user.logout()
                logger.debug("Logged out from router")
        except Exception as e:
            logger.warning(f"Error during logout: {e}")

    def get_unread_messages(self) -> List[Dict[str, Any]]:
        """Fetch unread SMS messages from the router."""
        if not self.client:
            logger.error("Client not connected")
            return []

        try:
            sms_response = self.client.sms.get_sms_list(
                1, BoxTypeEnum.LOCAL_INBOX, self.config.max_messages, 0, 0, 1
            )

            if sms_response.get('Messages') is None:
                logger.info("No messages found")
                return []

            messages = sms_response['Messages']['Message']

            if isinstance(messages, dict):
                messages = [messages]

            unread_messages = [msg for msg in messages if int(msg.get('Smstat', 1)) == 0]

            logger.info(f"Found {len(unread_messages)} unread message(s)")
            return unread_messages

        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    def mark_as_read(self, message_index: int) -> bool:
        """Mark a message as read."""
        if self.config.dry_run:
            logger.info(f"DRY RUN: Would mark message {message_index} as read")
            return True

        try:
            self.client.sms.set_read(message_index)
            logger.info(f"Marked message {message_index} as read")
            return True
        except Exception as e:
            logger.error(f"Failed to mark message {message_index} as read: {e}")
            return False

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number: strip spaces, ensure + prefix, strip leading zeros."""
        phone = phone.replace(' ', '').replace('-', '')
        if phone and not phone.startswith('+'):
            phone = '+' + phone.lstrip('0')
        return phone

    def should_process_message(self, message: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check if message should be processed based on filters."""
        phone = self.normalize_phone(message.get('Phone', ''))
        content = message.get('Content', '')
        content_preview = content[:50] + "..." if len(content) > 50 else content

        # Phone number filter — normalized exact match
        if self.config.filter_phones:
            normalized_filters = [self.normalize_phone(p) for p in self.config.filter_phones]
            if not any(phone == filter_phone for filter_phone in normalized_filters):
                reason = f"Phone {phone} not in whitelist {self.config.filter_phones}"
                logger.info(f"FILTERED: Message from {phone} - {reason}")
                logger.debug(f"Content preview: {content_preview}")
                return False, reason

        # Keyword filter
        if self.config.filter_keywords:
            if not any(keyword.lower() in content.lower() for keyword in self.config.filter_keywords):
                reason = f"Content missing required keywords: {self.config.filter_keywords}"
                logger.info(f"FILTERED: Message from {phone} - {reason}")
                logger.debug(f"Content preview: {content_preview}")
                return False, reason

        return True, None

    def get_device_info(self) -> str:
        """Get the device model name."""
        try:
            return self.client.device.information().get('DeviceName', 'Unknown')
        except Exception as e:
            logger.warning(f"Could not fetch device info: {e}")
            return "Unknown"

    def delete_message(self, message_index: int) -> bool:
        """Delete a message from the router."""
        if self.config.dry_run:
            logger.info(f"DRY RUN: Would delete message {message_index}")
            return True

        try:
            self.client.sms.delete_sms(message_index)
            logger.info(f"Deleted message {message_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete message {message_index}: {e}")
            return False

    def parse_message_date(self, date_str: str) -> Optional[datetime]:
        """Parse message date string to datetime object."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None

    def is_message_expired(self, message: Dict[str, Any]) -> bool:
        """Check if message is older than retention period."""
        if self.config.sms_retention_days <= 0:
            return False

        date_str = message.get('Date', '')
        message_date = self.parse_message_date(date_str)

        if not message_date:
            return False

        age_days = (datetime.now() - message_date).days
        return age_days > self.config.sms_retention_days

    def get_all_read_messages(self) -> List[Dict[str, Any]]:
        """Fetch all read SMS messages from the router."""
        if not self.client:
            logger.error("Client not connected")
            return []

        try:
            sms_response = self.client.sms.get_sms_list(
                1, BoxTypeEnum.LOCAL_INBOX, 50, 0, 0, 0
            )

            if sms_response.get('Messages') is None:
                return []

            messages = sms_response['Messages']['Message']

            if isinstance(messages, dict):
                messages = [messages]

            return [msg for msg in messages if int(msg.get('Smstat', 0)) == 1]

        except Exception as e:
            logger.error(f"Error fetching read messages: {e}")
            return []

    def get_recent_messages_summary(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get summary of recent messages (both read and unread) for diagnostics."""
        if not self.client:
            logger.error("Client not connected")
            return []

        try:
            sms_response = self.client.sms.get_sms_list(
                1, BoxTypeEnum.LOCAL_INBOX, limit, 0, 0, 0
            )

            if sms_response.get('Messages') is None:
                return []

            messages = sms_response['Messages']['Message']

            if isinstance(messages, dict):
                messages = [messages]

            return messages

        except Exception as e:
            logger.error(f"Error fetching recent messages: {e}")
            return []


class PushOverNotifier:
    """Class to handle PushOver notifications."""

    def __init__(self, config: Config):
        self.config = config

    def send_notification(self, message: str) -> bool:
        """Send notification to PushOver with retry mechanism."""
        if self.config.dry_run:
            logger.info("DRY RUN: Would send PushOver notification:")
            logger.info(message)
            return True

        for attempt in range(1, self.config.max_retries + 1):
            conn = None
            try:
                logger.debug(f"Sending notification (attempt {attempt}/{self.config.max_retries})")

                payload = {
                    "token": self.config.pushover_token,
                    "user": self.config.pushover_user,
                    "message": message,
                    "priority": self.config.pushover_priority,
                }

                if self.config.pushover_sound:
                    payload["sound"] = self.config.pushover_sound

                conn = http.client.HTTPSConnection("api.pushover.net:443", timeout=30)
                conn.request(
                    "POST",
                    "/1/messages.json",
                    urllib.parse.urlencode(payload),
                    {"Content-type": "application/x-www-form-urlencoded"}
                )

                response = conn.getresponse()
                response_string = response.read().decode('utf-8')
                json_obj = json.loads(response_string)

                if response.status == 200 and json_obj.get('status') == 1:
                    logger.info("PushOver notification sent successfully")
                    return True
                else:
                    logger.warning(f"PushOver failed: {response.reason} - {response_string}")

                    if attempt < self.config.max_retries:
                        logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                        time.sleep(self.config.retry_delay)

            except Exception as e:
                logger.error(f"Error sending notification (attempt {attempt}): {e}")
                if attempt < self.config.max_retries:
                    logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                    time.sleep(self.config.retry_delay)
            finally:
                if conn:
                    conn.close()

        logger.error(f"Failed to send notification after {self.config.max_retries} attempts")
        return False


    def send_test_notification(self, last_sms=None) -> bool:
        """Send a test notification to verify PushOver credentials work."""
        conn = None
        try:
            msg = f"Dry-run test from {self.config.router_name}\n"
            if last_sms:
                phone = last_sms.get('Phone', 'Unknown')
                date = last_sms.get('Date', 'Unknown')
                preview = last_sms.get('Content', '')[:80]
                msg += f"\nLast SMS: {phone} ({date})\n{preview}"
            else:
                msg += "No messages on router."
            msg += "\n\nPushOver credentials verified ✓"

            payload = {
                "token": self.config.pushover_token,
                "user": self.config.pushover_user,
                "message": msg,
                "priority": -1,
            }

            conn = http.client.HTTPSConnection("api.pushover.net:443", timeout=30)
            conn.request(
                "POST",
                "/1/messages.json",
                urllib.parse.urlencode(payload),
                {"Content-type": "application/x-www-form-urlencoded"}
            )

            response = conn.getresponse()
            response_string = response.read().decode("utf-8")
            json_obj = json.loads(response_string)

            if response.status == 200 and json_obj.get("status") == 1:
                logger.info("PushOver test notification sent successfully — credentials verified")
                return True
            else:
                logger.error(f"PushOver test FAILED: {response.reason} - {response_string}")
                return False
        except Exception as e:
            logger.error(f"PushOver test FAILED: {e}")
            return False
        finally:
            if conn:
                conn.close()


class SMSProcessor:
    """Main class to orchestrate SMS processing."""

    def __init__(self, config: Config):
        self.config = config
        self.sms_reader = HuaweiSMSReader(config)
        self.notifier = PushOverNotifier(config)

    def format_message(self, sms: Dict[str, Any], device_model: str) -> str:
        """Format SMS content for notification."""
        message = f"SMS from {self.config.router_name} (Huawei {device_model})\n"
        message += f"FROM: {sms.get('Phone', 'Unknown')} - "
        message += f"DATE: {sms.get('Date', 'Unknown')}\n"
        message += "CONTENT:\n"
        message += sms.get('Content', '')
        return message

    def cleanup_old_messages(self) -> int:
        """Delete old read messages based on retention policy. Returns number deleted."""
        if self.config.sms_retention_days <= 0:
            logger.debug("SMS retention disabled, skipping cleanup")
            return 0

        logger.info("Checking for old messages to delete...")

        read_messages = self.sms_reader.get_all_read_messages()

        if not read_messages:
            logger.debug("No read messages found")
            return 0

        deleted_count = 0

        for message in read_messages:
            try:
                if self.sms_reader.is_message_expired(message):
                    message_index = int(message.get('Index', 0))
                    phone = message.get('Phone', 'Unknown')
                    date = message.get('Date', 'Unknown')

                    logger.info(f"Deleting expired message from {phone} dated {date}")

                    if self.sms_reader.delete_message(message_index):
                        deleted_count += 1
            except Exception as e:
                logger.error(f"Error processing message for deletion: {e}")
                continue

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} expired message(s)")
        else:
            logger.debug("No expired messages to delete")

        return deleted_count

    def process(self) -> int:
        """Main processing logic. Returns processed count, or -1 on fatal error."""
        try:
            if not self.sms_reader.connect():
                logger.error("Failed to connect to router")
                return -1

            device_model = self.sms_reader.get_device_info()

            unread_messages = self.sms_reader.get_unread_messages()

            stats = ProcessingStats()
            stats.total_messages = len(unread_messages)

            if not unread_messages:
                logger.info("No unread messages found. Checking recent message history...")
                recent_messages = self.sms_reader.get_recent_messages_summary(limit=5)

                if recent_messages:
                    logger.info(f"Found {len(recent_messages)} recent message(s) (including read):")
                    for msg in recent_messages:
                        phone = msg.get('Phone', 'Unknown')
                        date = msg.get('Date', 'Unknown')
                        smstat = int(msg.get('Smstat', 1))
                        status = "UNREAD" if smstat == 0 else "READ"
                        content_preview = msg.get('Content', '')[:30] + "..."
                        logger.info(f"  [{status}] From: {phone}, Date: {date}")
                        logger.debug(f"       Preview: {content_preview}")
                else:
                    logger.info("No messages found in router inbox at all.")

                if self.config.dry_run:
                    last_sms = recent_messages[0] if recent_messages else None
                    logger.info("Sending dry-run test notification...")
                    if not self.notifier.send_test_notification(last_sms=last_sms):
                        logger.error("PushOver credential verification failed!")

                self.cleanup_old_messages()
                return 0

            if self.config.dry_run:
                last_sms = unread_messages[0] if unread_messages else None
                logger.info("Sending dry-run test notification...")
                if not self.notifier.send_test_notification(last_sms=last_sms):
                    logger.error("PushOver credential verification failed!")

            processed_count = 0

            for sms in unread_messages:
                try:
                    should_process, filter_reason = self.sms_reader.should_process_message(sms)
                    if not should_process:
                        stats.filtered_messages += 1
                        stats.filter_reasons.append(filter_reason)
                        continue

                    formatted_message = self.format_message(sms, device_model)
                    logger.info(f"\n{'='*50}\n{formatted_message}\n{'='*50}")

                    if self.notifier.send_notification(formatted_message):
                        message_index = int(sms.get('Index', 0))
                        if self.sms_reader.mark_as_read(message_index):
                            processed_count += 1
                            stats.processed_messages += 1
                    else:
                        logger.warning(f"Skipping message {sms.get('Index')} - notification failed")
                        stats.failed_messages += 1

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    stats.failed_messages += 1
                    continue

            logger.info("=" * 60)
            logger.info("PROCESSING SUMMARY:")
            logger.info(f"  Total unread messages found: {stats.total_messages}")
            logger.info(f"  Filtered out: {stats.filtered_messages}")
            logger.info(f"  Successfully processed: {stats.processed_messages}")
            logger.info(f"  Failed to process: {stats.failed_messages}")

            if stats.filtered_messages > 0:
                logger.info("  Filter reasons:")
                for reason in stats.filter_reasons:
                    logger.info(f"    - {reason}")

            logger.info("=" * 60)

            self.cleanup_old_messages()

            return processed_count

        except huawei_lte_api.exceptions.ResponseErrorLoginRequiredException:
            logger.error("Session timeout, login again!")
            return -1
        except huawei_lte_api.exceptions.LoginErrorAlreadyLoginException:
            logger.warning("Already logged in, logging out")
            if self.sms_reader.client:
                self.sms_reader.client.user.logout()
            return 0
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return -1
        finally:
            self.sms_reader.disconnect()


def main():
    """Main entry point."""
    try:
        config = Config.from_env()
        config.validate()

        processor = SMSProcessor(config)
        result = processor.process()

        if result < 0:
            sys.exit(2)  # retryable/transient — entrypoint.sh will continue the loop

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
