# SAGE Participant Handshake Reference Implementation

This is an experimental, local-first reference implementation of the SAGE
provenance model. It is not a production watermark and does not authenticate
providers or establish that an asset is genuine.

The consolidated design direction is documented in
`sage_wp_v1.07_handshake_consolidated.pdf`. It proposes a minimal,
language-neutral participant handshake while explicitly separating that
proposal from the current v0.02 participant-handshake implementation. Earlier
v0.01 material remains as historical documentation only; the active runtime is
v0.02-only.

## Run

Use Python 3.10+ with Pillow and pytest installed:

```text
python -m pytest -q
python -m sage.cli encode input.png output.png --participant-id IMAGE_TOOL --ext-data-1 opaque_operation_id
python -m sage.cli decode output.png --mode STRICT
```

The PNG experimental profile stores the canonical record in an uncompressed
`iTXt` chunk and a deterministic, redundant tiled-LSB prototype. The concealed
layer is intentionally experimental; transformation robustness must be measured
against the corpus before making any production claim.

Generate a transformation report from an encoded PNG:

```text
python tools/transform_corpus.py tests/fixtures/encoded/encoded_lsb.png --output-dir tests/fixtures/transformed --report tests/reports/transform_report.json
```

The repository CI runs the pytest suite, Python compilation checks, and the
deterministic conformance vectors on Python 3.10 through 3.12.
