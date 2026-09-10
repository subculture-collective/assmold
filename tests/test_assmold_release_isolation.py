"""Fork publication must not target the upstream project's image namespace."""

from pathlib import Path

import yaml


def test_inherited_release_entrypoints_are_upstream_only():
    root = Path(__file__).resolve().parents[1]
    for filename, job in (("release.yaml", "verify"), ("backend-role-release.yaml", "backend-image")):
        workflow = yaml.safe_load((root / ".gitea" / "workflows" / filename).read_text())
        assert workflow["jobs"][job]["if"] == "gitea.repository == 'subculture-collective/hasanara'"


def test_image_publication_requires_the_guarded_verification():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".gitea/workflows/release.yaml").read_text())
    images = workflow["jobs"]["images"]
    assert "verify" in images["needs"]
    assert "needs.verify.result == 'success'" in images["if"]
