from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "itdd-prepare"


def prepare_skill_text():
    return " ".join((SKILL / "SKILL.md").read_text().split())


def test_prepare_skill_defines_planning_handoff_and_references():
    text = prepare_skill_text()
    for required in (
        "published spec and agreed tickets",
        "use `to-spec`",
        "Use `to-tickets`",
        "ordinary planning decision",
        "planning-handoff",
        "Stop here.",
    ):
        assert required in text
    assert (SKILL / "references" / "execution-contract-template.md").is_file()
    assert (SKILL / "references" / "preparation-checklist.md").is_file()


def test_planning_ticket_publication_uses_human_status_and_stops():
    text = prepare_skill_text()
    for required in (
        "`ready-for-human`",
        "do not add `ready-for-agent`",
        "Before publishing, verify",
        "stop without creating tickets",
        "do not follow",
        '"Work the frontier" instruction',
        "direct `/to-tickets` invocations keep that skill's own instructions",
    ):
        assert required in text


def test_prepare_skill_keeps_planning_separate_from_execution():
    text = prepare_skill_text()
    assert "never launches `/itdd-execute`, BUILD, TEST, or VERIFY" in text
    assert "A separate human request is required to consider execution." in text
    assert "A planning handoff alone is never an execution contract or permission to run work." in text


def test_prepare_skill_is_in_bundle_payload():
    # itdd-new copies every skill directory from the package bundle.
    assert (SKILL / "SKILL.md").is_file()
    assert (SKILL / "agents" / "openai.yaml").is_file()
    assert "itdd-prepare" in SKILL.name
