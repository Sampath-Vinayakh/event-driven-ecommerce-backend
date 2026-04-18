from django.urls import path
from .views import create_checkout_session

urlpatterns = [
    path("session/", create_checkout_session, name="create-checkout-session"),
]