import unittest
from pathlib import Path

from campaigns.bundle import load_campaign_template


class CampaignBundleTests(unittest.TestCase):
    def test_sample_template(self):
        root = Path(__file__).parent
        rendered = load_campaign_template(root, root / "campaign.json")
        self.assertIn("{{customer_name}}", rendered)
        self.assertIn("{{region}}", rendered)


if __name__ == "__main__":
    unittest.main()
