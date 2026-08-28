from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ABSENT = "ABSENT"
VALID = "VALID"
DAMAGED = "DAMAGED"
INVALID = "INVALID"

PRESENT = "PRESENT"
NOT_DETECTED = "NOT_DETECTED"
CONFLICT = "CONFLICT"


@dataclass
class Evidence:
    layer: str
    status: str = ABSENT
    profile_id: str | None = None
    profile_version: str | None = None
    record: Any = None
    recovery_quality: str | None = None
    recovery_metrics: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class DecodeResult:
    algorithm: str = "sage_decode"
    algorithm_version: str = "0.01"
    mode: str | None = None
    status: str = "SUCCESS"
    error_code: str | None = None
    error_details: Any = None
    presence: str | None = None
    detected: bool | str | None = None
    record: Any = None
    candidate_records: list[Any] = field(default_factory=list)
    integrity: str | None = None
    metadata_evidence: list[Evidence] = field(default_factory=list)
    concealed_evidence: list[Evidence] = field(default_factory=list)
    verification: str = "NOT_CHECKED"
    provider_verification: list[Any] = field(default_factory=list)
    asset_relation: str = "NOT_CHECKED"
    profile_ids: list[str] = field(default_factory=list)
    recovery_quality: str | None = None
    recovery_metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    semantic_notes: list[str] = field(default_factory=list)
    forensic: Any = None

    def as_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)
