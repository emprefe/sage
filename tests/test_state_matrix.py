import io

from PIL import Image

from sage.core import Hop, Record
from sage.decode import decode
from sage.profiles.png_exp import PngExperimentalProfile
from sage.types import Evidence, ABSENT, DAMAGED, INVALID, VALID, PRESENT, CONFLICT


def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(stream, format="PNG")
    return stream.getvalue()


class StubProfile(PngExperimentalProfile):
    def __init__(self, metadata, concealed):
        self._metadata, self._concealed = metadata, concealed

    def decode_metadata(self, media):
        return self._metadata

    def decode_concealed(self, media, recovery_level="STANDARD", scan_budget=None):
        return self._concealed


def evidence(layer, status, record=None):
    return Evidence(layer, status, "TEST", "0.01", record)


def test_conflicting_layers_are_preserved():
    left = Record(0, (Hop("A", "one"),))
    right = Record(1, (Hop("B", "two"),))
    profile = StubProfile(evidence("METADATA", VALID, left), evidence("CONCEALED", VALID, right))
    result = decode(png_bytes(), "STRICT", profile=profile)
    assert result.presence == CONFLICT
    assert set(result.candidate_records) == {left, right}


def test_damage_without_complete_record_is_damaged():
    profile = StubProfile(evidence("METADATA", ABSENT), evidence("CONCEALED", DAMAGED))
    assert decode(png_bytes(), "STRICT", profile=profile).presence == DAMAGED
