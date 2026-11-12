import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import reddit_connector as rc


class ConnectorTests(unittest.TestCase):
    def test_load_communities(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.json"
            path.write_text(json.dumps({"communities": ["UKPersonalFinance"]}), encoding="utf-8")
            self.assertEqual(rc.load_communities(path), ["UKPersonalFinance"])

    def test_fetch_new_posts_maps_public_fields(self):
        session = Mock()

        token_response = Mock()
        token_response.raise_for_status.return_value = None
        token_response.json.return_value = {"access_token": "token"}
        session.post.return_value = token_response

        listing_response = Mock()
        listing_response.raise_for_status.return_value = None
        listing_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "name": "t3_example",
                            "subreddit": "ExampleCommunity",
                            "title": "Example title",
                            "selftext": "Example body",
                            "created_utc": 1760000000,
                            "permalink": "/r/ExampleCommunity/comments/example/post/",
                            "num_comments": 12,
                            "score": 34,
                        }
                    }
                ]
            }
        }
        session.get.return_value = listing_response

        import os
        old = {k: os.environ.get(k) for k in [
            "SCOUT_REDDIT_CLIENT_ID",
            "SCOUT_REDDIT_CLIENT_SECRET",
            "SCOUT_REDDIT_USER_AGENT",
        ]}
        try:
            os.environ["SCOUT_REDDIT_CLIENT_ID"] = "id"
            os.environ["SCOUT_REDDIT_CLIENT_SECRET"] = "secret"
            os.environ["SCOUT_REDDIT_USER_AGENT"] = "test-agent"
            posts = rc.fetch_new_posts(["ExampleCommunity"], limit=5, session=session)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].source_native_id, "t3_example")
        self.assertEqual(posts[0].community, "r/ExampleCommunity")
        self.assertEqual(posts[0].engagement["comments"], 12)
        self.assertEqual(posts[0].engagement["score"], 34)
        self.assertTrue(posts[0].url.startswith("https://www.reddit.com/"))


if __name__ == "__main__":
    unittest.main()
