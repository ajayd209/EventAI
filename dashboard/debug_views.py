from django.http import JsonResponse
from django.conf import settings
import allauth

def debug_google_config(request):
    return JsonResponse({
        'client_id': settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APPS', [{}])[0].get('client_id', 'MISSING'),
        'site_id': getattr(settings, 'SITE_ID', 'MISSING'),
        'allauth_version': allauth.__version__,
        'google_provider_config': settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
    })
