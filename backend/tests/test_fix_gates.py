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


def test_added_line_with_triple_plus_prefix_is_captured_and_scanned():
    patched = ORIG + '++TOKEN = "AKIA1234567890ABCDEF"\n'
    report = _gate(patched)
    assert report.added_lines == 1
    assert any(f.gate == "secrets" for f in report.failures)


def test_added_lines_with_triple_plus_prefix_count_toward_diff_cap():
    patched = ORIG + "++alpha\n++beta\n"
    report = _gate(patched, max_diff_lines=1)
    assert report.added_lines == 2
    assert any(f.gate == "diff_size" for f in report.failures)


def test_removed_line_with_triple_dash_prefix_is_counted():
    original = ORIG + "--legacy\n"
    report = _gate(ORIG, original=original)
    assert report.removed_lines == 1


def test_allowlist_rejects_traversal_shaped_target_path():
    report = _gate(ORIG + "\n# x\n", target_path="../app/run.py")
    assert not report.passed
    assert any(f.gate == "allowlist" for f in report.failures)


def test_allowlist_rejects_sibling_of_dotfile_finding():
    report = _gate(ORIG + "\n# x\n", target_path="env", finding_file_path=".env")
    assert any(f.gate == "allowlist" for f in report.failures)


def test_allowlist_rejects_empty_target_path():
    report = _gate(ORIG + "\n# x\n", target_path="")
    assert any(f.gate == "allowlist" for f in report.failures)


def test_allowlist_accepts_normal_equivalent_paths():
    report = _gate(ORIG + "\n# x\n", target_path="./app/run.py")
    assert report.passed
