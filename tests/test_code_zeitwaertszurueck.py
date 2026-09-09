from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "code_zeitwaertszurueck.py"
SPEC = importlib.util.spec_from_file_location("code_zeitwaertszurueck", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
provenance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provenance)


def run(command, cwd: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=cwd,
        env=merged_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


class TemporaryGitRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def git(self, *args: str, check: bool = True, env: dict[str, str] | None = None) -> str:
        result = run(["git", *args], self.root, env=env)
        if check and result.returncode != 0:
            raise AssertionError(
                f"git {' '.join(args)} failed ({result.returncode})\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return result.stdout.strip()

    def write(self, relative: str, content: str | bytes) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8", newline="\n")

    def commit(self, message: str, timestamp: str) -> str:
        self.git("add", "--all")
        commit_env = {
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }
        self.git("commit", "-m", message, env=commit_env)
        return self.git("rev-parse", "HEAD")


class ProvenanceUnitTests(unittest.TestCase):
    def test_canonical_json_and_digest_ignore_dictionary_insertion_order(self) -> None:
        left = {"z": [3, {"b": True, "a": "ä"}], "a": None}
        right = {"a": None, "z": [3, {"a": "ä", "b": True}]}
        self.assertEqual(provenance.canonical_json_bytes(left), provenance.canonical_json_bytes(right))
        self.assertEqual(provenance.snapshot_digest(left), provenance.snapshot_digest(right))

    def test_path_guards_reject_traversal_absolute_windows_and_git_metadata(self) -> None:
        bad_paths = (
            "",
            "../escape",
            "a/../escape",
            "/absolute",
            "C:/Windows/file",
            "a\\b",
            ".git/config",
            "safe/.GIT/config",
        )
        for path in bad_paths:
            with self.subTest(path=path):
                with self.assertRaises(provenance.ProvenanceError):
                    provenance.validate_git_path(path)
        self.assertEqual(provenance.validate_git_path("docs/PROGRAMM.md"), "docs/PROGRAMM.md")

    def test_repository_url_normalization_removes_transport_variants_and_rejects_credentials(self) -> None:
        expected = "https://github.com/Juri-Halveth/example"
        self.assertEqual(
            provenance.canonical_repository_url("git@github.com:Juri-Halveth/example.git"),
            expected,
        )
        self.assertEqual(
            provenance.canonical_repository_url("https://github.com/Juri-Halveth/example.git/"),
            expected,
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.canonical_repository_url("https://secret@example.test/owner/repo.git")
        with self.assertRaises(provenance.ProvenanceError):
            provenance.canonical_repository_url("file:///C:/Users/private/repo")

    def test_license_classifier_matches_explicit_map_and_stops_unknown_paths(self) -> None:
        self.assertEqual(provenance.classify_license("build_pdf.py")["licenseId"], "MIT")
        self.assertEqual(
            provenance.classify_license("docs/PROGRAMM.md")["licenseId"],
            "LicenseRef-Juri-Public-Interest-1.0",
        )
        self.assertEqual(
            provenance.classify_license("THIRD_PARTY_NOTICES.md")["licenseId"],
            "LicenseRef-Mixed-Third-Party-Terms",
        )
        self.assertEqual(provenance.classify_license("new-unmapped.bin")["licenseId"], "UNKNOWN")

    def test_resolve_repo_file_keeps_paths_inside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            inside = provenance.resolve_repo_file(root, "receipts/snapshot.json")
            self.assertEqual(inside, root / "receipts" / "snapshot.json")
            with self.assertRaises(provenance.ProvenanceError):
                provenance.resolve_repo_file(root, "../outside.json")


class ProvenanceGitIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name).resolve()
        self.repo = TemporaryGitRepository(root)
        self.repo.git("init", "--initial-branch=main")
        self.repo.git("config", "user.name", "Provenance Test")
        self.repo.git("config", "user.email", "provenance@example.invalid")
        self.repo.git("remote", "add", "origin", "git@github.com:Juri-Halveth/test-thesis.git")

        self.repo.write("LICENSE-JURI-PUBLIC-INTEREST.md", "custom license v1\n")
        self.repo.write("LICENSES.md", "# map v1\n")
        self.repo.write("README.md", "first edition\n")
        self.first_commit = self.repo.commit("initial edition", "2026-09-07T10:00:00+00:00")

        self.repo.write("README.md", "second edition\n")
        self.repo.write("docs/PROGRAMM.md", "program documentation\n")
        self.second_commit = self.repo.commit("second edition", "2026-09-08T10:00:00+00:00")
        tag_env = {
            "GIT_COMMITTER_DATE": "2026-09-09T10:00:00+00:00",
        }
        self.repo.git("tag", "-a", "v1.2.0", "-m", "release 1.2.0", env=tag_env)
        self.fixed_time = "2026-09-09T12:00:00Z"
        self.repository_url = "https://github.com/Juri-Halveth/test-thesis"

    def create(self) -> dict:
        return provenance.create_snapshot(
            self.repo.root,
            ref="v1.2.0",
            repository_url=self.repository_url,
            generated_at=self.fixed_time,
        )

    def write_manifest(self, name: str, snapshot: dict) -> Path:
        path = self.repo.root / name
        provenance.write_snapshot(path, snapshot)
        return path

    def test_annotated_tag_snapshot_binds_objects_files_history_and_verifies(self) -> None:
        snapshot = self.create()
        subject = snapshot["subject"]
        self.assertEqual(subject["refObjectType"], "tag")
        self.assertEqual(subject["commitId"], self.second_commit)
        self.assertEqual(subject["treeId"], self.repo.git("rev-parse", "HEAD^{tree}"))
        self.assertNotEqual(subject["refObjectId"], subject["commitId"])
        tag_payload = run(
            ["git", "cat-file", "tag", subject["refObjectId"]], self.repo.root
        ).stdout.encode("utf-8")
        self.assertEqual(subject["refObjectPayloadByteLength"], len(tag_payload))
        self.assertEqual(
            subject["refObjectPayloadSha256"], hashlib.sha256(tag_payload).hexdigest()
        )

        files = snapshot["fileSet"]["files"]
        paths = [record["path"] for record in files]
        self.assertEqual(paths, sorted(paths, key=lambda path: path.encode("utf-8")))
        readme = next(record for record in files if record["path"] == "README.md")
        readme_bytes = (self.repo.root / "README.md").read_bytes()
        self.assertEqual(readme["byteLength"], len(readme_bytes))
        self.assertEqual(readme["sha256"], hashlib.sha256(readme_bytes).hexdigest())
        self.assertEqual(
            readme["objectId"], self.repo.git("hash-object", "--", "README.md")
        )
        self.assertEqual(readme["history"]["lastVisibleChange"]["commitId"], self.second_commit)
        self.assertEqual(
            readme["history"]["firstVisibleAtCurrentPath"]["commitId"], self.first_commit
        )
        self.assertEqual(readme["history"]["visibleChangeCount"], 2)

        first_parent_ids = [record["commitId"] for record in snapshot["backwardTrace"]["commits"]]
        self.assertEqual(first_parent_ids, [self.second_commit, self.first_commit])
        self.assertEqual(
            snapshot["fileSet"]["sha256Root"], provenance.compute_file_root(files)
        )
        without_digest = dict(snapshot)
        without_digest.pop("snapshotDigest")
        self.assertEqual(snapshot["snapshotDigest"], provenance.snapshot_digest(without_digest))

        self.write_manifest("snapshot.json", snapshot)
        verified = provenance.verify_snapshot(self.repo.root, manifest="snapshot.json")
        self.assertEqual(verified["state"], "VERIFIED")
        self.assertEqual(verified["commitId"], self.second_commit)
        self.assertEqual(verified["snapshotDigest"], snapshot["snapshotDigest"])

    def test_lightweight_head_ref_binds_commit_as_ref_object(self) -> None:
        snapshot = provenance.create_snapshot(
            self.repo.root,
            ref="HEAD",
            repository_url=self.repository_url,
            generated_at=self.fixed_time,
        )
        self.assertEqual(snapshot["subject"]["refObjectType"], "commit")
        self.assertEqual(snapshot["subject"]["refObjectId"], self.second_commit)
        self.assertEqual(snapshot["subject"]["commitId"], self.second_commit)

    def test_first_parent_trace_excludes_the_merged_side_branch(self) -> None:
        self.repo.git("switch", "-c", "research-side", self.first_commit)
        self.repo.write("docs/FORSCHUNGSBASIS.md", "side branch evidence\n")
        side_commit = self.repo.commit("side branch", "2026-09-08T12:00:00+00:00")
        self.repo.git("switch", "main")
        merge_env = {
            "GIT_AUTHOR_DATE": "2026-09-08T13:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-09-08T13:00:00+00:00",
        }
        self.repo.git("merge", "--no-ff", "research-side", "-m", "merge research side", env=merge_env)
        merge_commit = self.repo.git("rev-parse", "HEAD")
        tag_env = {"GIT_COMMITTER_DATE": "2026-09-09T10:00:00+00:00"}
        self.repo.git("tag", "-f", "-a", "v1.2.0", "-m", "release after merge", env=tag_env)

        snapshot = self.create()
        history_ids = [
            record["commitId"] for record in snapshot["backwardTrace"]["commits"]
        ]
        self.assertEqual(history_ids, [merge_commit, self.second_commit, self.first_commit])
        self.assertNotIn(side_commit, history_ids)

    def test_cli_create_and_verify_write_canonical_json(self) -> None:
        create_result = run(
            [
                sys.executable,
                str(SCRIPT),
                "create",
                "--ref",
                "v1.2.0",
                "--repository-url",
                self.repository_url,
                "--generated-at",
                self.fixed_time,
                "--output",
                "receipts/snapshot.json",
            ],
            self.repo.root,
        )
        self.assertEqual(create_result.returncode, 0, create_result.stderr)
        created_summary = json.loads(create_result.stdout)
        self.assertEqual(created_summary["state"], "CREATED")
        manifest_path = self.repo.root / "receipts" / "snapshot.json"
        raw = manifest_path.read_bytes()
        stored = provenance.parse_json_bytes(raw)
        self.assertEqual(raw, provenance.canonical_json_bytes(stored) + b"\n")

        verify_result = run(
            [sys.executable, str(SCRIPT), "verify", "--manifest", "receipts/snapshot.json"],
            self.repo.root,
        )
        self.assertEqual(verify_result.returncode, 0, verify_result.stderr)
        self.assertEqual(json.loads(verify_result.stdout)["state"], "VERIFIED")

    def test_plain_digest_tampering_is_rejected(self) -> None:
        snapshot = self.create()
        snapshot["generatedAt"] = "2099-01-01T00:00:00Z"
        self.write_manifest("tampered-digest.json", snapshot)
        with self.assertRaisesRegex(provenance.ProvenanceError, "snapshot digest mismatch"):
            provenance.verify_snapshot(self.repo.root, manifest="tampered-digest.json")

    def test_recomputed_digest_cannot_hide_blob_record_tampering(self) -> None:
        snapshot = self.create()
        forged = copy.deepcopy(snapshot)
        forged.pop("snapshotDigest")
        record = forged["fileSet"]["files"][0]
        record["sha256"] = "0" * 64
        forged["fileSet"]["sha256Root"] = provenance.compute_file_root(
            forged["fileSet"]["files"]
        )
        forged = provenance.attach_snapshot_digest(forged)
        self.write_manifest("forged-blob.json", forged)
        with self.assertRaisesRegex(provenance.ProvenanceError, "does not match"):
            provenance.verify_snapshot(self.repo.root, manifest="forged-blob.json")

    def test_recomputed_digest_cannot_hide_unsafe_manifest_path(self) -> None:
        snapshot = self.create()
        forged = copy.deepcopy(snapshot)
        forged.pop("snapshotDigest")
        forged["fileSet"]["files"][0]["path"] = "../escape"
        forged = provenance.attach_snapshot_digest(forged)
        self.write_manifest("forged-path.json", forged)
        with self.assertRaisesRegex(provenance.ProvenanceError, "Git path"):
            provenance.verify_snapshot(self.repo.root, manifest="forged-path.json")

    def test_moved_tag_is_rejected_even_when_commit_tree_remains_available(self) -> None:
        snapshot = self.create()
        self.write_manifest("before-tag-move.json", snapshot)
        self.repo.git("tag", "-f", "v1.2.0", self.first_commit)
        with self.assertRaisesRegex(provenance.ProvenanceError, "does not match"):
            provenance.verify_snapshot(self.repo.root, manifest="before-tag-move.json")

    def test_unclassified_tree_path_stops_creation(self) -> None:
        self.repo.write("unmapped.bin", b"unmapped\x00bytes")
        self.repo.commit("add unmapped path", "2026-09-09T11:00:00+00:00")
        with self.assertRaisesRegex(provenance.ProvenanceError, "unclassified license paths"):
            provenance.create_snapshot(
                self.repo.root,
                ref="HEAD",
                repository_url=self.repository_url,
                generated_at=self.fixed_time,
            )


if __name__ == "__main__":
    unittest.main()
