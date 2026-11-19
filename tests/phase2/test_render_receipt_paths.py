from pathlib import Path
from scripts.render_receipt_paths import receipt_path

def test_receipt_never_overwrites_editable_plan(tmp_path):
    plan=tmp_path/"film.json"
    plan.write_text('{"hello":"plan"}')
    output=tmp_path/"film.mp4"
    sidecar=receipt_path(output,plan)
    assert sidecar==tmp_path/"film.receipt.json"
    sidecar.write_text('{"result":"decoded"}')
    assert plan.read_text()=='{"hello":"plan"}'

def test_separate_plan_directory_keeps_legacy_receipt_path(tmp_path):
    plan=tmp_path/"plans"/"film.json"
    plan.parent.mkdir()
    output=tmp_path/"out"/"film.mp4"
    output.parent.mkdir()
    assert receipt_path(output,plan)==tmp_path/"out"/"film.json"

def test_no_plan_preserves_original_cli_receipt_behavior(tmp_path):
    assert receipt_path(tmp_path/"capture.mp4")==tmp_path/"capture.json"
