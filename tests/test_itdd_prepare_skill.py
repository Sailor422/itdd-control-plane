from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "itdd-prepare"


def test_prepare_skill_has_contract_and_reference_templates():
    text = (SKILL / "SKILL.md").read_text()
    for required in (
        "DISCOVERY", "GRILLING", "RESEARCH", "SPEC/TICKET DECOMPOSITION",
        "EXECUTION-CONTRACT DRAFTING", "INDEPENDENT REVIEW", "fresh",
        "BASELINE SHA", "ALLOWED PATHS/SCOPE", "ACCEPTANCE CRITERIA",
        "POSITIVE TESTS", "NEGATIVE/HOSTILE TESTS", "ARTIFACTS/EVIDENCE",
        "EXCLUSIONS", "HUMAN APPROVAL", "never implements code",
        "never invokes BUILD, TEST, or VERIFY",
        "clarification frontier", "explicit human designation", "never self-approve intent",
        "stop as `BLOCKED`",
    ):
        assert required in text
    assert (SKILL / "references" / "execution-contract-template.md").is_file()
    assert (SKILL / "references" / "preparation-checklist.md").is_file()


def test_prepare_skill_is_in_bundle_payload():
    # itdd-new copies every skill directory from the package bundle.
    assert (SKILL / "SKILL.md").is_file()
    assert (SKILL / "agents" / "openai.yaml").is_file()
    assert "itdd-prepare" in SKILL.name


def test_prepare_skill_prohibits_execution_and_requires_approval():
    text = (SKILL / "SKILL.md").read_text()
    assert "READY FOR HUMAN APPROVAL" in text
    assert "Do not call `/itdd-execute`" in text
    assert "six fresh execution identities" in text


def test_prepare_skill_routes_helpers_lazily_by_trigger():
    text = (SKILL / "SKILL.md").read_text()
    expected_routes = {
        "Ambiguity, contested assumptions, or an unresolved decision frontier": "`grilling`",
        "An external or repository fact is needed": "`research`",
        "Glossary terminology conflicts, or a glossary/ADR decision is needed": "`domain-modeling`",
        "A public seam or module boundary is unclear": "`codebase-design`",
        "Acceptance seams or positive/negative tests need shaping": "`tdd`",
        "A skill or handoff contract needs clearer agent-facing wording": "`writing-for-agents`",
        "An independent standards/spec review is required": "`code-review`",
        "A reproducible failure is reported and needs diagnosis": "`diagnosing-bugs`",
    }
    assert "## Lazy Pocock-skill routing" in text
    assert "Consult a helper skill only when its trigger applies" in text
    for trigger, helper in expected_routes.items():
        assert trigger in text
        assert helper in text


def test_prepare_skill_keeps_lazy_router_and_roles_non_executing():
    text = (SKILL / "SKILL.md").read_text()
    for required in (
        "fresh phase-agent identity",
        "ITDD role separation remain mandatory",
        "No helper skill may approve intent",
        "execute BUILD, TEST, or VERIFY",
    ):
        assert required in text
    assert "do not preload or run the" in text
    assert "future Kanban/UI consumer" in text
    for field in ("question", "recommendation", "human answer", "blocker", "phase", "execution identity"):
        assert f"`{field}`" in text
    assert "out of current implementation scope" in text
