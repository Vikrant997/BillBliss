# middleware.py

from django.utils import translation

class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = request.session.get('django_language', request.COOKIES.get('selected_language', ''))
        if language in ['sw', 'en']:
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()
        return self.get_response(request)
