from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "idd" / "SKILL.md"


def test_bundled_idd_skill_routes_approved_execution_contract():
    assert SKILL.is_file(), "bundled /idd skill contract is missing"
    text = SKILL.read_text()

    assert "name: idd" in text
    assert "/itdd-prepare" in text
    assert "/itdd-execute" in text
    assert "approved" in text.lower()
    assert "BUILD" in text and "TEST" in text and "VERIFY" in text
    assert "fresh agent execution" in text
    assert ".idd/build_workspaces/" in text


def test_idd_reconstructs_resume_context_before_requesting_missing_details():
    text = SKILL.read_text().lower()
    for phrase in (
        "current conversation", "source contract", "project ledger",
        "assigned worktree", "build", "test", "verify", "last completed phase",
        "next authorized action", "failed candidate sha", "preserve prior reports",
    ):
        assert phrase in text
    assert "never infer approval" in text


def test_execute_preflights_live_state_and_reconciles_evidence_before_roles():
    path = ROOT / "skills" / "itdd-execute" / "SKILL.md"
    text = path.read_text().lower()
    for phrase in (
        "live agent roster", "assigned worktree", "head", "status",
        "latest role report", "contract", "candidate", "do not spawn",
        "completed phase", "durable evidence", "conflict",
    ):
        assert phrase in text
    assert "controller" in text and "approval" in text
