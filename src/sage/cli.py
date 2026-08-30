from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .decode import decode, result_dict
from .encode import EncodeFailure, encode


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="sage")
    sub = parser.add_subparsers(dest="command", required=True)
    enc = sub.add_parser("encode")
    enc.add_argument("input", type=Path)
    enc.add_argument("output", type=Path)
    enc.add_argument("--participant-id", required=True)
    enc.add_argument("--ext-data-1")
    enc.add_argument("--ext-data-2")
    enc.add_argument("--ext-data-3")
    dec = sub.add_parser("decode")
    dec.add_argument("input", type=Path)
    dec.add_argument("--mode", choices=("FAST", "NORMAL", "STRICT", "FORENSIC"), default="NORMAL")
    ins = sub.add_parser("inspect")
    ins.add_argument("input", type=Path)
    ins.add_argument("--mode", choices=("FAST", "NORMAL", "STRICT", "FORENSIC"), default="NORMAL")
    args = parser.parse_args(argv)
    try:
        if args.command == "encode":
            extensions = (args.ext_data_1, args.ext_data_2, args.ext_data_3)
            output, report = encode(args.input.read_bytes(), args.participant_id, extensions)
            args.output.write_bytes(output)
            print(json.dumps(report, sort_keys=True))
        else:
            result = decode(args.input.read_bytes(), args.mode)
            print(json.dumps(result_dict(result), sort_keys=True))
        return 0
    except EncodeFailure as exc:
        print(json.dumps({"status": "ERROR", "error_code": exc.code, "error_details": str(exc)}, sort_keys=True))
        return 2
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error_code": "INTERNAL_ERROR", "error_details": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
