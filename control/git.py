"""Small, structured Git adapter used for E7 attestation and integration."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from control.authority.paths import resolve_project_root
from control.events import EventLog, EventLogIntegrityError
from control.events.format import canonical_json


class GitError(ValueError): pass


class GitAdapter:
    def __init__(self, root: str | Path) -> None: self.root = resolve_project_root(root)
    def run(self, *args: str, cwd: Path | None = None) -> str:
        try: result = subprocess.run(["git", *args], cwd=cwd or self.root, text=True, capture_output=True, check=False)
        except OSError as exc: raise GitError("git unavailable") from exc
        if result.returncode: raise GitError((result.stderr or result.stdout).strip() or "git command failed")
        # Preserve Git porcelain's leading index/worktree status columns.  The
        # controller's bounded diff parser relies on those columns remaining
        # intact when validating Builder changes.
        return result.stdout.rstrip()
    def show(self, fmt: str, ref: str, *, cwd: Path | None = None) -> str: return self.run("show", "-s", f"--format={fmt}", ref, cwd=cwd)
    def exists(self, ref: str) -> bool:
        try: self.run("cat-file", "-e", f"{ref}^{{commit}}"); return True
        except GitError: return False
    def tree(self, ref: str) -> str: return self.show("%T", ref)
    def changed_paths(self, baseline: str, candidate: str) -> list[str]: return [x for x in self.run("diff", "--name-only", "--diff-filter=ACDMRTUXB", baseline, candidate).splitlines() if x]
    def identity(self) -> str: return self.run("rev-parse", "--show-toplevel")
    def is_ancestor(self, baseline: str, candidate: str) -> bool:
        try: self.run("merge-base", "--is-ancestor", baseline, candidate); return True
        except GitError: return False
    def head(self, cwd: Path) -> str: return self.run("rev-parse", "HEAD", cwd=cwd)


class CandidateAttestationStore:
    def __init__(self, root: str | Path) -> None: self.root = resolve_project_root(root); self.git = GitAdapter(self.root); self.events = EventLog(self.root)
    def path(self, attestation_id: str) -> Path: return self.root / ".idd/attestations" / f"{attestation_id}.json"
    def read(self, attestation_id: str) -> dict[str, Any]: return json.loads(self.path(attestation_id).read_text(encoding="utf-8"))
    def reconstruct(self) -> dict[str, dict[str, Any]]:
        out = {}
        for event in self.events.verify():
            if event["event_type"] == "candidate.git.attested": out[event["payload"]["attestation"]["attestation_id"]] = event["payload"]["attestation"]
        return out

    def attest(self, *, attestation_id: str, project_id: str, baseline_commit: str, candidate_commit: str, created_at: str, created_by: str = "controller") -> dict[str, Any]:
        if not self.git.exists(baseline_commit) or not self.git.exists(candidate_commit): raise GitError("commit does not exist in expected repository")
        if not self.git.is_ancestor(baseline_commit, candidate_commit): raise GitError("candidate is not related to baseline")
        candidate_tree = self.git.tree(candidate_commit); paths = self.git.changed_paths(baseline_commit, candidate_commit)
        item = {"attestation_id":attestation_id,"schema_version":1,"project_id":project_id,"baseline_commit":self.git.show("%H", baseline_commit),"candidate_commit":self.git.show("%H", candidate_commit),"candidate_tree":candidate_tree,"observed_changed_paths":paths,"repository_identity":self.git.identity(),"created_at":created_at,"created_by":created_by}
        item["attestation_hash"] = hashlib.sha256(canonical_json(item).encode()).hexdigest(); path = self.path(attestation_id); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(canonical_json(item)+"\n", encoding="utf-8")
        event = self.events.new_event(event_id=f"{attestation_id}-event", event_type="candidate.git.attested", timestamp=created_at, project_id=project_id, actor_type="controller", actor_id=created_by, payload={"attestation":item}); self.events.append(event); return item

    def verify(self, attestation_id: str) -> dict[str, Any]:
        item = self.read(attestation_id)
        if item != self.reconstruct().get(attestation_id): raise EventLogIntegrityError("attestation diverges from event history")
        actual = self.attest_preview(item["baseline_commit"], item["candidate_commit"])
        for key in ("candidate_tree", "observed_changed_paths", "repository_identity"):
            if actual[key] != item[key]: raise GitError(f"attestation {key} mismatch")
        return item

    def attest_preview(self, baseline: str, candidate: str) -> dict[str, Any]:
        if not self.git.exists(baseline) or not self.git.exists(candidate): raise GitError("commit does not exist")
        return {"candidate_tree":self.git.tree(candidate),"observed_changed_paths":self.git.changed_paths(baseline,candidate),"repository_identity":self.git.identity()}
