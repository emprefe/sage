from __future__ import annotations

import json
from pathlib import Path

from sage.core import ParticipantEntry, Record, parse_record, serialize_record


def main() -> int:
    vectors = [
        {"name": "single_participant", "record": Record((ParticipantEntry("A"),))},
        {"name": "ordered_chain", "record": Record((ParticipantEntry("A"), ParticipantEntry("B")))},
    ]
    output = []
    for vector in vectors:
        payload = serialize_record(vector["record"])
        output.append({"name": vector["name"], "payload_utf8": payload.decode(), "round_trip": parse_record(payload) == vector["record"]})
    report = {"algorithm": "sage_core", "version": "0.02", "vectors": output, "passed": all(x["round_trip"] for x in output)}
    target = Path(__file__).resolve().parents[1] / "tests" / "vectors" / "core_vectors.json"
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
