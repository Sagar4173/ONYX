"""Deterministic gates (spec 4.3.2): allowlist, syntax, diff cap, secrets."""
from services.ai.fix_gates import validate_patch

ORIG = "import os\n\ndef run(query):\n    return os.popen(query)\n"


def _gate(patched, **kw):
    args = dict(
        target_path="app/run.py",
        finding_file_path="app/run.py",
        original=ORIG,
        patched=patched,
        max_diff_lines=50,
    )
    args.update(kw)
    return validate_patch(**args)


def test_clean_patch_passes_with_diff_stats():
    patched = "import os\nimport shlex\n\ndef run(query):\n    return os.popen(shlex.quote(query))\n"
    report = _gate(patched)
    assert report.passed
    assert report.failures == []
    assert report.added_lines >= 1
    assert report.diff.startswith("---")


def test_allowlist_mismatch_fails():
    report = _gate(ORIG + "\n# x\n", target_path="other/evil.py")
    assert not report.passed
    assert any(f.gate == "allowlist" for f in report.failures)


def test_empty_patch_fails():
    report = _gate("   \n")
    assert any(f.gate == "non_empty" for f in report.failures)


def test_python_syntax_error_fails_with_location():
    report = _gate("def broken(:\n    pass\n")
    assert any(f.gate == "syntax" and "line 1" in f.message for f in report.failures)


def test_non_python_file_skips_syntax_gate():
    js = "function x( {\n"
    report = _gate(js, target_path="app/run.js", finding_file_path="app/run.js")
    assert not any(f.gate == "syntax" for f in report.failures)


def test_diff_cap_exceeded_fails():
    big = ORIG + "".join(f"# filler {i}\n" for i in range(60))
    report = _gate(big, max_diff_lines=50)
    assert any(f.gate == "diff_size" for f in report.failures)


def test_secret_on_added_line_fails_gate():
    patched = ORIG + 'TOKEN = "AKIA1234567890ABCDEF"\n'
    report = _gate(patched)
    assert any(f.gate == "secrets" for f in report.failures)


def test_preexisting_secret_in_untouched_original_is_not_rescanned():
    secret_orig = ORIG + 'LEGACY = "AKIA1234567890ABCDEF"\n'
    patched = secret_orig + "import sys\n"
    report = _gate(patched, original=secret_orig)
    assert report.passed
