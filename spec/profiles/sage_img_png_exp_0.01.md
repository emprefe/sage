# SAGE-IMG-PNG-EXP 0.01

The experimental profile stores the canonical Core record in an uncompressed
PNG `iTXt` chunk using the keyword `SAGE`. It preserves unrelated PNG chunks
where practical and reports `ABSENT`, `VALID`, `DAMAGED`, or `INVALID` layer
evidence. The current concealed prototype repeats a framed record across three
deterministic spatial tile regions using quantized red-channel 2x2 block means.
The frame contains a stable `SAGEPNG1` bootstrap, payload length, UTF-8 Core
record, and CRC32. This is an experiment only and is not claimed to resist
resizing, cropping, blur, screenshots, or lossy recompression.
