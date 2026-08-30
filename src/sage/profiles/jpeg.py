from __future__ import annotations

import io
import struct

from PIL import Image

from ..metadata import read_metadata
from ..types import ABSENT, Evidence
from .xmp import XMP_HEADER, evidence_from_xmp, make_xmp

class JpegMetadataProfile:
    id = "SAGE-IMG-JPEG-META"
    version = "0.01"
    concealed_supported = False

    def _segments(self, media):
        if not media.startswith(b"\xff\xd8"):
            raise ValueError("input is not JPEG")
        offset = 2
        while offset + 4 <= len(media):
            if media[offset] != 0xff:
                raise ValueError("malformed JPEG marker")
            marker = media[offset + 1]
            if marker in (0xd8, 0xd9):
                yield offset, offset + 2, marker, b""
                offset += 2
                if marker == 0xd9:
                    break
                continue
            if marker == 0xda:
                yield offset, len(media), marker, media[offset + 2:]
                break
            if offset + 4 > len(media):
                raise ValueError("truncated JPEG segment")
            length = struct.unpack(">H", media[offset + 2:offset + 4])[0]
            end = offset + 2 + length
            if end > len(media) or length < 2:
                raise ValueError("truncated JPEG segment")
            yield offset, end, marker, media[offset + 4:end]
            offset = end

    def decode_metadata(self, media):
        try:
            copies = [payload for _, _, marker, payload in self._segments(media) if marker == 0xe1 and payload.startswith(XMP_HEADER)]
            return evidence_from_xmp(copies, self.id, self.version)
        except Exception:
            evidence = Evidence("METADATA", profile_id=self.id, profile_version=self.version)
            evidence.status = "DAMAGED"
            evidence.diagnostics.append("MALFORMED_JPEG_METADATA")
            return evidence

    def encode_metadata(self, media, record):
        with Image.open(io.BytesIO(media)) as image:
            if image.format != "JPEG":
                raise ValueError("input is not JPEG")
            image.verify()
        xmp = make_xmp(record)
        segment = b"\xff\xe1" + struct.pack(">H", len(xmp) + 2) + xmp
        output = bytearray(b"\xff\xd8")
        inserted = False
        for start, end, marker, payload in self._segments(media):
            if marker == 0xd8:
                continue
            if marker == 0xda:
                if not inserted:
                    output.extend(segment)
                    inserted = True
                output.extend(media[start:])
                break
            if marker == 0xe1 and payload.startswith(XMP_HEADER):
                if not inserted:
                    output.extend(segment)
                    inserted = True
                continue
            output.extend(media[start:end])
        if not inserted:
            output.extend(segment)
        return bytes(output)

    def remove_metadata(self, media):
        output = bytearray(b"\xff\xd8")
        for start, end, marker, payload in self._segments(media):
            if marker == 0xd8:
                continue
            if marker == 0xe1 and payload.startswith(XMP_HEADER):
                continue
            output.extend(media[start:end])
        return bytes(output)

    def decode_concealed(self, media, recovery_level="STANDARD", scan_budget=None):
        return Evidence("CONCEALED", ABSENT, self.id, self.version)
