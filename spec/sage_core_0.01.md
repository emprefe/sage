# SAGE Core Draft 0.01

The canonical logical record is UTF-8 text:

```text
SAGE/0.01|<source_type>|<ai_id>:<generation_id>|...
```

Identifiers match `[A-Za-z0-9._~-]{1,64}`. `source_type` is `0` for a non-AI
source later modified by AI and `1` for an AI-generated source. A record must
contain at least one ordered hop. Core serialization contains no transport
checksum, ECC, redundancy, placement data, or media hash.
