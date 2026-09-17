import importlib.util
import logging
import os
from pathlib import Path
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "check-sms.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_sms", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeConnection:
    def __init__(self, error=None):
        self.close_calls = 0
        self.error = error

    def close(self):
        self.close_calls += 1
        if self.error:
            raise self.error


class LoggingAndDisconnectTests(unittest.TestCase):
    def test_default_log_level_is_warning(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            module = load_module()
        self.assertEqual(module.LOG_LEVEL, "WARNING")

    def test_invalid_log_level_falls_back_to_warning(self):
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "NOT_A_LEVEL"}, clear=True):
            with mock.patch("logging.basicConfig") as basic_config:
                load_module()
        self.assertEqual(basic_config.call_args.kwargs["level"], logging.WARNING)

    def test_disconnect_uses_connection_close_and_clears_state(self):
        module = load_module()
        reader = module.HuaweiSMSReader(mock.Mock())
        connection = FakeConnection()
        client = mock.Mock()
        reader.connection = connection
        reader.client = client

        reader.disconnect()

        self.assertEqual(connection.close_calls, 1)
        self.assertIsNone(reader.connection)
        self.assertIsNone(reader.client)
        client.user.logout.assert_not_called()

    def test_disconnect_clears_state_when_close_fails(self):
        module = load_module()
        reader = module.HuaweiSMSReader(mock.Mock())
        connection = FakeConnection(RuntimeError("close failed"))
        reader.connection = connection
        reader.client = mock.Mock()

        with self.assertLogs(module.logger, level=logging.WARNING) as captured:
            reader.disconnect()

        self.assertEqual(connection.close_calls, 1)
        self.assertIn("Error while closing router connection", captured.output[0])
        self.assertIsNone(reader.connection)
        self.assertIsNone(reader.client)

    def test_already_logged_in_uses_finally_cleanup_not_direct_logout(self):
        module = load_module()
        config = module.Config("192.168.8.1", "admin", "", "test", "test", "test")
        processor = module.SMSProcessor(config)
        reader = mock.Mock()
        reader.connect.side_effect = module.huawei_lte_api.exceptions.LoginErrorAlreadyLoginException(
            "already logged in", 108006
        )
        processor.sms_reader = reader

        with self.assertLogs(module.logger, level=logging.WARNING):
            result = processor.process()

        self.assertEqual(result, 0)
        reader.client.user.logout.assert_not_called()
        reader.disconnect.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
