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
