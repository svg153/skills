from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-planning-runtime-evidence.py"
TEMPLATE = ROOT / "plugins" / "planning" / "evidence" / "TEMPLATE.json"

spec = importlib.util.spec_from_file_location("planning_runtime_evidence", SCRIPT)
runtime_evidence = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runtime_evidence)


class PlanningRuntimeEvidenceTests(unittest.TestCase):
    def template(self) -> dict:
        return json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def verified_auth(self, provider: dict) -> None:
        provider["authentication"] = {
            "status": "verified",
            "method": "client-managed OAuth",
            "credentialStoredInPlugin": False,
            "evidence": "OAuth completed in the client and provider reconnect succeeded.",
        }

    def verified_read(self, provider: dict, ref: str) -> None:
        provider["readToolCall"] = {
            "status": "verified",
            "operation": "read planning record",
            "resourceType": "issue",
            "resourceRef": ref,
            "resultSummary": "Returned the expected non-sensitive planning state.",
            "evidence": "Client tool result matched the known test record.",
        }

    def test_template_is_valid_but_does_not_claim_runtime_evidence(self) -> None:
        document = self.template()
        runtime_evidence.validate_document(document, "template")
        self.assertEqual(document["mode"], "template")
        self.assertEqual(document["endToEnd"]["status"], "pending")

    def test_secret_like_pat_is_rejected(self) -> None:
        document = self.template()
        document["notes"] = "accidentally pasted github_pat_abcdefghijklmnopqrstuvwxyz1234567890"
        with self.assertRaisesRegex(runtime_evidence.EvidenceError, "secret-like value"):
            runtime_evidence.validate_document(document, "secret")

    def test_secret_bearing_key_is_rejected_even_with_redacted_value(self) -> None:
        document = self.template()
        document["providers"]["github"]["access_token"] = "REDACTED"
        with self.assertRaisesRegex(runtime_evidence.EvidenceError, "secret-like key"):
            runtime_evidence.validate_document(document, "secret-key")

    def test_verified_read_requires_verified_authentication(self) -> None:
        document = self.template()
        document["mode"] = "evidence"
        self.verified_read(document["providers"]["github"], "svg153/skills#36")
        with self.assertRaisesRegex(runtime_evidence.EvidenceError, "cannot be verified before authentication"):
            runtime_evidence.validate_document(document, "read-without-auth")

    def test_verified_mutation_requires_explicit_user_intent(self) -> None:
        document = self.template()
        document["mode"] = "evidence"
        github = document["providers"]["github"]
        self.verified_auth(github)
        github["mutation"] = {
            "status": "verified",
            "explicitUserIntent": False,
            "operation": "create test issue",
            "returnedId": "#999",
            "resultSummary": "Provider returned a test issue ID.",
            "evidence": "Sanitized provider response retained the returned ID.",
        }
        document["providers"]["atlassian"]["authentication"] = {
            "status": "blocked",
            "method": "client-managed OAuth 2.1",
            "credentialStoredInPlugin": False,
            "evidence": "OAuth connection is not available in this environment.",
        }
        with self.assertRaisesRegex(runtime_evidence.EvidenceError, "explicitUserIntent must be true"):
            runtime_evidence.validate_document(document, "mutation-without-intent")

    def test_end_to_end_requires_both_reads_and_a_real_mutation(self) -> None:
        document = self.template()
        document["mode"] = "evidence"
        github = document["providers"]["github"]
        atlassian = document["providers"]["atlassian"]
        self.verified_auth(github)
        self.verified_auth(atlassian)
        self.verified_read(github, "svg153/skills#36")
        document["endToEnd"] = {
            "status": "verified",
            "singleSourceOfTruthVerified": True,
            "crossProviderLinkVerified": True,
            "resultSummary": "Cross-provider scenario completed.",
            "evidence": "Sanitized scenario transcript retained.",
        }
        with self.assertRaisesRegex(runtime_evidence.EvidenceError, "verified Atlassian read"):
            runtime_evidence.validate_document(document, "incomplete-e2e")

    def test_complete_sanitized_evidence_is_valid(self) -> None:
        document = deepcopy(self.template())
        document["mode"] = "evidence"
        github = document["providers"]["github"]
        atlassian = document["providers"]["atlassian"]
        self.verified_auth(github)
        self.verified_auth(atlassian)
        self.verified_read(github, "svg153/skills#36")
        self.verified_read(atlassian, "TEST-123")
        github["mutation"] = {
            "status": "verified",
            "explicitUserIntent": True,
            "operation": "create linked implementation issue",
            "returnedId": "#1001",
            "resultSummary": "Created a non-sensitive test implementation issue.",
            "evidence": "Provider returned the public test issue identifier.",
        }
        atlassian["mutation"] = {
            "status": "not-applicable",
            "explicitUserIntent": False,
            "operation": "",
            "returnedId": "",
            "resultSummary": "",
            "evidence": "",
        }
        document["endToEnd"] = {
            "status": "verified",
            "singleSourceOfTruthVerified": True,
            "crossProviderLinkVerified": True,
            "resultSummary": "Jira planning record remained authoritative while a linked GitHub implementation child was created.",
            "evidence": "Sanitized provider identifiers and cross-link result were retained.",
        }
        runtime_evidence.validate_document(document, "complete")


if __name__ == "__main__":
    unittest.main()
