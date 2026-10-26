"""Tests for photo analysis error reporting in report_issue."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.report_issue import _analyze_image_with_vision, VISION_MODEL, OLLAMA_URL


class _MissingModelResponse:
    status_code = 404

    def json(self):
        return {"error": f"model '{VISION_MODEL}' not found"}

    text = '{"error": "model not found"}'
    headers = {}


class _Endpoint404Response:
    status_code = 404

    def json(self):
        raise ValueError("not json")

    text = "404 page not found"
    headers = {}


class _SuccessResponse:
    status_code = 200
    headers = {}

    def json(self):
        return {
            "model": VISION_MODEL,
            "created_at": "2026-01-01T00:00:00Z",
            "message": {
                "role": "assistant",
                "content": '{"category": "Pothole", "description": "Large pothole on Main St", "priority": "High", "reason": "Road hazard"}',
            },
            "done": True,
        }

    text = "{}"


class TestAnalyzeImageWithVision(unittest.TestCase):
    def test_missing_model_surfaces_ollama_error(self):
        with patch("pages.report_issue.requests.post", return_value=_MissingModelResponse()):
            result = _analyze_image_with_vision(b"fake-bytes", "photo.jpg")
        self.assertIn("error", result)
        self.assertIn(VISION_MODEL, result["error"])
        self.assertIn("not found", result["error"].lower())

    def test_genuine_endpoint_404_falls_back_to_http_404(self):
        with patch("pages.report_issue.requests.post", return_value=_Endpoint404Response()):
            result = _analyze_image_with_vision(b"fake-bytes", "photo.jpg")
        self.assertEqual(result.get("error"), "http_404")

    def test_request_uses_chat_endpoint_and_vision_model(self):
        captured = {}

        def fake_post(url, json=None, **kwargs):
            captured["url"] = url
            captured["payload"] = json
            return _MissingModelResponse()

        with patch("pages.report_issue.requests.post", side_effect=fake_post):
            _analyze_image_with_vision(b"fake-bytes", "photo.jpg")
        self.assertEqual(captured["url"], OLLAMA_URL)
        self.assertEqual(captured["payload"]["model"], VISION_MODEL)
        self.assertEqual(captured["payload"]["messages"][0]["images"], [__import__("base64").b64encode(b"fake-bytes").decode("utf-8")])

    def test_success_response_shape_parsed(self):
        with patch("pages.report_issue.requests.post", return_value=_SuccessResponse()):
            result = _analyze_image_with_vision(b"fake-bytes", "photo.jpg")
        self.assertNotIn("error", result)
        self.assertEqual(result["category"], "Pothole")
        self.assertEqual(result["description"], "Large pothole on Main St")
        self.assertEqual(result["priority"], "High")
        self.assertEqual(result["reason"], "Road hazard")


if __name__ == "__main__":
    unittest.main()
