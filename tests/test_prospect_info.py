import copy
import json
import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from gtm_agent import data_service
from gtm_agent import gtm_agent


class FakeScoringLLM:
    def invoke(self, messages):
        offering = json.loads(messages[1]["content"].split("Offering:\n", 1)[1].split("\n\nProspect profile:\n", 1)[0])
        profile = json.loads(messages[1]["content"].split("\n\nProspect profile:\n", 1)[1])
        missing = [technology for technology in offering["required_tech_stack"] if technology not in profile["tech_stack"]]
        return gtm_agent.ProspectScore(
            score=100 - len(missing),
            justification=f"Missing: {', '.join(missing)}",
            rubric_breakdown={"revenue_fit": 100, "tech_stack_match": 100 - len(missing), "segment_fit": 100},
        )


class ProspectInfoTest(unittest.TestCase):
    def test_update_persists_and_rescoring_uses_new_technology(self):
        prospect_id = "LEAD-39002"
        original_record = copy.deepcopy(data_service.PROSPECTS[prospect_id])
        original_profile = data_service._PROFILES.pop(prospect_id, None)
        original_llm = gtm_agent._scoring_llm
        try:
            profile = gtm_agent.build_prospect_profile.invoke({"prospect_id": prospect_id})["prospect_profile"]
            result = data_service.update_prospect_info(prospect_id, "Terraform")

            self.assertTrue(result["updated"])
            self.assertIn("Terraform", data_service.fetch_tech_stack(prospect_id))
            self.assertNotIn(prospect_id, data_service._PROFILES)

            gtm_agent._scoring_llm = FakeScoringLLM()
            score = gtm_agent.score_prospect.invoke({"prospect_profile": profile, "offering": data_service.get_offering("OFFER-10004")})

            self.assertNotIn("Terraform", score["justification"])
        finally:
            data_service.PROSPECTS[prospect_id] = original_record
            data_service._PROFILES.pop(prospect_id, None)
            if original_profile is not None:
                data_service._PROFILES[prospect_id] = original_profile
            gtm_agent._scoring_llm = original_llm


if __name__ == "__main__":
    unittest.main()
