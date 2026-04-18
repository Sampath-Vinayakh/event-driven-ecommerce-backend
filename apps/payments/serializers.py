from rest_framework import serializers
from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "provider",
            "status",
            "amount",
            "currency",
            "provider_payment_id",
            "provider_session_id",
            "checkout_url",
            "failure_code",
            "failure_message",
            "paid_at",
            "failed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields