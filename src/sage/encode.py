from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256

from .core import ParticipantEntry, Record, serialize_record, update_participant, validate_record
from .errors import SageError
from .profiles.png_exp import PngExperimentalProfile
from .types import DAMAGED, INVALID, VALID


class EncodeFailure(SageError):
    pass


def _prior(meta, concealed):
    valid = [e for e in (meta, concealed) if e.status == VALID]
    records = []
    for evidence in valid:
        if not any(evidence.record == item for item in records):
            records.append(evidence.record)
    if len(records) > 1:
        raise EncodeFailure("PRIOR_CONFLICT", "Prior SAGE evidence conflicts")
    if records:
        secondary = [e.status for e in (meta, concealed) if e.status in (DAMAGED, INVALID)]
        return records[0], secondary
    if any(e.status == DAMAGED for e in (meta, concealed)):
        raise EncodeFailure("PRIOR_DAMAGED_UNRECOVERABLE", "Prior SAGE evidence is damaged")
    if any(e.status == INVALID for e in (meta, concealed)):
        raise EncodeFailure("PRIOR_INVALID", "Prior SAGE evidence is invalid")
    return None, []


def encode(media: bytes, current_participant_id: str, ext_data=None, profile=None) -> tuple[bytes, dict]:
    profile = profile or PngExperimentalProfile()
    try:
        meta = profile.decode_metadata(media)
        concealed = profile.decode_concealed(media)
        prior, secondary = _prior(meta, concealed)
        if prior is None:
            record = Record((ParticipantEntry(current_participant_id, _normalize_extensions(ext_data)),))
            validate_record(record)
            action = "CREATE_NEW_CHAIN"
        else:
            record = update_participant(prior, current_participant_id, _normalize_extensions(ext_data))
            action = "IDEMPOTENT_REWRITE" if record == prior else "APPEND_CHAIN"
        validate_record(record)
        serialized = serialize_record(record)
        output = profile.encode_metadata(media, record)
        if hasattr(profile, "encode_concealed"):
            output = profile.encode_concealed(output, record)
        verify = profile.decode_metadata(output)
        concealed_verify = profile.decode_concealed(output)
        if verify.status != VALID or verify.record != record or concealed_verify.status != VALID:
            raise EncodeFailure("SELF_CHECK_FAILED", "metadata self-check failed")
        report = {
            "logical_record": asdict(record),
            "serialized_bytes": len(serialized),
            "metadata_written": True,
            "concealed_written": True,
            "profile": f"{profile.id} {profile.version}",
            "encoder_version": "0.02",
            "prior_integrity": secondary,
            "action": action,
            "self_check": "PASS",
            "media_sha256": sha256(output).hexdigest(),
        }
        return output, report
    except SageError:
        raise
    except Exception as exc:
        if "capacity exceeded" in str(exc).lower():
            raise EncodeFailure("CAPACITY_EXCEEDED", str(exc)) from exc
        raise EncodeFailure("PROFILE_FAILURE", str(exc)) from exc


def _normalize_extensions(value):
    if value is None:
        return (None, None, None)
    if isinstance(value, str):
        return (value, None, None)
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return tuple(value)
    raise EncodeFailure("INVALID_EXTENSION_FIELDS", "ext_data must contain exactly three values")
