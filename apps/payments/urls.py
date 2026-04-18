from django.urls import path
from apps.payments import views

urlpatterns = [
    path("<uuid:order_id>/session/", views.create_payment_session, name="create-payment-session"),
    path("razorpay/webhook/", views.razorpay_webhook, name="payment-webhook"),
]