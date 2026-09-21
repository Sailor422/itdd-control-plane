from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_execute_requires_idd_and_isolated_build_workspace():
    text = (ROOT / "skills" / "itdd-execute" / "SKILL.md").read_text()
    assert "`/idd` top-level directive" in text
    assert "`.idd/build_workspaces/` boundary" in text
    assert "ordinary working tree" in text
    assert "preparation evidence" in text


def test_usage_documents_preparation_handoff_and_evidence():
    usage = (ROOT / "docs" / "agents" / "itdd-in-prime-usage.md").read_text()
    handoff = (ROOT / "docs" / "agents" / "itdd-preparation-execution-handoff.md").read_text()
    for text in (usage, handoff):
        assert "/idd" in text
        assert "clarification frontier" in text
        assert "explicit" in text and "designation" in text
        assert ".idd/build_workspaces/" in text
        assert ".idd/preparation/" in text
        assert "BUILD" in text and "TEST" in text and "VERIFY" in text
