"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

import django
from channels.routing import ProtocolTypeRouter, URLRouter

from channels.auth import AuthMiddlewareStack
import transcript.urls as trans_urls


django.setup()



application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            trans_urls.websocket_urlpatterns
        )
    )
})

# import os
# from django.core.asgi import get_asgi_application

# # Set the Django settings module FIRST
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# # Initialize Django BEFORE any other imports
# django_asgi_app = get_asgi_application()

# # NOW you can import other modules
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import transcript.urls as trans_urls

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             trans_urls.websocket_urlpatterns
#         )
#     ),
# })