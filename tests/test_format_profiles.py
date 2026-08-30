import io

from PIL import Image

from sage.core import ParticipantEntry, Record
from sage.profiles import profile_for_format
from sage.types import ABSENT, VALID


def image_bytes(format_name):
    stream = io.BytesIO()
    Image.new("RGB", (32, 32), (20, 40, 60)).save(stream, format=format_name)
    return stream.getvalue()


def test_png_jpeg_and_webp_metadata_profiles_round_trip_and_remove():
    record = Record((ParticipantEntry("TEST"),))
    for format_name in ("PNG", "JPEG", "WEBP"):
        profile = profile_for_format(format_name)
        encoded = profile.encode_metadata(image_bytes(format_name), record)
        assert profile.decode_metadata(encoded).status == VALID
        assert profile.decode_metadata(encoded).record == record
        assert profile.decode_metadata(profile.remove_metadata(encoded)).status == ABSENT
        assert profile.decode_concealed(encoded).status == ABSENT
