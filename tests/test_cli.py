from pathlib import Path

from PIL import Image

from sage.cli import main


def png_path(path, size=(128, 128)):
    Image.new("RGBA", size, (10, 20, 30, 255)).save(path, format="PNG")


def test_cli_encode_decode_uses_participant_fields(capsys):
    output_dir = Path("local_test_outputs/cli")
    output_dir.mkdir(parents=True, exist_ok=True)
    source = output_dir / "source.png"
    output = output_dir / "output.png"
    png_path(source)
    assert main(["encode", str(source), str(output), "--participant-id", "EDITOR", "--ext-data-1", "op-1"]) == 0
    encoded = capsys.readouterr().out
    assert '"self_check": "PASS"' in encoded
    assert main(["decode", str(output), "--mode", "STRICT"]) == 0
    decoded = capsys.readouterr().out
    assert '"participant_id": "EDITOR"' in decoded


def test_cli_reports_capacity_error_as_machine_readable(capsys):
    output_dir = Path("local_test_outputs/cli")
    output_dir.mkdir(parents=True, exist_ok=True)
    source = output_dir / "tiny.png"
    output = output_dir / "tiny-output.png"
    png_path(source, size=(16, 16))
    assert main(["encode", str(source), str(output), "--participant-id", "EDITOR"]) == 2
    assert '"error_code": "CAPACITY_EXCEEDED"' in capsys.readouterr().out
