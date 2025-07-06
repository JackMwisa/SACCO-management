import os
import logging

from django.utils.translation import gettext as _
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache

import google.generativeai as genai

# Logger setup
logger = logging.getLogger(__name__)

# Initialize Gemini with API key from .env or Django settings
GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
genai.configure(api_key=GEMINI_API_KEY)

# Static page views
def faq(request):
    return render(request, "faq/faq.html", {
        "breadcrumb": {"parent": "FAQ", "child": "FAQ"}
    })

def tutorial(request):
    return render(request, "support/tutorial.html", {
        "breadcrumb": {"parent": "Support", "child": "Tutorial"}
    })


@csrf_exempt
def chatbot(request):
    """
    Gemini-powered chatbot with basic multilingual support and rate limiting.
    """
    if request.method == "POST":
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'unknown'))
        cache_key = f"chatbot_{ip}"
        request_count = cache.get(cache_key, 0)

        if request_count >= 20:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return JsonResponse({
                'reply': _("Please wait a moment before sending more messages."),
                'status': 'rate_limited'
            }, status=429)

        cache.set(cache_key, request_count + 1, timeout=60)

        message = request.POST.get("message", "").strip()
        lang = request.POST.get("lang", "en")

        if not message:
            return JsonResponse({
                'reply': _("Please type a message to continue."),
                'status': 'empty_message'
            }, status=400)

        if not GEMINI_API_KEY:
            logger.error("Gemini API key missing.")
            return JsonResponse({
                'reply': _("System configuration error. Please contact support."),
                'status': 'error'
            }, status=500)

        # Multilingual system prompt
        system_prompts = {
            'en': "You are GEMS AI, Gem SACCO's helpful virtual assistant. Provide concise, professional answers about banking services.",
            'lg': "Oli GEMS AI, omuyambi wa Gem SACCO. Weereza obuyambi obumanyirivu ku by'ensimbi.",
            'fr': "Vous êtes GEMS AI, l'assistant virtuel de Gem SACCO. Fournissez des réponses utiles sur les services bancaires.",
            'sw': "Wewe ni GEMS AI, msaidizi wa Gem SACCO. Toa majibu mafupi kuhusu huduma za kifedha."
        }

        try:
            model = genai.GenerativeModel("models/gemini-1.5-flash")

            response = model.generate_content(
                f"{system_prompts.get(lang, system_prompts['en'])}\n\nUser: {message}",
                generation_config={"temperature": 0.7},
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )

            reply = response.text
            logger.debug(f"Gemini response: {reply[:100]}...")
            return JsonResponse({'reply': reply, 'status': 'success'})

        except Exception as e:
            logger.error(f"Gemini error: {str(e)}", exc_info=True)
            error_msg = _("GEMS AI is temporarily unavailable. Please try again later.")
            if "quota" in str(e).lower():
                error_msg = _("Daily usage quota exceeded. Please try again tomorrow.")
            elif "safety" in str(e).lower():
                error_msg = _("Your message was blocked by content filters. Please rephrase.")

            return JsonResponse({'reply': error_msg, 'status': 'error'}, status=500)

    # GET request: Render chat interface
    return render(request, "support/chatbot.html", {
        'default_lang': request.COOKIES.get('gemsai_lang', 'en')
    })

