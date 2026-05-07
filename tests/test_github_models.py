import json
import unittest
from unittest.mock import patch

from coastal_fishing_forecast.github_models import (
    GitHubModelsError,
    generate_github_models_explanation_text,
    generate_github_models_plan_text,
)


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class GitHubModelsTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_missing_token_fails_clearly(self) -> None:
        with self.assertRaises(GitHubModelsError):
            generate_github_models_plan_text({"hero": {"score": 50}})

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=True)
    def test_valid_response_parses_json_content(self) -> None:
        payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"primary_action_text": "Try the morning beach signal."}),
                    }
                }
            ]
        }
        with patch("coastal_fishing_forecast.github_models.urlopen", return_value=_FakeResponse(payload)):
            result = generate_github_models_plan_text({"hero": {"score": 50}})

        self.assertEqual(result["primary_action_text"], "Try the morning beach signal.")

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=True)
    def test_non_json_content_fails(self) -> None:
        payload = {"choices": [{"message": {"content": "not-json"}}]}
        with patch("coastal_fishing_forecast.github_models.urlopen", return_value=_FakeResponse(payload)):
            with self.assertRaises(GitHubModelsError):
                generate_github_models_plan_text({"hero": {"score": 50}})

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=True)
    def test_explanation_response_parses_json_content(self) -> None:
        payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "why_this_window": [
                                    "Dawn has the best local setup.",
                                    "Moving water supports the time signal.",
                                ],
                                "score_story": "The local score stayed above the raw time signal.",
                            }
                        ),
                    }
                }
            ]
        }
        with patch("coastal_fishing_forecast.github_models.urlopen", return_value=_FakeResponse(payload)):
            result = generate_github_models_explanation_text({"best_window": {"score": 70}})

        self.assertEqual(len(result["why_this_window"]), 2)
        self.assertIn("local score", result["score_story"])


if __name__ == "__main__":
    unittest.main()
