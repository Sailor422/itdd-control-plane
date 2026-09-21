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


def test_preparation_handoff_documents_lazy_helper_routing_and_boundaries():
    text = (ROOT / "docs" / "agents" / "itdd-preparation-execution-handoff.md").read_text()
    assert "## Lazy helper-skill routing" in text
    assert "/itdd-prepare` is an explicit router" in text
    for phrase in (
        "`grilling` for", "`research` for", "`domain-modeling` only",
        "`codebase-design` when", "`tdd` for", "`writing-for-agents` for",
        "`code-review` for", "`diagnosing-bugs` only",
        "fresh phase-agent", "ITDD role separation",
        "No helper can approve intent", "execute BUILD, TEST, or VERIFY",
        "future Kanban/UI consumer", "out of current implementation scope",
    ):
        assert phrase in text
    for field in ("question", "recommendation", "human answer", "blocker", "phase", "execution identity"):
        assert f"`{field}`" in text
    assert "no UI is added" in text
