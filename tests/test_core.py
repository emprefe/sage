import pytest

from sage.core import Hop, Record, append_record, compare_records, parse_record, serialize_record
from sage.errors import ValidationError


def test_round_trip_is_canonical():
    record = Record(1, (Hop("OPENAI", "gen_a"), Hop("EDITOR_2", "g-2")))
    payload = serialize_record(record)
    assert payload == b"SAGE/0.01|1|OPENAI:gen_a|EDITOR_2:g-2"
    assert parse_record(payload) == record


def test_append_preserves_order_and_source_type():
    record = Record(0, (Hop("A", "one"),))
    result = append_record(record, "B", "two")
    assert result.source_type == 0
    assert result.chain == (Hop("A", "one"), Hop("B", "two"))


def test_duplicate_last_hop_is_idempotent():
    record = Record(0, (Hop("A", "one"),))
    assert append_record(record, "A", "one") == record


@pytest.mark.parametrize("payload", [b"SAGE/0.01|2|A:x", b"SAGE/0.01|0|", b"SAGE/0.01|0|A:x:y"])
def test_invalid_records_rejected(payload):
    with pytest.raises(ValidationError):
        parse_record(payload)


def test_compare_records_uses_logical_values():
    left = Record(1, (Hop("A", "one"),))
    right = parse_record(serialize_record(left))
    assert compare_records(left, right) == "EQUAL"
