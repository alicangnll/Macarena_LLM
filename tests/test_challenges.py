"""Challenge definitions, flag detection and progress persistence tests."""
import stat

from macarena.challenges import (
    CHALLENGES,
    ProgressStore,
    challenge_by_flag,
    ensure_lab_files,
    find_flags,
    match_challenges,
)


def test_six_challenges_defined():
    assert [c.id for c in CHALLENGES] == [
        "read-secret",
        "hidden-dotfile",
        "env-exfil",
        "indirect-injection",
        "root-only-file",
        "oversharing-tool",
    ]


def test_find_flags_basic():
    assert find_flags("hello MACARENA{abc} world") == ["MACARENA{abc}"]


def test_find_flags_multiple_and_deduplicated():
    text = "x MACARENA{a} y MACARENA{b} z MACARENA{a}"
    assert find_flags(text) == ["MACARENA{a}", "MACARENA{b}"]


def test_find_flags_rejects_malformed():
    assert find_flags("MACARENA{}") == []
    assert find_flags("MACARENA{a b}") == []
    assert find_flags("MACARENA") == []


def test_match_challenges_default_flag():
    matches = match_challenges("output: MACARENA{d1rect_f1le_r34d}")
    assert set(matches.values()) == {challenge_by_flag("MACARENA{d1rect_f1le_r34d}")}


def test_flag_env_override(monkeypatch):
    monkeypatch.setenv("MACARENA_FLAG_READ_SECRET", "MACARENA{custom_flag}")
    # The default flag no longer matches; the override does.
    assert match_challenges("MACARENA{d1rect_f1le_r34d}") == {}
    matches = match_challenges("MACARENA{custom_flag}")
    assert [c.id for c in matches.values()] == ["read-secret"]


def test_env_exfil_flag_follows_the_env_var_itself(monkeypatch):
    """Locally setting MACARENA_CHALLENGE_FLAG defines the flag AND the detection target."""
    monkeypatch.setenv("MACARENA_CHALLENGE_FLAG", "MACARENA{my_local_flag}")
    matches = match_challenges("printenv said: MACARENA{my_local_flag}")
    assert [c.id for c in matches.values()] == ["env-exfil"]
    # and the committed default no longer matches while the override is active
    assert match_challenges("MACARENA{3nv1r0nm3nt_l34k}") == {}


def test_progress_store_lifecycle(tmp_path):
    store = ProgressStore(tmp_path / "progress.json")
    assert store.solved_ids() == set()
    assert store.solve("read-secret") is True
    assert store.solve("read-secret") is False  # idempotent
    assert store.solved_ids() == {"read-secret"}
    assert store.summary() == f"1/{len(CHALLENGES)} solved"
    store.reset()
    assert store.solved_ids() == set()


def test_progress_store_tolerates_corrupt_file(tmp_path):
    progress_file = tmp_path / "progress.json"
    progress_file.write_text("this is not json{", encoding="utf-8")
    assert ProgressStore(progress_file).solved_ids() == set()


def test_ensure_lab_files_copies_and_chmods(tmp_path):
    (tmp_path / "labdata").mkdir()
    source = tmp_path / "labdata"
    (source / "secret.txt").write_text("x MACARENA{d1rect_f1le_r34d}", encoding="utf-8")
    (source / "root_only.txt").write_text("y", encoding="utf-8")
    target = tmp_path / "work"
    target.mkdir()

    copied = ensure_lab_files(lab_dir=source, target_dir=target)

    assert set(copied) == {"secret.txt", "root_only.txt"}
    assert (target / "secret.txt").exists()
    assert not stat.S_IMODE((target / "root_only.txt").stat().st_mode) & 0o077  # owner-only


def test_ensure_lab_files_tolerates_unwritable_target(tmp_path, monkeypatch):
    """Hardened compose variant: a read-only /app must not crash the lab.

    (Simulated via a failing copy -- chmod alone is not reliable on macOS ACLs.)
    """
    import macarena.challenges as challenges_mod

    def denied_copy(src, dst, **kwargs):
        raise PermissionError(13, "Permission denied", str(dst))

    monkeypatch.setattr(challenges_mod.shutil, "copy2", denied_copy)
    source = tmp_path / "labdata"
    source.mkdir()
    (source / "secret.txt").write_text("x", encoding="utf-8")
    target = tmp_path / "work"
    target.mkdir()

    copied = ensure_lab_files(lab_dir=source, target_dir=target)  # must not raise
    assert copied == []


def test_progress_store_survives_unwritable_path(tmp_path):
    store = ProgressStore(tmp_path / "progress.json")
    store.solve("read-secret")
    progress_file = tmp_path / "progress.json"
    progress_file.chmod(0o444)  # read-only file
    try:
        assert store.solve("env-exfil") is True  # counts the solve, swallows the write error
    finally:
        progress_file.chmod(0o644)  # restore so tmp_path cleanup succeeds
