from __future__ import annotations

import struct

from ..types import ABSENT, DAMAGED, Evidence
from .xmp import XMP_HEADER, evidence_from_xmp, make_xmp

class WebpMetadataProfile:
    id = "SAGE-IMG-WEBP-META"
    version = "0.01"
    concealed_supported = False

    def _chunks(self, media):
        if len(media) < 12 or media[:4] != b"RIFF" or media[8:12] != b"WEBP":
            raise ValueError("input is not WebP")
        offset = 12
        while offset + 8 <= len(media):
            kind = media[offset:offset + 4]
            length = struct.unpack("<I", media[offset + 4:offset + 8])[0]
            end = offset + 8 + length + (length & 1)
            if end > len(media):
                raise ValueError("truncated WebP chunk")
            yield offset, end, kind, media[offset + 8:offset + 8 + length]
            offset = end

    def decode_metadata(self, media):
        try:
            return evidence_from_xmp([payload for _, _, kind, payload in self._chunks(media) if kind == b"XMP "], self.id, self.version)
        except Exception:
            evidence = Evidence("METADATA", profile_id=self.id, profile_version=self.version)
            evidence.status = DAMAGED
            evidence.diagnostics.append("MALFORMED_WEBP_METADATA")
            return evidence

    def encode_metadata(self, media, record):
        list(self._chunks(media))
        payload = make_xmp(record)[len(XMP_HEADER):]
        chunk = b"XMP " + struct.pack("<I", len(payload)) + payload + (b"\0" if len(payload) & 1 else b"")
        output = bytearray(media[:12])
        inserted = False
        for start, end, kind, old_payload in self._chunks(media):
            if kind == b"XMP ":
                if not inserted:
                    output.extend(chunk)
                    inserted = True
                continue
            output.extend(media[start:end])
        if not inserted:
            output.extend(chunk)
        output[4:8] = struct.pack("<I", len(output) - 8)
        return bytes(output)

    def remove_metadata(self, media):
        output = bytearray(media[:12])
        for start, end, kind, payload in self._chunks(media):
            if kind != b"XMP ":
                output.extend(media[start:end])
        output[4:8] = struct.pack("<I", len(output) - 8)
        return bytes(output)

    def decode_concealed(self, media, recovery_level="STANDARD", scan_budget=None):
        return Evidence("CONCEALED", ABSENT, self.id, self.version)
