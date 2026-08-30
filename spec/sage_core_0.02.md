# SAGE Core 0.02 - Participant Handshake

This draft defines a small, language-neutral participant handshake. The active
runtime supports this format only; earlier experimental formats remain in the
repository as historical documents.

## Canonical form

```text
SAGE/0.02|<participant_id>|<ext1>|<ext2>|<ext3>|...
```

Each participant entry occupies four fields. Empty extension slots are encoded
as `-`. Non-empty extension values are UTF-8 strings encoded as unpadded URL-safe
base64. Each extension is limited to 256 UTF-8 bytes.

`PARTICIPANT_ID` is the only field with standardized SAGE meaning. Identifiers
match `[A-Za-z0-9._~-]{1,64}`. Extension values are opaque participant-owned
claims and are not authenticated or interpreted by SAGE.

## Chain rules

- A record must contain at least one participant entry.
- Each `PARTICIPANT_ID` appears at most once.
- Chain order represents relative most-recent SAGE-recorded participation.
- Updating an existing participant removes its old entry and appends the new entry.
- Repeating an update with the same entry is logically idempotent.
- Chain order is not authenticated wall-clock chronology.

## Equality and validation

Equality compares parsed logical entries, not raw strings. Serialization is
deterministic UTF-8. Malformed field counts, invalid identifiers, duplicate
participants, invalid base64, invalid UTF-8, and over-capacity extension values
are rejected.

## Trust boundary

SAGE reports surviving evidence that a participant was represented in a record.
It does not prove authenticity, complete history, custody, participant claims,
or that an unmarked asset is human-created. Registry lookup and visible markers
are optional enrichment outside Core semantics.
