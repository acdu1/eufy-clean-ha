"""Unit tests for the utils module (encode/decode/varint)."""

from base64 import b64encode

import pytest

from custom_components.robovac_mqtt.proto.cloud.error_code_pb2 import ErrorCode
from custom_components.robovac_mqtt.utils import decode, encode, encode_message, encode_varint


def test_decode_empty_data_raises():
    """decode() with has_length=True and empty base64 raises ValueError."""
    empty_b64 = b64encode(b"").decode()
    with pytest.raises(ValueError, match="Cannot decode empty data"):
        decode(ErrorCode, empty_b64, has_length=True)


def test_decode_truncated_varint_raises():
    """decode() with only continuation bytes raises ValueError."""
    truncated_b64 = b64encode(b"\x80\x80").decode()
    with pytest.raises(ValueError, match="Truncated varint"):
        decode(ErrorCode, truncated_b64, has_length=True)


def test_decode_without_length_prefix():
    """decode() with has_length=False passes raw bytes directly to protobuf."""
    msg = ErrorCode()
    msg.error.append(42)
    raw = msg.SerializeToString()
    b64_data = b64encode(raw).decode()

    result = decode(ErrorCode, b64_data, has_length=False)
    assert 42 in result.error


def test_decode_valid_with_length_prefix():
    """Round-trip: encode_message then decode returns correct fields."""
    msg = ErrorCode()
    msg.error.append(7)
    encoded = encode_message(msg, has_length=True)

    result = decode(ErrorCode, encoded, has_length=True)
    assert 7 in result.error


def test_encode_varint_negative_raises():
    """encode_varint with a negative number raises ValueError."""
    with pytest.raises(ValueError, match="Cannot encode negative varint"):
        encode_varint(-1)


def test_encode_varint_zero():
    """encode_varint(0) returns a single zero byte."""
    assert encode_varint(0) == b"\x00"


def test_encode_varint_large():
    """encode_varint(300) returns the correct two-byte varint encoding."""
    assert encode_varint(300) == b"\xac\x02"


def test_encode_decode_roundtrip():
    """Full roundtrip: encode() a dict, decode() it back, verify fields."""
    encoded = encode(ErrorCode, {"error": [99, 100]}, has_length=True)

    result = decode(ErrorCode, encoded, has_length=True)
    assert list(result.error) == [99, 100]
