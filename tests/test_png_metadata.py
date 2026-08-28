import io

from PIL import Image, PngImagePlugin

from sage.core import Hop, Record
from sage.metadata import remove_metadata, read_metadata, write_metadata
from sage.types import ABSENT, VALID


def png_bytes():
    image = Image.new("RGB", (32, 24), (40, 90, 130))
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "unrelated metadata")
    stream = io.BytesIO()
    image.save(stream, format="PNG", pnginfo=info)
    return stream.getvalue()


def test_metadata_round_trip_and_unrelated_metadata_preservation():
    source = png_bytes()
    record = Record(0, (Hop("A", "one"),))
    encoded = write_metadata(source, record)
    evidence = read_metadata(encoded)
    assert evidence.status == VALID
    assert evidence.record == record
    with Image.open(io.BytesIO(encoded)) as image:
        assert image.info["Comment"] == "unrelated metadata"


def test_metadata_removal_returns_absent():
    source = png_bytes()
    encoded = write_metadata(source, Record(1, (Hop("A", "one"),)))
    assert read_metadata(remove_metadata(encoded)).status == ABSENT
