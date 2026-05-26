"""
Unit tests for structured logging: setup_logging() and log_tool_call().
"""
import json
import logging
import sys
import unittest
from unittest.mock import MagicMock

# Stub out webexpythonsdk so common.py can be imported without the real SDK
_sdk_stub = MagicMock()
sys.modules.setdefault("webexpythonsdk", _sdk_stub)
sys.modules.setdefault("webexpythonsdk.exceptions", _sdk_stub)

from webex_bot_mcp.tools.common import (  # noqa: E402
    _JsonFormatter,
    _kv,
    create_error_response,
    create_success_response,
    log_tool_call,
    setup_logging,
    WebexErrorCodes,
)


# ---------------------------------------------------------------------------
# Helper: a simple in-memory log handler
# ---------------------------------------------------------------------------
class _Collector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _fresh_logger() -> logging.Logger:
    """Return the webex_bot_mcp logger with all handlers cleared."""
    log = logging.getLogger("webex_bot_mcp")
    log.handlers.clear()
    log.setLevel(logging.DEBUG)
    log.propagate = False
    return log


# ---------------------------------------------------------------------------
# Tests: setup_logging
# ---------------------------------------------------------------------------
class TestSetupLogging(unittest.TestCase):

    def tearDown(self):
        _fresh_logger()  # leave the logger clean for other test suites

    def test_debug_mode_sets_level_to_debug(self):
        log = _fresh_logger()
        setup_logging(log_level="INFO", log_format="text", debug=True)
        self.assertEqual(log.level, logging.DEBUG)

    def test_non_debug_uses_log_level(self):
        log = _fresh_logger()
        setup_logging(log_level="WARNING", log_format="text", debug=False)
        self.assertEqual(log.level, logging.WARNING)

    def test_idempotent_second_call_is_noop(self):
        log = _fresh_logger()
        setup_logging(log_level="INFO", log_format="text", debug=False)
        handler_count = len(log.handlers)
        setup_logging(log_level="DEBUG", log_format="json", debug=True)
        # second call must not attach more handlers or change the level
        self.assertEqual(len(log.handlers), handler_count)
        self.assertEqual(log.level, logging.INFO)

    def test_json_format_attaches_json_formatter(self):
        log = _fresh_logger()
        setup_logging(log_level="INFO", log_format="json", debug=False)
        self.assertIsInstance(log.handlers[0].formatter, _JsonFormatter)

    def test_text_format_attaches_standard_formatter(self):
        log = _fresh_logger()
        setup_logging(log_level="INFO", log_format="text", debug=False)
        self.assertNotIsInstance(log.handlers[0].formatter, _JsonFormatter)


# ---------------------------------------------------------------------------
# Tests: _JsonFormatter
# ---------------------------------------------------------------------------
class TestJsonFormatter(unittest.TestCase):

    def _make_record(self, msg: str, extra: dict) -> logging.LogRecord:
        record = logging.LogRecord(
            name="webex_bot_mcp",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_output_is_valid_json(self):
        fmt = _JsonFormatter()
        record = self._make_record("hello", {"tool": "send_webex_message"})
        data = json.loads(fmt.format(record))
        self.assertEqual(data["message"], "hello")
        self.assertEqual(data["level"], "DEBUG")

    def test_extra_fields_included(self):
        fmt = _JsonFormatter()
        record = self._make_record("x", {"room_id": "abc123", "latency_ms": 42.1})
        data = json.loads(fmt.format(record))
        self.assertEqual(data["room_id"], "abc123")
        self.assertEqual(data["latency_ms"], 42.1)

    def test_timestamp_field_present(self):
        fmt = _JsonFormatter()
        record = self._make_record("ts", {})
        data = json.loads(fmt.format(record))
        self.assertIn("timestamp", data)


# ---------------------------------------------------------------------------
# Tests: _kv helper
# ---------------------------------------------------------------------------
class TestKvHelper(unittest.TestCase):

    def test_event_name_is_first_token(self):
        result = _kv("tool_request", {"tool": "list_rooms"})
        self.assertTrue(result.startswith("tool_request"))

    def test_string_values_are_repr_quoted(self):
        result = _kv("tool_request", {"tool": "list_rooms", "room_id": "abc"})
        self.assertIn("tool='list_rooms'", result)
        self.assertIn("room_id='abc'", result)

    def test_numeric_values_not_quoted(self):
        result = _kv("tool_response", {"latency_ms": 12.5})
        self.assertIn("latency_ms=12.5", result)


# ---------------------------------------------------------------------------
# Tests: log_tool_call decorator
# ---------------------------------------------------------------------------
class TestLogToolCall(unittest.TestCase):

    def _instrument(self, func):
        """Wrap func with log_tool_call and wire up a collecting handler."""
        collector = _Collector()
        log = _fresh_logger()
        log.addHandler(collector)
        return log_tool_call(func), collector.records

    def tearDown(self):
        _fresh_logger()

    # -- Return-value passthrough --

    def test_success_return_value_preserved(self):
        def my_tool(room_id=None):
            return create_success_response({"id": "r1"})

        wrapped, _ = self._instrument(my_tool)
        result = wrapped(room_id="r1")
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["id"], "r1")

    def test_error_return_value_preserved(self):
        def my_tool():
            return create_error_response(WebexErrorCodes.NOT_FOUND, "not found")

        wrapped, _ = self._instrument(my_tool)
        result = wrapped()
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "E404")

    # -- Log emission --

    def test_success_emits_two_debug_records(self):
        def my_tool(room_id=None):
            return create_success_response({})

        wrapped, records = self._instrument(my_tool)
        wrapped(room_id="abc")
        debug_records = [r for r in records if r.levelno == logging.DEBUG]
        self.assertEqual(len(debug_records), 2)
        msgs = [r.getMessage() for r in debug_records]
        self.assertTrue(any("tool_request" in m for m in msgs))
        self.assertTrue(any("tool_response" in m for m in msgs))

    def test_error_emits_warning_record(self):
        def my_tool():
            return create_error_response(WebexErrorCodes.INTERNAL_ERROR, "oops")

        wrapped, records = self._instrument(my_tool)
        wrapped()
        warning_records = [r for r in records if r.levelno == logging.WARNING]
        self.assertEqual(len(warning_records), 1)
        self.assertIn("E500", warning_records[0].getMessage())

    # -- Structured fields --

    def test_room_id_captured_in_record(self):
        def my_tool(room_id=None):
            return create_success_response({})

        wrapped, records = self._instrument(my_tool)
        wrapped(room_id="ROOM_XYZ")
        response_rec = next(r for r in records if "tool_response" in r.getMessage())
        self.assertEqual(response_rec.__dict__.get("room_id"), "ROOM_XYZ")

    def test_latency_ms_present_and_is_float(self):
        def my_tool():
            return create_success_response({})

        wrapped, records = self._instrument(my_tool)
        wrapped()
        response_rec = next(r for r in records if "tool_response" in r.getMessage())
        self.assertIn("latency_ms", response_rec.__dict__)
        self.assertIsInstance(response_rec.__dict__["latency_ms"], float)

    def test_error_code_in_warning_record_extra(self):
        def my_tool():
            return create_error_response(WebexErrorCodes.RATE_LIMITED, "slow down")

        wrapped, records = self._instrument(my_tool)
        wrapped()
        warning = next(r for r in records if r.levelno == logging.WARNING)
        self.assertEqual(warning.__dict__.get("error_code"), "E503")

    def test_tool_name_in_request_record(self):
        def list_webex_rooms():
            return create_success_response({})

        wrapped, records = self._instrument(list_webex_rooms)
        wrapped()
        request_rec = next(r for r in records if "tool_request" in r.getMessage())
        self.assertEqual(request_rec.__dict__.get("tool"), "list_webex_rooms")

    def test_status_success_in_response_record(self):
        def my_tool():
            return create_success_response({})

        wrapped, records = self._instrument(my_tool)
        wrapped()
        response_rec = next(r for r in records if "tool_response" in r.getMessage())
        self.assertEqual(response_rec.__dict__.get("status"), "success")

    def test_status_error_in_response_record(self):
        def my_tool():
            return create_error_response(WebexErrorCodes.FORBIDDEN, "no access")

        wrapped, records = self._instrument(my_tool)
        wrapped()
        response_rec = next(r for r in records if "tool_response" in r.getMessage())
        self.assertEqual(response_rec.__dict__.get("status"), "error")

    # -- functools.wraps metadata --

    def test_wraps_preserves_name_and_docstring(self):
        def my_special_tool(room_id: str = None) -> dict:
            """My special tool docstring."""
            return {}

        wrapped = log_tool_call(my_special_tool)
        self.assertEqual(wrapped.__name__, "my_special_tool")
        self.assertEqual(wrapped.__doc__, "My special tool docstring.")

    def test_wraps_sets_wrapped_attribute(self):
        def my_tool():
            return {}

        wrapped = log_tool_call(my_tool)
        self.assertIs(wrapped.__wrapped__, my_tool)


if __name__ == "__main__":
    unittest.main()
