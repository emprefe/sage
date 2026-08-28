from __future__ import annotations

import io
import struct
import zlib

from PIL import Image, PngImagePlugin

from ..core import parse_record, serialize_record
from ..metadata import read_metadata, remove_metadata, write_metadata
from ..types import ABSENT, DAMAGED, VALID, Evidence

MAGIC = b"SAGEPNG1"
COPY_COUNT = 3
BLOCK_SIZE = 2
QUANTUM = 16


def _bits(data: bytes):
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def _bytes(bits):
    output = bytearray()
    for start in range(0, len(bits) - 7, 8):
        value = 0
        for bit in bits[start:start + 8]:
            value = (value << 1) | bit
        output.append(value)
    return bytes(output)


def _frame(payload: bytes) -> bytes:
    return MAGIC + struct.pack(">H", len(payload)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xffffffff)


def _positions(width, height, copy_index):
    # Deterministic tiled traversal. Copies occupy interleaved tile regions.
    tile_w = max(1, width // 3)
    tile_h = max(1, height // 3)
    start_x = (copy_index % 3) * tile_w
    start_y = (copy_index // 3) * tile_h
    for y in range(start_y, height - BLOCK_SIZE + 1, BLOCK_SIZE):
        for x in range(start_x, width - BLOCK_SIZE + 1, BLOCK_SIZE):
            yield x, y


def _embed_copy(pixels, width, height, frame, copy_index):
    bit_iter = iter(_bits(frame))
    for x, y in _positions(width, height, copy_index):
        try:
            bit = next(bit_iter)
        except StopIteration:
            return True
        values = [pixels[x + dx, y + dy][0] for dy in range(BLOCK_SIZE) for dx in range(BLOCK_SIZE)]
        mean = sum(values) / len(values)
        base = int(round(mean / QUANTUM)) * QUANTUM
        if base + (QUANTUM * 3 // 4) > 255:
            base -= QUANTUM
        target = base + (QUANTUM * 3 // 4 if bit else QUANTUM // 4)
        delta = target - int(round(mean))
        for dy in range(BLOCK_SIZE):
            for dx in range(BLOCK_SIZE):
                pixel = list(pixels[x + dx, y + dy])
                pixel[0] = max(0, min(255, pixel[0] + delta))
                pixels[x + dx, y + dy] = tuple(pixel)
    return False


def _extract_copy(pixels, width, height, copy_index):
    bits = []
    for x, y in _positions(width, height, copy_index):
        values = [pixels[x + dx, y + dy][0] for dy in range(BLOCK_SIZE) for dx in range(BLOCK_SIZE)]
        mean = sum(values) / len(values)
        bits.append(1 if int(mean) % QUANTUM >= QUANTUM // 2 else 0)
    raw = _bytes(bits)
    if len(raw) < len(MAGIC) + 6 or not raw.startswith(MAGIC):
        return None
    length = struct.unpack(">H", raw[len(MAGIC):len(MAGIC) + 2])[0]
    end = len(MAGIC) + 2 + length + 4
    if end > len(raw):
        return None
    payload = raw[len(MAGIC) + 2:len(MAGIC) + 2 + length]
    checksum = struct.unpack(">I", raw[end - 4:end])[0]
    if zlib.crc32(payload) & 0xffffffff != checksum:
        return None
    return payload


class PngExperimentalProfile:
    id = "SAGE-IMG-PNG-EXP"
    version = "0.01"

    def decode_metadata(self, media: bytes) -> Evidence:
        return read_metadata(media, self.id, self.version)

    def encode_metadata(self, media: bytes, record):
        return write_metadata(media, record)

    def remove_metadata(self, media: bytes):
        return remove_metadata(media)

    def encode_concealed(self, media: bytes, record, recovery_level="STANDARD", scan_budget=None):
        try:
            with Image.open(io.BytesIO(media)) as source:
                if source.format != "PNG":
                    raise ValueError("input is not PNG")
                image = source.convert("RGBA")
                pixels = image.load()
                frame = _frame(serialize_record(record))
                capacity = sum(1 for _ in _positions(image.width, image.height, 0))
                if capacity < len(frame) * 8:
                    raise ValueError("PNG concealed capacity exceeded")
                for copy_index in range(COPY_COUNT):
                    if not _embed_copy(pixels, image.width, image.height, frame, copy_index):
                        raise ValueError("PNG concealed capacity exceeded")
                info = PngImagePlugin.PngInfo()
                for key, value in source.info.items():
                    if key == "SAGE":
                        continue
                    if isinstance(value, str):
                        info.add_text(key, value)
                info.add_itxt("SAGE", serialize_record(record).decode("utf-8"), zip=False)
                output = io.BytesIO()
                image.save(output, format="PNG", pnginfo=info, optimize=False, compress_level=9)
                return output.getvalue()
        except Exception as exc:
            raise ValueError(f"concealed encoding failed: {exc}") from exc

    def decode_concealed(self, media: bytes, recovery_level="STANDARD", scan_budget=None) -> Evidence:
        evidence = Evidence("CONCEALED", ABSENT, self.id, self.version)
        try:
            with Image.open(io.BytesIO(media)) as image:
                rgba = image.convert("RGBA")
                pixels = rgba.load()
                payloads = []
                for copy_index in range(COPY_COUNT):
                    payload = _extract_copy(pixels, rgba.width, rgba.height, copy_index)
                    if payload is not None:
                        payloads.append(payload)
                evidence.recovery_metrics.update({
                    "bootstrap_hits": len(payloads),
                    "redundant_copies_found": COPY_COUNT,
                    "redundant_copies_valid": len(payloads),
                })
                if not payloads:
                    return evidence
                records = []
                for payload in payloads:
                    try:
                        record = parse_record(payload)
                    except Exception:
                        continue
                    if record not in records:
                        records.append(record)
                if len(records) != 1:
                    evidence.status = DAMAGED
                    evidence.diagnostics.append("CONCEALED_COPY_CONFLICT_OR_INVALID")
                    return evidence
                evidence.status = VALID
                evidence.record = records[0]
                evidence.recovery_quality = "EXACT"
                return evidence
        except Exception:
            evidence.status = DAMAGED
            evidence.recovery_quality = "PARTIAL"
            evidence.diagnostics.append("MALFORMED_PNG_CONCEALED_LAYER")
            return evidence
