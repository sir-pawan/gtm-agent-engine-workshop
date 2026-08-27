import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile, get_prospect


SENSITIVE_KEYS = {"tax_id", "card_on_file", "date_of_birth", "credit_check_ref"}


def nested_keys(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(nested_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(nested_keys(item) for item in value))
    return set()


class ProspectRedactionTest(unittest.TestCase):
    def setUp(self):
        data_service._PROFILES.clear()

    def test_redact_prospect_is_non_mutating(self):
        record = {"name": "Ada", "billing_qualification": {"tax_id": "123"}}

        redacted = data_service.redact_prospect(record)

        self.assertEqual(redacted, {"name": "Ada"})
        self.assertIn("billing_qualification", record)

    def test_prospect_tools_do_not_return_sensitive_fields(self):
        profile = build_prospect_profile.invoke({"prospect_id": "LEAD-39002"})
        contact = get_prospect.invoke({"prospect_id": "LEAD-39002"})

        self.assertTrue(SENSITIVE_KEYS.isdisjoint(nested_keys(profile)))
        self.assertTrue(SENSITIVE_KEYS.isdisjoint(nested_keys(contact)))


if __name__ == "__main__":
    unittest.main()
