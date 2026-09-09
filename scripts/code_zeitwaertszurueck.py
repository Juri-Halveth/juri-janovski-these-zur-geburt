#!/usr/bin/env python3
"""Create and verify an evidence-bounded Git provenance snapshot.

The snapshot walks *backward as a query* from a named ref to the commit, tree,
blob bytes and visible repository history.  It does not rewrite history or
claim a creation time, right or truth beyond the bound Git objects.

Only the Python standard library and the local ``git`` executable are used.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = "1.0.0"
SNAPSHOT_KIND = "CODE_ZEITWAERTSZURUECK_GIT_PROVENANCE_ENVELOPE"
LICENSE_CLASSIFIER_VERSION = "JURI_THESE_LICENSES_MD_V1_2_0"
CLAIM_CEILING = (
    "EXACT_BYTES_AND_VISIBLE_GIT_HISTORY_WITHIN_THE_BOUND_REPOSITORY_ONLY;"
    "DOES_NOT_PROVE_EARLIER_CREATION_EXCLUSIVE_IDEA_OWNERSHIP_"
    "THIRD_PARTY_RIGHTS_SCIENTIFIC_TRUTH_OR_RETROACTIVE_EFFECT"
)

_CUSTOM_ID = "LicenseRef-Juri-Public-Interest-1.0"
_CUSTOM_BASIS = "LICENSE-JURI-PUBLIC-INTEREST.md"
_HEX_RE = re.compile(r"^[0-9a-f]+$")
_SCP_REMOTE_RE = re.compile(
    r"^(?:(?P<user>[^@/:]+)@)?(?P<host>[^/:]+):(?P<path>.+)$"
)


class ProvenanceError(RuntimeError):
    """Raised when a provenance contract cannot be created or verified."""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    """Return the project's canonical, UTF-8 JSON representation.

    The schema contains no floating-point values.  Rejecting NaN/Infinity and
    writing compact sorted-key JSON makes the digest implementation explicit
    and reproducible across supported Python versions.
    """

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ProvenanceError(f"value is not canonical-JSON compatible: {exc}") from exc
    return encoded.encode("utf-8")


def snapshot_digest(snapshot_without_digest: Mapping[str, Any]) -> str:
    return "sha256:" + sha256_hex(canonical_json_bytes(snapshot_without_digest))


def attach_snapshot_digest(snapshot_without_digest: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(snapshot_without_digest))
    if "snapshotDigest" in result:
        raise ProvenanceError("snapshotDigest must not be present before digesting")
    result["snapshotDigest"] = snapshot_digest(result)
    return result


def _reject_json_constant(token: str) -> None:
    raise ProvenanceError(f"non-finite JSON number is forbidden: {token}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProvenanceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json_bytes(data: bytes) -> Any:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProvenanceError("manifest must be strict UTF-8") from exc
    if text.startswith("\ufeff"):
        raise ProvenanceError("manifest must not contain a UTF-8 BOM")
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except ProvenanceError:
        raise
    except json.JSONDecodeError as exc:
        raise ProvenanceError(f"invalid JSON manifest: {exc}") from exc


def validate_ref(ref: str) -> str:
    if not isinstance(ref, str) or not ref:
        raise ProvenanceError("ref must be a non-empty string")
    if ref.startswith("-") or any(char in ref for char in ("\x00", "\r", "\n")):
        raise ProvenanceError(f"unsafe Git ref expression: {ref!r}")
    return ref


def validate_git_path(relative_path: str) -> str:
    """Validate the exact UTF-8 path carried by a Git tree and JSON manifest."""

    if not isinstance(relative_path, str) or not relative_path:
        raise ProvenanceError("Git path must be a non-empty string")
    if "\x00" in relative_path or "\\" in relative_path:
        raise ProvenanceError(f"unsafe Git path: {relative_path!r}")
    if relative_path.startswith("/") or re.match(r"^[A-Za-z]:", relative_path):
        raise ProvenanceError(f"absolute Git path is forbidden: {relative_path!r}")
    path = PurePosixPath(relative_path)
    if str(path) != relative_path:
        raise ProvenanceError(f"non-canonical Git path: {relative_path!r}")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ProvenanceError(f"traversing Git path is forbidden: {relative_path!r}")
    if any(part.casefold() == ".git" for part in path.parts):
        raise ProvenanceError(f".git path component is forbidden: {relative_path!r}")
    try:
        relative_path.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise ProvenanceError(f"Git path is not valid UTF-8: {relative_path!r}") from exc
    return relative_path


def resolve_repo_file(repo_root: Path, supplied_path: str | os.PathLike[str]) -> Path:
    """Resolve an input/output path and keep it within the bound repository."""

    root = repo_root.resolve(strict=True)
    candidate = Path(supplied_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve(strict=False)
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ProvenanceError(f"path escapes repository root: {candidate}") from exc
    if not relative.parts:
        raise ProvenanceError("a manifest path must name a file, not the repository root")
    if any(part.casefold() == ".git" for part in relative.parts):
        raise ProvenanceError("writing or reading a manifest inside .git is forbidden")
    return candidate


def canonical_repository_url(raw_url: str) -> str:
    """Normalize a public repository locator without retaining credentials."""

    if not isinstance(raw_url, str) or not raw_url.strip():
        raise ProvenanceError("repository URL must be a non-empty string")
    value = raw_url.strip()
    if any(char in value for char in ("\x00", "\r", "\n")):
        raise ProvenanceError("repository URL contains forbidden control characters")

    scp_match = _SCP_REMOTE_RE.fullmatch(value)
    if scp_match and "://" not in value and not re.match(r"^[A-Za-z]:[\\/]", value):
        host = scp_match.group("host").lower()
        repo_path = scp_match.group("path").strip("/")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]
        if not repo_path or ".." in PurePosixPath(repo_path).parts:
            raise ProvenanceError("repository URL contains an unsafe path")
        return f"https://{host}/{repo_path}"

    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https", "ssh"):
        raise ProvenanceError(
            "repository URL must use http, https or ssh, or Git's user@host:path form"
        )
    if parsed.username or parsed.password:
        if parsed.scheme != "ssh" or parsed.username not in (None, "git"):
            raise ProvenanceError(
                "credential-bearing repository URL is forbidden; pass a public canonical URL"
            )
    if parsed.query or parsed.fragment:
        raise ProvenanceError("repository URL query strings and fragments are forbidden")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ProvenanceError("repository URL is missing a host")
    port = f":{parsed.port}" if parsed.port else ""
    netloc = host + port
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path:
        raise ProvenanceError("repository URL is missing a repository path")
    if ".." in PurePosixPath(path).parts:
        raise ProvenanceError("repository URL contains an unsafe path")
    scheme = "https" if parsed.scheme == "ssh" else parsed.scheme.lower()
    return urlunsplit((scheme, netloc, path, "", ""))


def classify_license(relative_path: str) -> dict[str, Any]:
    """Classify one tracked path according to ``LICENSES.md``.

    No generic catch-all is used.  A new path must first be added to the
    repository's license map and this classifier, otherwise snapshot creation
    stops with an explicit error.
    """

    path = validate_git_path(relative_path)

    if path in {"build_pdf.py", "requirements.txt", ".github/workflows/build-pdf.yml"}:
        return {
            "licenseId": "MIT",
            "ruleId": "PROGRAM_CODE_AND_BUILD_CONFIGURATION",
            "basisPath": "LICENSE-CODE",
            "versionScope": "ALL_REPOSITORY_VERSIONS_WHERE_PRESENT",
        }
    if path in {".gitattributes", ".gitignore"}:
        return {
            "licenseId": "MIT",
            "ruleId": "PROGRAM_SUPPORT_CONFIGURATION",
            "basisPath": "LICENSE-CODE",
            "versionScope": "ALL_REPOSITORY_VERSIONS_WHERE_PRESENT",
        }
    if path in {
        "scripts/code_zeitwaertszurueck.py",
        "tests/test_code_zeitwaertszurueck.py",
    }:
        return {
            "licenseId": _CUSTOM_ID,
            "ruleId": "EXACT_PROVENANCE_IMPLEMENTATION_PATH",
            "basisPath": _CUSTOM_BASIS,
            "versionScope": "FROM_FIRST_PUBLIC_COMMIT_OF_THIS_PATH",
        }
    if path == "LICENSE-CODE":
        return {
            "licenseId": "MIT",
            "ruleId": "LICENSE_TEXT_FOR_PROGRAM_CODE",
            "basisPath": "LICENSE-CODE",
            "versionScope": "LICENSE_TEXT",
        }
    if path == "LICENSE-CONTENT":
        return {
            "licenseId": "CC-BY-4.0",
            "ruleId": "HISTORICAL_CONTENT_LICENSE_TEXT",
            "basisPath": "LICENSE-CONTENT",
            "versionScope": "LICENSE_TEXT_AND_HISTORICAL_CONTENT_SCOPE",
        }
    if path == "LICENSE-JURI-PUBLIC-INTEREST.md":
        return {
            "licenseId": "LicenseRef-License-Notice-Copy-Only",
            "ruleId": "CUSTOM_LICENSE_TEXT_COPY_PERMISSION",
            "basisPath": path,
            "versionScope": "UNALTERED_LICENSE_TEXT_ONLY",
        }
    if path == "THIRD_PARTY_NOTICES.md":
        return {
            "licenseId": "LicenseRef-Mixed-Third-Party-Terms",
            "ruleId": "THIRD_PARTY_NOTICES_AND_EMBEDDED_LICENSE_TEXTS",
            "basisPath": path,
            "versionScope": "TERMS_IDENTIFIED_WITHIN_FILE",
        }
    if path == "LICENSE":
        return {
            "licenseId": "LicenseRef-Repository-License-Index",
            "ruleId": "REPOSITORY_LICENSE_INDEX",
            "basisPath": "LICENSES.md",
            "versionScope": "PATH_AND_VERSION_SPECIFIC_REFERENCES_ONLY",
        }
    if path == "LICENSES.md":
        return {
            "licenseId": _CUSTOM_ID,
            "ruleId": "CURRENT_PATH_AND_VERSION_LICENSE_MAP",
            "basisPath": _CUSTOM_BASIS,
            "versionScope": "CURRENT_DISTINGUISHABLE_EDITORIAL_CONTRIBUTION",
        }

    if path == "JURI_THESE_GEBURTSRAUM.md" or (
        path.startswith("docs/") and path.endswith(".md")
    ):
        return {
            "licenseId": _CUSTOM_ID,
            "ruleId": "CURRENT_THESIS_OR_DOCUMENTATION",
            "basisPath": "LICENSES.md",
            "versionScope": "V1_2_0_AND_LATER_DISTINGUISHABLE_NEW_CONTRIBUTIONS",
            "historicalLicenseIds": ["CC-BY-4.0"],
            "historicalOverlap": "V1_0_0_AND_V1_1_0_GRANTS_CONTINUE_FOR_IDENTICAL_OR_OVERLAPPING_MATERIAL",
        }
    if path == "output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf":
        return {
            "licenseId": _CUSTOM_ID,
            "ruleId": "CURRENT_GENERATED_PDF",
            "basisPath": "LICENSES.md",
            "versionScope": "V1_2_0_AND_LATER_DISTINGUISHABLE_NEW_CONTRIBUTIONS",
            "historicalLicenseIds": ["CC-BY-4.0"],
            "historicalOverlap": "V1_0_0_AND_V1_1_0_GRANTS_CONTINUE_FOR_IDENTICAL_OR_OVERLAPPING_MATERIAL",
        }
    if path in {
        "README.md",
        "RELEASE_NOTES.md",
        "PROVENANCE_AND_RIGHTS.md",
        "CITATION.cff",
        "output/pdf/JURI_JANOVSKI_THESE_ZUR_GEBURT.pdf.sha256",
        "SHA256SUMS.txt",
    }:
        return {
            "licenseId": _CUSTOM_ID,
            "ruleId": "CURRENT_RELEASE_METADATA_OR_CHECKSUM",
            "basisPath": "LICENSES.md",
            "versionScope": "FROM_FIRST_PUBLIC_COMMIT_WITH_CURRENT_LICENSE_MAP",
            "historicalOverlap": "ANY_PRIOR_GRANT_CONTINUES_TO_ITS_ORIGINAL_SCOPE",
        }

    return {
        "licenseId": "UNKNOWN",
        "ruleId": "NO_EXACT_LICENSES_MD_RULE",
        "basisPath": "LICENSES.md",
        "versionScope": "UNCLASSIFIED_STOP_REQUIRED",
    }


def _run_git(repo: Path, args: Sequence[str], *, text: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        command = "git " + " ".join(args)
        stderr = completed.stderr.decode("utf-8", "replace").strip()
        raise ProvenanceError(f"{command} failed ({completed.returncode}): {stderr}")
    if text:
        try:
            return completed.stdout.decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise ProvenanceError(f"Git output for {args!r} is not strict UTF-8") from exc
    return completed.stdout


def find_repo_root(cwd: Path | str) -> Path:
    output = _run_git(Path(cwd), ["rev-parse", "--show-toplevel"], text=True)
    assert isinstance(output, str)
    return Path(output.strip()).resolve(strict=True)


def _git_text(repo: Path, args: Sequence[str]) -> str:
    output = _run_git(repo, args, text=True)
    assert isinstance(output, str)
    return output.strip()


def _resolve_object(repo: Path, ref: str, expected_type: str | None = None) -> str:
    safe_ref = validate_ref(ref)
    expression = f"{safe_ref}^{{{expected_type or 'object'}}}"
    return _git_text(repo, ["rev-parse", "--verify", "--end-of-options", expression])


def _parse_tree(raw: bytes) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for record in raw.split(b"\x00"):
        if not record:
            continue
        header, separator, path_bytes = record.partition(b"\t")
        if not separator:
            raise ProvenanceError("invalid NUL-delimited git ls-tree record")
        try:
            mode, object_type, object_id = header.decode("ascii", "strict").split(" ")
            path = path_bytes.decode("utf-8", "strict")
        except (UnicodeDecodeError, ValueError) as exc:
            raise ProvenanceError("invalid or non-UTF-8 git tree record") from exc
        validate_git_path(path)
        if object_type != "blob":
            raise ProvenanceError(
                f"unsupported non-blob tree entry at {path!r}: {object_type}; "
                "submodule/tree provenance requires a separate contract"
            )
        if not _HEX_RE.fullmatch(object_id):
            raise ProvenanceError(f"invalid Git object id for {path!r}: {object_id!r}")
        entries.append(
            {"mode": mode, "type": object_type, "objectId": object_id, "path": path}
        )
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    paths = [entry["path"] for entry in entries]
    if len(paths) != len(set(paths)):
        raise ProvenanceError("duplicate paths in target Git tree")
    return entries


def _parse_nul_history(raw: bytes, field_count: int) -> list[list[str]]:
    if not raw:
        return []
    fields = raw.split(b"\x00")
    if fields[-1] == b"":
        fields.pop()
    if len(fields) % field_count != 0:
        raise ProvenanceError("invalid NUL-delimited Git history output")
    try:
        decoded = [field.decode("utf-8", "strict") for field in fields]
    except UnicodeDecodeError as exc:
        raise ProvenanceError("Git history contains non-UTF-8 metadata") from exc
    return [
        decoded[index : index + field_count]
        for index in range(0, len(decoded), field_count)
    ]


def first_parent_history(repo: Path, commit_id: str) -> list[dict[str, Any]]:
    raw = _run_git(
        repo,
        [
            "log",
            "--first-parent",
            "-z",
            "--format=%H%x00%T%x00%cI%x00%P%x00%s",
            commit_id,
        ],
    )
    assert isinstance(raw, bytes)
    history: list[dict[str, Any]] = []
    for commit, tree, committed_at, parents, subject in _parse_nul_history(raw, 5):
        parent_ids = parents.split(" ") if parents else []
        history.append(
            {
                "commitId": commit,
                "treeId": tree,
                "committedAt": committed_at,
                "parentIds": parent_ids,
                "firstParentId": parent_ids[0] if parent_ids else None,
                "subject": subject,
            }
        )
    if not history or history[0]["commitId"] != commit_id:
        raise ProvenanceError("first-parent history does not begin at the target commit")
    return history


def path_history(repo: Path, commit_id: str, relative_path: str) -> dict[str, Any]:
    validate_git_path(relative_path)
    raw = _run_git(
        repo,
        [
            "log",
            "-z",
            "--format=%H%x00%cI",
            "--diff-filter=AMR",
            commit_id,
            "--",
            relative_path,
        ],
    )
    assert isinstance(raw, bytes)
    records = _parse_nul_history(raw, 2)
    if not records:
        raise ProvenanceError(f"no visible path history found for tracked path {relative_path!r}")

    def as_record(fields: Sequence[str]) -> dict[str, str]:
        return {"commitId": fields[0], "committedAt": fields[1]}

    return {
        "lastVisibleChange": as_record(records[0]),
        "firstVisibleAtCurrentPath": as_record(records[-1]),
        "visibleChangeCount": len(records),
        "coverage": "CURRENT_PATH_HISTORY_WITHOUT_RENAME_INFERENCE",
    }


def compute_file_root(files: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for file_record in files:
        fields = (
            file_record["path"],
            file_record["mode"],
            file_record["type"],
            file_record["objectId"],
            str(file_record["byteLength"]),
            file_record["sha256"],
        )
        for field in fields:
            if not isinstance(field, str) or "\x00" in field or "\n" in field:
                raise ProvenanceError("file-root field must be a newline-free string")
        digest.update(fields[0].encode("utf-8"))
        for field in fields[1:]:
            digest.update(b"\x00")
            digest.update(field.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _origin_url(repo: Path) -> str:
    try:
        return _git_text(repo, ["remote", "get-url", "origin"])
    except ProvenanceError as exc:
        raise ProvenanceError(
            "repository has no readable origin; pass --repository-url explicitly"
        ) from exc


def create_snapshot(
    cwd: Path | str,
    *,
    ref: str = "HEAD",
    repository_url: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    repo = find_repo_root(cwd)
    requested_ref = validate_ref(ref)
    ref_object_id = _resolve_object(repo, requested_ref)
    ref_object_type = _git_text(repo, ["cat-file", "-t", ref_object_id])
    ref_payload = _run_git(repo, ["cat-file", ref_object_type, ref_object_id])
    assert isinstance(ref_payload, bytes)
    commit_id = _resolve_object(repo, requested_ref, "commit")
    tree_id = _git_text(repo, ["rev-parse", f"{commit_id}^{{tree}}"])
    object_format = _git_text(repo, ["rev-parse", "--show-object-format"])
    if object_format not in ("sha1", "sha256"):
        raise ProvenanceError(f"unsupported Git object format: {object_format!r}")

    canonical_url = canonical_repository_url(repository_url or _origin_url(repo))
    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if not isinstance(timestamp, str) or not timestamp or any(
        char in timestamp for char in ("\x00", "\r", "\n")
    ):
        raise ProvenanceError("generatedAt must be a non-empty single-line string")

    raw_tree = _run_git(
        repo, ["ls-tree", "-r", "-z", "--full-tree", "--", commit_id]
    )
    assert isinstance(raw_tree, bytes)
    tree_entries = _parse_tree(raw_tree)
    files: list[dict[str, Any]] = []
    unknown_paths: list[str] = []
    for entry in tree_entries:
        blob = _run_git(repo, ["cat-file", "blob", entry["objectId"]])
        assert isinstance(blob, bytes)
        license_record = classify_license(entry["path"])
        if license_record["licenseId"] == "UNKNOWN":
            unknown_paths.append(entry["path"])
        files.append(
            {
                **entry,
                "byteLength": len(blob),
                "sha256": sha256_hex(blob),
                "contentState": "EXACT_GIT_BLOB_BYTES_HASHED",
                "license": license_record,
                "history": path_history(repo, commit_id, entry["path"]),
            }
        )
    if unknown_paths:
        raise ProvenanceError(
            "unclassified license paths (update LICENSES.md and classifier first): "
            + ", ".join(unknown_paths)
        )

    by_path = {record["path"]: record for record in files}
    license_map = by_path.get("LICENSES.md")
    custom_license = by_path.get(_CUSTOM_BASIS)
    if license_map is None or custom_license is None:
        raise ProvenanceError(
            "target tree must contain LICENSES.md and LICENSE-JURI-PUBLIC-INTEREST.md"
        )

    is_shallow = _git_text(repo, ["rev-parse", "--is-shallow-repository"]) == "true"
    snapshot_without_digest: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "snapshotKind": SNAPSHOT_KIND,
        "canonicalization": "UTF8_SORTED_KEYS_COMPACT_JSON_NO_NAN",
        "snapshotDigestAlgorithm": "sha256(canonical JSON excluding snapshotDigest)",
        "generatedAt": timestamp,
        "subject": {
            "repositoryUrl": canonical_url,
            "requestedRef": requested_ref,
            "refObjectId": ref_object_id,
            "refObjectType": ref_object_type,
            "refObjectPayloadByteLength": len(ref_payload),
            "refObjectPayloadSha256": sha256_hex(ref_payload),
            "commitId": commit_id,
            "treeId": tree_id,
            "gitObjectHash": object_format,
        },
        "backwardTrace": {
            "direction": "TARGET_COMMIT_TO_FIRST_VISIBLE_FIRST_PARENT_ROOT",
            "repositoryHistoryState": "SHALLOW" if is_shallow else "FULL_LOCAL_OBJECT_GRAPH",
            "commits": first_parent_history(repo, commit_id),
            "semantics": "QUERY_ORDER_ONLY_NO_RETROACTIVE_CAUSATION_RIGHTS_CHANGE_OR_HISTORY_REWRITE",
        },
        "fileSet": {
            "source": "git ls-tree -r -z --full-tree <commit>",
            "sort": "BYTEWISE_UTF8_PATH_ASCENDING",
            "count": len(files),
            "canonicalRootAlgorithm": (
                "sha256(path_utf8 NUL mode NUL type NUL objectId NUL byteLength "
                "NUL sha256 LF)"
            ),
            "sha256Root": compute_file_root(files),
            "files": files,
        },
        "boundPolicy": {
            "licenseClassifierVersion": LICENSE_CLASSIFIER_VERSION,
            "licenseMapPath": "LICENSES.md",
            "licenseMapSha256": license_map["sha256"],
            "customLicensePath": _CUSTOM_BASIS,
            "customLicenseSha256": custom_license["sha256"],
        },
        "claimCeiling": CLAIM_CEILING,
    }
    return attach_snapshot_digest(snapshot_without_digest)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ProvenanceError(f"{label} must be a JSON object")
    return value


def _validate_stored_manifest(stored: Mapping[str, Any]) -> None:
    if stored.get("schemaVersion") != SCHEMA_VERSION:
        raise ProvenanceError(f"unsupported schemaVersion: {stored.get('schemaVersion')!r}")
    if stored.get("snapshotKind") != SNAPSHOT_KIND:
        raise ProvenanceError("unexpected snapshotKind")
    if stored.get("claimCeiling") != CLAIM_CEILING:
        raise ProvenanceError("claim ceiling mismatch")
    subject = _require_mapping(stored.get("subject"), "subject")
    validate_ref(subject.get("requestedRef"))
    canonical_url = canonical_repository_url(subject.get("repositoryUrl"))
    if canonical_url != subject.get("repositoryUrl"):
        raise ProvenanceError("repositoryUrl is not in canonical form")

    file_set = _require_mapping(stored.get("fileSet"), "fileSet")
    files = file_set.get("files")
    if not isinstance(files, list):
        raise ProvenanceError("fileSet.files must be an array")
    if file_set.get("count") != len(files):
        raise ProvenanceError("fileSet.count does not match file array length")
    paths: list[str] = []
    for index, raw_file in enumerate(files):
        file_record = _require_mapping(raw_file, f"fileSet.files[{index}]")
        path = validate_git_path(file_record.get("path"))
        paths.append(path)
        expected_license = classify_license(path)
        if file_record.get("license") != expected_license:
            raise ProvenanceError(f"license classification mismatch for {path!r}")
        if file_record.get("type") != "blob":
            raise ProvenanceError(f"non-blob file record is forbidden for {path!r}")
        if not isinstance(file_record.get("byteLength"), int) or file_record["byteLength"] < 0:
            raise ProvenanceError(f"invalid byteLength for {path!r}")
        for key in ("objectId", "sha256"):
            value = file_record.get(key)
            if not isinstance(value, str) or not _HEX_RE.fullmatch(value):
                raise ProvenanceError(f"invalid {key} for {path!r}")
    expected_order = sorted(paths, key=lambda path: path.encode("utf-8"))
    if paths != expected_order:
        raise ProvenanceError("file paths are not in canonical bytewise UTF-8 order")
    if len(paths) != len(set(paths)):
        raise ProvenanceError("manifest contains duplicate file paths")
    expected_root = compute_file_root(files)
    if file_set.get("sha256Root") != expected_root:
        raise ProvenanceError("stored file root does not match stored file records")


def verify_snapshot(cwd: Path | str, *, manifest: str | os.PathLike[str]) -> dict[str, Any]:
    repo = find_repo_root(cwd)
    manifest_path = resolve_repo_file(repo, manifest)
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise ProvenanceError(f"cannot read manifest {manifest_path}: {exc}") from exc
    stored = parse_json_bytes(manifest_bytes)
    stored_map = _require_mapping(stored, "manifest")
    _validate_stored_manifest(stored_map)

    stored_digest = stored_map.get("snapshotDigest")
    if not isinstance(stored_digest, str):
        raise ProvenanceError("snapshotDigest must be a string")
    without_digest = dict(stored_map)
    without_digest.pop("snapshotDigest", None)
    computed_digest = snapshot_digest(without_digest)
    if stored_digest != computed_digest:
        raise ProvenanceError(
            f"snapshot digest mismatch: stored {stored_digest!r}, computed {computed_digest!r}"
        )

    subject = _require_mapping(stored_map["subject"], "subject")
    rebuilt = create_snapshot(
        repo,
        ref=subject["requestedRef"],
        repository_url=subject["repositoryUrl"],
        generated_at=stored_map.get("generatedAt"),
    )
    if canonical_json_bytes(rebuilt) != canonical_json_bytes(stored_map):
        raise ProvenanceError(
            "manifest is internally digested but does not match the currently resolved Git objects"
        )
    return {
        "state": "VERIFIED",
        "manifest": str(manifest_path),
        "commitId": subject["commitId"],
        "treeId": subject["treeId"],
        "refObjectId": subject["refObjectId"],
        "fileCount": stored_map["fileSet"]["count"],
        "fileRoot": stored_map["fileSet"]["sha256Root"],
        "snapshotDigest": stored_digest,
        "claimCeiling": stored_map["claimCeiling"],
    }


def write_snapshot(path: Path, snapshot: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(snapshot) + b"\n"
    try:
        path.write_bytes(payload)
    except OSError as exc:
        raise ProvenanceError(f"cannot write manifest {path}: {exc}") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or verify a CODE ZEITWÄRTSZURÜCK Git provenance snapshot."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="create a canonical JSON snapshot")
    create_parser.add_argument("--ref", default="HEAD", help="Git ref/tag/commit to bind")
    create_parser.add_argument("--output", required=True, help="manifest path inside repository")
    create_parser.add_argument(
        "--repository-url",
        help="public canonical repository URL; defaults to origin after credential checks",
    )
    create_parser.add_argument(
        "--generated-at",
        help="receipt timestamp; defaults to current UTC time and is included in the digest",
    )

    verify_parser = subparsers.add_parser("verify", help="verify a stored snapshot")
    verify_parser.add_argument("--manifest", required=True, help="manifest path inside repository")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        repo = find_repo_root(Path.cwd())
        if args.command == "create":
            output = resolve_repo_file(repo, args.output)
            snapshot = create_snapshot(
                repo,
                ref=args.ref,
                repository_url=args.repository_url,
                generated_at=args.generated_at,
            )
            write_snapshot(output, snapshot)
            summary = {
                "state": "CREATED",
                "output": str(output),
                "commitId": snapshot["subject"]["commitId"],
                "treeId": snapshot["subject"]["treeId"],
                "refObjectId": snapshot["subject"]["refObjectId"],
                "fileCount": snapshot["fileSet"]["count"],
                "fileRoot": snapshot["fileSet"]["sha256Root"],
                "snapshotDigest": snapshot["snapshotDigest"],
                "claimCeiling": snapshot["claimCeiling"],
            }
        else:
            summary = verify_snapshot(repo, manifest=args.manifest)
    except ProvenanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
