from __future__ import annotations

from dataclasses import asdict

from .core import compare_records
from .profiles.png_exp import PngExperimentalProfile
from .types import ABSENT, CONFLICT, DAMAGED, INVALID, NOT_DETECTED, PRESENT, VALID, DecodeResult, Evidence


MODES = {"FAST", "NORMAL", "STRICT", "FORENSIC"}


def _resolve(result: DecodeResult) -> DecodeResult:
    evidence = result.metadata_evidence + result.concealed_evidence
    valid = []
    for item in evidence:
        if item.status == "VALID" and item.record is not None:
            if not any(compare_records(item.record, current) == "EQUAL" for current in valid):
                valid.append(item.record)
    result.profile_ids = sorted({f"{e.profile_id} {e.profile_version}" for e in evidence if e.profile_id})
    result.recovery_metrics = {
        "evidence_sources": len(evidence),
        "valid_records": len(valid),
        "damaged_evidence": sum(e.status == DAMAGED for e in evidence),
        "invalid_evidence": sum(e.status == INVALID for e in evidence),
    }
    if len(valid) > 1:
        result.detected = True
        result.presence = CONFLICT
        result.integrity = "MULTIPLE_VALID_RECORD_CONFLICT"
        result.candidate_records = valid
        return result
    if len(valid) == 1:
        result.detected = True
        result.presence = PRESENT
        result.record = valid[0]
        result.recovery_quality = "EXACT"
        statuses = {e.status for e in evidence}
        if DAMAGED in statuses:
            result.integrity = "VALID_RECORD_WITH_DAMAGED_SECONDARY"
        elif INVALID in statuses:
            result.integrity = "VALID_RECORD_WITH_INVALID_SECONDARY"
        elif len([e for e in evidence if e.status == VALID]) > 1:
            result.integrity = "AGREE"
        else:
            result.integrity = "SINGLE_LAYER"
        return result
    if any(e.status in (DAMAGED, INVALID) for e in evidence):
        result.detected = "POSSIBLE"
        result.presence = DAMAGED
        result.integrity = "NO_COMPLETE_VALID_RECORD"
        result.recovery_quality = "PARTIAL"
        return result
    result.detected = False
    result.presence = NOT_DETECTED
    result.integrity = "ALL_CHECKED_LAYERS_ABSENT"
    result.semantic_notes.append("NOT_DETECTED_DOES_NOT_MEAN_HUMAN_CREATED_OR_AUTHENTIC")
    return result


def decode(media: bytes, mode="NORMAL", options=None, profile=None) -> DecodeResult:
    result = DecodeResult(mode=mode)
    if mode not in MODES:
        result.status = "ERROR"
        result.error_code = "INVALID_MODE"
        result.errors.append("INVALID_MODE")
        return result
    profile = profile or PngExperimentalProfile()
    options = options or {}
    result.metadata_evidence = [profile.decode_metadata(media)]
    if mode == "FAST" and not options.get("concealed_sampling_decision", False):
        result = _resolve(result)
        result.semantic_notes.append("FAST_METADATA_ONLY_NO_CONCEALED_INTEGRITY_ASSURANCE")
        return result
    if mode == "NORMAL" and not options.get("concealed_sampling_decision", False):
        if result.metadata_evidence[0].status == "VALID":
            result = _resolve(result)
            result.semantic_notes.append("NORMAL_METADATA_FAST_PATH_CONCEALED_NOT_CHECKED")
            return result
    result.concealed_evidence = [profile.decode_concealed(media)]
    return _resolve(result)


def result_dict(result: DecodeResult) -> dict:
    def convert(value):
        if hasattr(value, "__dataclass_fields__"):
            return {k: convert(v) for k, v in asdict(value).items()}
        if isinstance(value, list):
            return [convert(v) for v in value]
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        return value
    return convert(result)
