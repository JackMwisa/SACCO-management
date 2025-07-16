from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.core.cache import cache

class SupportViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.chatbot_url = reverse("support:chatbot")
        self.faq_url = reverse("support:faq")
        self.tutorial_url = reverse("support:tutorial")

    def test_faq_view(self):
        response = self.client.get(self.faq_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "faq/faq.html")

    def test_tutorial_view(self):
        response = self.client.get(self.tutorial_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "support/tutorial.html")

    def test_chatbot_get(self):
        response = self.client.get(self.chatbot_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "support/chatbot.html")

    def test_chatbot_post_no_message(self):
        response = self.client.post(self.chatbot_url, {"message": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("empty_message", response.json()["status"])

    def test_chatbot_post_success(self):
        with patch("support.views.genai.GenerativeModel.generate_content") as mock_generate:
            mock_generate.return_value.text = "Hello! How can I help you?"

            response = self.client.post(self.chatbot_url, {
                "message": "What is a SACCO?",
                "lang": "en"
            })

            self.assertEqual(response.status_code, 200)
            self.assertIn("reply", response.json())
            self.assertEqual(response.json()["status"], "success")

    def test_chatbot_multilingual_prompt_luganda(self):
        with patch("support.views.genai.GenerativeModel.generate_content") as mock_generate:
            mock_generate.return_value.text = "Wangi, GEMS AI ali wano okuyamba."

            response = self.client.post(self.chatbot_url, {
                "message": "Ki SACCO?",
                "lang": "lg"
            })

            self.assertEqual(response.status_code, 200)
            self.assertIn("reply", response.json())
            self.assertEqual(response.json()["status"], "success")

    def test_chatbot_rate_limiting(self):
        ip = "127.0.0.1"
        cache_key = f"chatbot_{ip}"
        cache.set(cache_key, 20, timeout=60)  # Simulate 20 prior requests

        response = self.client.post(self.chatbot_url, {
            "message": "Hi",
        }, REMOTE_ADDR=ip)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["status"], "rate_limited")
