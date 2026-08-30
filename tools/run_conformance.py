from __future__ import annotations

import json
from pathlib import Path

from sage.core import parse_record, serialize_record
from sage.errors import ValidationError


def main() -> int:
    target = Path(__file__).resolve().parents[1] / "tests" / "vectors" / "core_vectors.json"
    source = json.loads(target.read_text(encoding="utf-8"))
    output = []
    for vector in source["vectors"]:
        payload = vector["payload_utf8"].encode("utf-8")
        parsed = parse_record(payload)
        canonical = serialize_record(parsed).decode("utf-8")
        output.append({"name": vector["name"], "canonical": canonical, "round_trip": canonical == vector["payload_utf8"]})
    invalid_output = []
    for vector in source.get("invalid_vectors", []):
        try:
            parse_record(vector["payload_utf8"])
        except ValidationError as exc:
            invalid_output.append({"name": vector["name"], "error_code": exc.code, "passed": exc.code == vector["error_code"]})
        else:
            invalid_output.append({"name": vector["name"], "error_code": None, "passed": False})
    report = {"algorithm": source["algorithm"], "version": source["version"], "vectors": output, "invalid_vectors": invalid_output, "passed": all(x["round_trip"] for x in output) and all(x["passed"] for x in invalid_output)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
