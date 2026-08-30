from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass

from .errors import ValidationError

VERSION = "0.02"
LEGACY_VERSION = "0.01"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9._~-]{1,64}$")
_EXTENSION_BYTES = 256


@dataclass(frozen=True)
class ParticipantEntry:
    participant_id: str
    ext_data: tuple[str | None, str | None, str | None] = (None, None, None)


@dataclass(frozen=True)
class Record:
    chain: tuple[ParticipantEntry, ...]
    version: str = VERSION


@dataclass(frozen=True)
class Hop:
    """Legacy v0.01 entry retained for explicit backward parsing."""
    ai_id: str
    generation_id: str


@dataclass(frozen=True)
class LegacyRecord:
    source_type: int
    chain: tuple[Hop, ...]
    version: str = LEGACY_VERSION


AnyRecord = Record | LegacyRecord


def validate_identifier(value: str, field: str = "participant_id") -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValidationError(f"INVALID_{field.upper()}", f"Invalid {field}: {value!r}")


def _validate_extension(value: str | None, field: str) -> None:
    if value is not None and (not isinstance(value, str) or len(value.encode("utf-8")) > _EXTENSION_BYTES):
        raise ValidationError(f"INVALID_{field.upper()}", f"Invalid {field}")


def validate_record(record: AnyRecord) -> None:
    if isinstance(record, Record):
        if record.version != VERSION or not record.chain:
            raise ValidationError("INVALID_RECORD", "Unsupported or empty SAGE record")
        seen = set()
        for entry in record.chain:
            validate_identifier(entry.participant_id)
            if entry.participant_id in seen:
                raise ValidationError("DUPLICATE_PARTICIPANT_ID", "Participant IDs must be unique")
            seen.add(entry.participant_id)
            if len(entry.ext_data) != 3:
                raise ValidationError("INVALID_EXTENSION_FIELDS", "Exactly three extension slots are required")
            for index, value in enumerate(entry.ext_data, 1):
                _validate_extension(value, f"ext_data_{index}")
        return
    if isinstance(record, LegacyRecord):
        if record.version != LEGACY_VERSION or record.source_type not in (0, 1) or not record.chain:
            raise ValidationError("INVALID_RECORD", "Unsupported or malformed legacy SAGE record")
        for hop in record.chain:
            validate_identifier(hop.ai_id, "ai_id")
            validate_identifier(hop.generation_id, "generation_id")
        return
    raise ValidationError("INVALID_RECORD", "Unsupported or malformed SAGE record")


def _encode_extension(value: str | None) -> str:
    if value is None:
        return "-"
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=") or "-"


def _decode_extension(value: str) -> str | None:
    if value == "-":
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValidationError("INVALID_EXTENSION_DATA", "Invalid encoded extension data")
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
        raise ValidationError("INVALID_EXTENSION_DATA", "Invalid encoded extension data") from exc
    _validate_extension(decoded, "extension_data")
    return decoded


def serialize_record(record: AnyRecord) -> bytes:
    validate_record(record)
    if isinstance(record, LegacyRecord):
        text = f"SAGE/{LEGACY_VERSION}|{record.source_type}|" + "|".join(
            f"{hop.ai_id}:{hop.generation_id}" for hop in record.chain
        )
    else:
        entries = []
        for entry in record.chain:
            entries.append("|".join([entry.participant_id, *(_encode_extension(v) for v in entry.ext_data)]))
        text = f"SAGE/{VERSION}|" + "|".join(entries)
    return text.encode("utf-8")


def parse_record(payload: bytes | str) -> AnyRecord:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("INVALID_UTF8", "SAGE payload is not valid UTF-8") from exc
    if not isinstance(payload, str):
        raise ValidationError("INVALID_PAYLOAD", "SAGE payload must be bytes or text")
    parts = payload.split("|")
    if not parts:
        raise ValidationError("INVALID_RECORD", "Invalid SAGE record")
    if parts[0] == f"SAGE/{LEGACY_VERSION}":
        if len(parts) < 3:
            raise ValidationError("INVALID_RECORD", "Invalid legacy SAGE field count")
        try:
            source_type = int(parts[1])
        except ValueError as exc:
            raise ValidationError("INVALID_SOURCE_TYPE", "source_type must be 0 or 1") from exc
        hops = []
        for encoded in parts[2:]:
            if encoded.count(":") != 1:
                raise ValidationError("INVALID_HOP", "Each legacy hop must contain one colon")
            hops.append(Hop(*encoded.split(":", 1)))
        record = LegacyRecord(source_type, tuple(hops))
        validate_record(record)
        return record
    if parts[0] != f"SAGE/{VERSION}" or len(parts[1:]) % 4 != 0 or not parts[1:]:
        raise ValidationError("INVALID_RECORD", "Invalid SAGE participant record header or field count")
    entries = []
    for start in range(1, len(parts), 4):
        entries.append(ParticipantEntry(parts[start], tuple(_decode_extension(v) for v in parts[start + 1:start + 4])))
    record = Record(tuple(entries))
    validate_record(record)
    return record


def compare_records(left: AnyRecord, right: AnyRecord) -> str:
    try:
        validate_record(left)
        validate_record(right)
    except ValidationError:
        return "NOT_EQUAL"
    return "EQUAL" if left == right else "NOT_EQUAL"


def update_participant(record: Record, participant_id: str,
                       ext_data: tuple[str | None, str | None, str | None] = (None, None, None)) -> Record:
    validate_record(record)
    validate_identifier(participant_id)
    entry = ParticipantEntry(participant_id, ext_data)
    remaining = tuple(item for item in record.chain if item.participant_id != participant_id)
    result = Record(remaining + (entry,))
    validate_record(result)
    return result


def migrate_legacy(record: LegacyRecord) -> Record:
    validate_record(record)
    return Record(tuple(ParticipantEntry(hop.ai_id, (hop.generation_id, None, None)) for hop in record.chain))


def append_record(record: AnyRecord, participant_id: str, ext_data=None) -> AnyRecord:
    """Compatibility wrapper for legacy callers and the v0.02 update rule."""
    if isinstance(record, LegacyRecord):
        validate_record(record)
        validate_identifier(participant_id, "ai_id")
        if ext_data is None:
            raise ValidationError("LEGACY_APPEND_REQUIRES_GENERATION_ID", "Legacy append requires generation_id")
        remaining = tuple(item for item in record.chain if item.ai_id != participant_id)
        return LegacyRecord(record.source_type, remaining + (Hop(participant_id, ext_data),))
    return update_participant(record, participant_id, ext_data or (None, None, None))
