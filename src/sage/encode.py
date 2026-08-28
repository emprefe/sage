from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256

from .core import Hop, Record, append_record, serialize_record, validate_record
from .errors import SageError, ValidationError
from .profiles.png_exp import PngExperimentalProfile
from .types import ABSENT, CONFLICT, DAMAGED, INVALID, VALID


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


def encode(media: bytes, current_ai_id: str, current_generation_id: str,
           new_asset_source_type: int | None = None, profile=None) -> tuple[bytes, dict]:
    profile = profile or PngExperimentalProfile()
    try:
        meta = profile.decode_metadata(media)
        concealed = profile.decode_concealed(media)
        prior, secondary = _prior(meta, concealed)
        if prior is None:
            if new_asset_source_type not in (0, 1):
                raise EncodeFailure("INVALID_SOURCE_TYPE", "source type is required for a new chain")
            record = Record(
                new_asset_source_type,
                (Hop(current_ai_id, current_generation_id),),
            )
            validate_record(record)
            action = "CREATE_NEW_CHAIN"
        else:
            record = append_record(prior, current_ai_id, current_generation_id)
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
            "encoder_version": "0.01",
            "prior_integrity": secondary,
            "action": action,
            "self_check": "PASS",
            "media_sha256": sha256(output).hexdigest(),
        }
        return output, report
    except SageError:
        raise
    except Exception as exc:
        raise EncodeFailure("PROFILE_FAILURE", str(exc)) from exc
