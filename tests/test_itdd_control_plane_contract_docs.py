from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_execute_requires_idd_and_isolated_build_workspace():
    text = (ROOT / "skills" / "itdd-execute" / "SKILL.md").read_text()
    assert "`/idd` top-level directive" in text
    assert "`.idd/build_workspaces/` boundary" in text
    assert "ordinary working tree" in text
    assert "preparation evidence" in text


def test_current_onboarding_is_unreleased_and_data_first():
    readme = (ROOT / "README.md").read_text()
    getting_started = (ROOT / "docs" / "GETTING-STARTED.md").read_text()
    usage = (ROOT / "docs" / "agents" / "itdd-in-prime-usage.md").read_text()

    for text in (readme, getting_started, usage):
        assert "Unreleased" in text
        assert "collect" in text.lower()
        assert "/itdd-prepare" in text
        assert "ready-for-agent" in text
        assert "BUILD" in text
        assert "TEST" in text
        assert "VERIFY" in text

    assert "not currently in use" in readme.lower()
    assert "/itdd-new` is optional" in readme
    assert "A separate explicit request" in usage
    assert "Return the links" in getting_started


def test_legacy_guides_are_archived_and_linked_from_archive_index():
    archive = (ROOT / "docs" / "archive" / "README.md").read_text()
    old_getting_started = (ROOT / "docs" / "archive" / "guides" / "GETTING-STARTED-LEGACY.md").read_text()
    old_handoff = (ROOT / "docs" / "archive" / "guides" / "itdd-preparation-execution-handoff.md").read_text()
    legacy_examples = (ROOT / "docs" / "archive" / "guides" / "legacy-controller-examples.md").read_text()

    assert "superseded" in old_getting_started
    assert "not current onboarding or authorization to execute" in old_handoff
    assert "not current onboarding" in legacy_examples
    for title in ("Legacy Getting Started guide", "Preparation-to-execution handoff", "Legacy controller examples"):
        assert title in archive


def test_archive_explains_research_and_evidence_status():
    archive = (ROOT / "docs" / "archive" / "README.md").read_text()
    inventory = (ROOT / "docs" / "archive" / "SOURCE-INVENTORY.md").read_text()
    history = (ROOT / "docs" / "archive" / "ENGINEERING-HISTORY.md").read_text()
    assert "source inventory" in archive.lower()
    assert "Historical acceptance" in archive
    assert "private session metadata" in archive
    assert "not a complete activity log" in history
    assert "does not certify the source set as sanitized" in inventory.lower()


def test_archive_catalog_distinguishes_public_summaries_from_raw_sources():
    catalog = (ROOT / "docs" / "archive" / "RESEARCH-CATALOG.md").read_text()
    assert "not a complete activity log" in catalog
    assert "Stage E5 result" in catalog
    assert "not proof of present-day behavior" in catalog
    assert "detailed operational forensic reports" in catalog.lower()
    assert "not copied here" in catalog
    assert "machine-specific environment metadata" in catalog
    assert "not an approved design" in catalog


def test_host_specific_source_notes_are_summarized_not_reproduced():
    audit = (ROOT / "docs" / "research" / "stage-a-codex-audit.md").read_text()
    bootstrap = (ROOT / "docs" / "specs" / "CODEX-BOOTSTRAP-SPEC.md").read_text()
    for text in (audit, bootstrap):
        assert "historical" in text.lower()
        assert "/Users/" not in text
        assert "CODEX_VAULT_DIR" not in text
    assert "older revisions may retain" in audit
    assert "older revisions may retain" in bootstrap
