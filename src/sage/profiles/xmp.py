from __future__ import annotations

import re

from ..core import parse_record, serialize_record
from ..errors import ValidationError
from ..types import ABSENT, DAMAGED, INVALID, VALID, Evidence

XMP_HEADER = b"http://ns.adobe.com/xap/1.0/\0"
XMP_NS = "https://sage-protocol.org/ns/0.02/"
_RECORD = re.compile(rb"<sage:record>([^<]*)</sage:record>")


def make_xmp(record) -> bytes:
    value = serialize_record(record).decode("utf-8")
    body = (
        b"<?xpacket begin=\xef\xbb\xbf id=W5M0MpCehiHzreSzNTczkc9d?>"
        b"<x:xmpmeta xmlns:x=\"adobe:ns:meta/\"><rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\">"
        b"<rdf:Description xmlns:sage=\"" + XMP_NS.encode("ascii") + b"\"><sage:record>"
        + value.encode("utf-8")
        + b"</sage:record></rdf:Description></rdf:RDF></x:xmpmeta>"
        b"<?xpacket end=\"w\"?>"
    )
    return XMP_HEADER + body


def record_from_xmp(payload: bytes):
    match = _RECORD.search(payload)
    if not match:
        raise ValidationError("INVALID_XMP", "SAGE record is missing from XMP")
    return parse_record(match.group(1))


def evidence_from_xmp(copies: list[bytes], profile_id: str, profile_version: str) -> Evidence:
    evidence = Evidence("METADATA", profile_id=profile_id, profile_version=profile_version)
    if not copies:
        return evidence
    records = []
    for payload in copies:
        try:
            record = record_from_xmp(payload)
        except ValidationError:
            evidence.status = INVALID
            evidence.diagnostics.append("INVALID_SAGE_XMP")
            return evidence
        if record not in records:
            records.append(record)
    if len(records) != 1:
        evidence.status = DAMAGED
        evidence.diagnostics.append("CONFLICTING_SAGE_XMP_COPIES")
        return evidence
    evidence.status = VALID
    evidence.record = records[0]
    evidence.recovery_quality = "EXACT"
    evidence.recovery_metrics["metadata_copies_found"] = len(copies)
    return evidence
