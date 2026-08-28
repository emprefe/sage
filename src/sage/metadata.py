from __future__ import annotations

import struct
import zlib

from .core import Record, parse_record, serialize_record
from .errors import ValidationError
from .types import ABSENT, DAMAGED, INVALID, VALID, Evidence

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SAGE_KEYWORD = "SAGE"


def _chunks(data: bytes):
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG")
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        chunk_type = data[offset + 4:offset + 8]
        chunk_data = data[offset + 8:offset + 8 + length]
        yield offset, end, chunk_type, chunk_data
        offset = end
        if chunk_type == b"IEND":
            break


def _itxt(payload: bytes) -> bytes:
    keyword = SAGE_KEYWORD.encode("latin-1") + b"\0"
    # compression flag/method, language tag, translated keyword, UTF-8 text
    body = keyword + b"\0\0\0\0" + payload
    return _chunk(b"iTXt", body)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def _is_sage_itxt(chunk_data: bytes) -> bool:
    return chunk_data.startswith(SAGE_KEYWORD.encode("latin-1") + b"\0")


def write_metadata(data: bytes, record: Record) -> bytes:
    from PIL import Image
    import io
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "PNG":
                raise ValueError("input is not PNG")
            image.verify()
    except Exception as exc:
        raise ValueError("invalid PNG input") from exc
    payload = serialize_record(record)
    output = bytearray(PNG_SIGNATURE)
    inserted = False
    for _, _, kind, chunk_data in _chunks(data):
        if kind == b"iTXt" and _is_sage_itxt(chunk_data):
            if not inserted:
                output.extend(_itxt(payload))
                inserted = True
            continue
        output.extend(_chunk(kind, chunk_data))
        if kind == b"IHDR" and not inserted:
            output.extend(_itxt(payload))
            inserted = True
    if not inserted:
        raise ValueError("PNG has no IHDR")
    return bytes(output)


def remove_metadata(data: bytes) -> bytes:
    output = bytearray(PNG_SIGNATURE)
    for _, _, kind, chunk_data in _chunks(data):
        if kind == b"iTXt" and _is_sage_itxt(chunk_data):
            continue
        output.extend(_chunk(kind, chunk_data))
    return bytes(output)


def read_metadata(data: bytes, profile_id="SAGE-IMG-PNG-EXP", profile_version="0.01") -> Evidence:
    evidence = Evidence("METADATA", profile_id=profile_id, profile_version=profile_version)
    try:
        found = []
        for _, _, kind, chunk_data in _chunks(data):
            if kind == b"iTXt" and _is_sage_itxt(chunk_data):
                found.append(chunk_data)
        if not found:
            return evidence
        records = []
        for chunk_data in found:
            try:
                nul = chunk_data.find(b"\0")
                rest = chunk_data[nul + 1:]
                if len(rest) < 4:
                    raise ValidationError("INVALID_ITXT", "Malformed iTXt")
                text = rest[4:]
                records.append(parse_record(text))
            except ValidationError:
                evidence.status = INVALID
                evidence.diagnostics.append("INVALID_SAGE_ITXT")
                return evidence
        if any(record != records[0] for record in records[1:]):
            evidence.status = DAMAGED
            evidence.diagnostics.append("CONFLICTING_SAGE_METADATA_COPIES")
            return evidence
        evidence.status = VALID
        evidence.record = records[0]
        evidence.recovery_quality = "EXACT"
        evidence.recovery_metrics["metadata_copies_found"] = len(records)
        return evidence
    except (ValueError, struct.error):
        evidence.status = DAMAGED
        evidence.diagnostics.append("MALFORMED_PNG_METADATA")
        return evidence
