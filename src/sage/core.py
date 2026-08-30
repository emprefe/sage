from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass

from .errors import ValidationError

VERSION = "0.02"
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


def validate_identifier(value: str, field: str = "participant_id") -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValidationError(f"INVALID_{field.upper()}", f"Invalid {field}: {value!r}")


def _validate_extension(value: str | None, field: str) -> None:
    if value is not None and (not isinstance(value, str) or len(value.encode("utf-8")) > _EXTENSION_BYTES):
        raise ValidationError(f"INVALID_{field.upper()}", f"Invalid {field}")


def validate_record(record: Record) -> None:
    if not isinstance(record, Record) or record.version != VERSION or not record.chain:
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


def _encode_extension(value: str | None) -> str:
    if value is None or value == "":
        return "-"
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


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


def serialize_record(record: Record) -> bytes:
    validate_record(record)
    fields = []
    for entry in record.chain:
        fields.extend([entry.participant_id, *(_encode_extension(value) for value in entry.ext_data)])
    return (f"SAGE/{VERSION}|" + "|".join(fields)).encode("utf-8")


def parse_record(payload: bytes | str) -> Record:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("INVALID_UTF8", "SAGE payload is not valid UTF-8") from exc
    if not isinstance(payload, str):
        raise ValidationError("INVALID_PAYLOAD", "SAGE payload must be bytes or text")
    parts = payload.split("|")
    if parts[0] != f"SAGE/{VERSION}":
        raise ValidationError("UNSUPPORTED_VERSION", "Only SAGE/0.02 is supported")
    if not parts[1:] or len(parts[1:]) % 4 != 0:
        raise ValidationError("INVALID_RECORD", "Invalid SAGE participant field count")
    entries = []
    for start in range(1, len(parts), 4):
        entries.append(ParticipantEntry(parts[start], tuple(_decode_extension(value) for value in parts[start + 1:start + 4])))
    record = Record(tuple(entries))
    validate_record(record)
    return record


def compare_records(left: Record, right: Record) -> str:
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
