import io

from PIL import Image

from sage.core import ParticipantEntry, Record
from sage.decode import decode
from sage.encode import encode
from sage.types import NOT_DETECTED, PRESENT


def png_bytes():
    stream = io.BytesIO()
    Image.new("RGBA", (128, 128), (10, 20, 30, 255)).save(stream, format="PNG")
    return stream.getvalue()


def test_encode_decode_and_append():
    first, report = encode(png_bytes(), "A", ("one", None, None))
    assert report["self_check"] == "PASS"
    result = decode(first, "STRICT")
    assert result.presence == PRESENT
    assert result.record == Record((ParticipantEntry("A", ("one", None, None)),))
    second, _ = encode(first, "B", ("two", None, None))
    assert decode(second, "FAST").record == Record((ParticipantEntry("A", ("one", None, None)), ParticipantEntry("B", ("two", None, None))))


def test_clean_png_is_not_detected_but_concealed_is_explicitly_deferred():
    result = decode(png_bytes(), "NORMAL")
    assert result.presence == NOT_DETECTED


def test_invalid_mode_is_machine_readable():
    result = decode(png_bytes(), "BAD")
    assert result.status == "ERROR"
    assert result.error_code == "INVALID_MODE"
