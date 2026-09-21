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
