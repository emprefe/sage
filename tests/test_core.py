import pytest

from sage.core import ParticipantEntry, Record, compare_records, parse_record, serialize_record, update_participant
from sage.errors import ValidationError


def test_round_trip_is_canonical():
    record = Record((ParticipantEntry("CAMERA", ("capture-1", None, "owner")), ParticipantEntry("EDITOR_2")))
    payload = serialize_record(record)
    assert payload == b"SAGE/0.02|CAMERA|Y2FwdHVyZS0x|-|b3duZXI|EDITOR_2|-|-|-"
    assert parse_record(payload) == record


def test_update_moves_existing_participant_to_end_and_replaces_data():
    record = Record((ParticipantEntry("A"), ParticipantEntry("B"), ParticipantEntry("C")))
    result = update_participant(record, "A", ("new", None, None))
    assert result.chain == (ParticipantEntry("B"), ParticipantEntry("C"), ParticipantEntry("A", ("new", None, None)))


def test_update_new_participant_appends():
    record = Record((ParticipantEntry("A"),))
    assert update_participant(record, "B").chain == (ParticipantEntry("A"), ParticipantEntry("B"))


def test_duplicate_participants_rejected():
    with pytest.raises(ValidationError):
        parse_record(b"SAGE/0.02|A|-|-|-|A|-|-|-")


def test_legacy_records_are_rejected_explicitly():
    with pytest.raises(ValidationError, match="Only SAGE/0.02 is supported"):
        parse_record(b"SAGE/0.01|1|A:one")


def test_invalid_records_rejected():
    for payload in (b"SAGE/0.02|A|-|-", b"SAGE/0.02|A|%%%|-|-", b"SAGE/0.02||-|-|-"):
        with pytest.raises(ValidationError):
            parse_record(payload)


def test_compare_records_uses_logical_values():
    left = Record((ParticipantEntry("A", ("one", None, None)),))
    right = parse_record(serialize_record(left))
    assert compare_records(left, right) == "EQUAL"


def test_extensions_round_trip_utf8_and_empty_slots():
    record = Record((ParticipantEntry("TOOL", ("cafe", "café", None)),))
    assert parse_record(serialize_record(record)) == record
