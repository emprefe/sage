from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import ValidationError

VERSION = "0.01"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9._~-]{1,64}$")


@dataclass(frozen=True)
class Hop:
    ai_id: str
    generation_id: str


@dataclass(frozen=True)
class Record:
    source_type: int
    chain: tuple[Hop, ...]
    version: str = VERSION


def validate_identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValidationError(f"INVALID_{field.upper()}", f"Invalid {field}: {value!r}")


def validate_record(record: Record) -> None:
    if not isinstance(record, Record) or record.version != VERSION:
        raise ValidationError("INVALID_RECORD", "Unsupported or malformed SAGE record")
    if record.source_type not in (0, 1):
        raise ValidationError("INVALID_SOURCE_TYPE", "source_type must be 0 or 1")
    if not record.chain:
        raise ValidationError("EMPTY_CHAIN", "A SAGE record must contain at least one hop")
    for hop in record.chain:
        validate_identifier(hop.ai_id, "ai_id")
        validate_identifier(hop.generation_id, "generation_id")


def serialize_record(record: Record) -> bytes:
    validate_record(record)
    text = "SAGE/0.01|{}|{}".format(
        record.source_type,
        "|".join(f"{hop.ai_id}:{hop.generation_id}" for hop in record.chain),
    )
    return text.encode("utf-8")


def parse_record(payload: bytes | str) -> Record:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("INVALID_UTF8", "SAGE payload is not valid UTF-8") from exc
    if not isinstance(payload, str):
        raise ValidationError("INVALID_PAYLOAD", "SAGE payload must be bytes or text")
    parts = payload.split("|")
    if len(parts) < 3 or parts[0] != "SAGE/0.01":
        raise ValidationError("INVALID_RECORD", "Invalid SAGE record header or field count")
    try:
        source_type = int(parts[1])
    except ValueError as exc:
        raise ValidationError("INVALID_SOURCE_TYPE", "source_type must be 0 or 1") from exc
    hops = []
    for encoded in parts[2:]:
        if encoded.count(":") != 1:
            raise ValidationError("INVALID_HOP", "Each hop must contain one colon")
        ai_id, generation_id = encoded.split(":")
        hops.append(Hop(ai_id, generation_id))
    record = Record(source_type, tuple(hops))
    validate_record(record)
    return record


def compare_records(left: Record, right: Record) -> str:
    try:
        validate_record(left)
        validate_record(right)
    except ValidationError:
        return "NOT_EQUAL"
    return "EQUAL" if left == right else "NOT_EQUAL"


def append_record(record: Record, ai_id: str, generation_id: str) -> Record:
    validate_record(record)
    validate_identifier(ai_id, "ai_id")
    validate_identifier(generation_id, "generation_id")
    hop = Hop(ai_id, generation_id)
    if record.chain and record.chain[-1] == hop:
        return record
    return Record(record.source_type, record.chain + (hop,), record.version)
