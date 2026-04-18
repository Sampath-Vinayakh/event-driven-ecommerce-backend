from django.contrib import admin
from apps.payments.models import Payment,PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "provider",
        "status",
        "amount",
        "currency",
        "provider_order_id",
        "provider_payment_id",
        "paid_at",
        "created_at",
    )
    list_filter = (
        "status",
        "provider",
        "currency",
        "created_at",
        "paid_at",
        "failed_at",
        "cancelled_at",
    )
    search_fields = (
        "id",
        "order__id",
        "order__user__email",
        "provider_order_id",
        "provider_payment_id",
        "idempotency_key",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "paid_at",
        "failed_at",
        "cancelled_at",
    )
    ordering = ("-created_at",)
    list_select_related = ("order", "order__user")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "order",
                    "provider",
                    "status",
                )
            },
        ),
        (
            "Amount Details",
            {
                "fields": (
                    "amount",
                    "currency",
                )
            },
        ),
        (
            "Provider References",
            {
                "fields": (
                    "provider_order_id",
                    "provider_payment_id",
                    "checkout_url",
                    "idempotency_key",
                )
            },
        ),
        (
            "Failure Details",
            {
                "fields": (
                    "failure_code",
                    "failure_message",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "metadata",
                    "raw_provider_response",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "paid_at",
                    "failed_at",
                    "cancelled_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "provider",
        "event_type",
        "processed",
        "processed_at",
        "created_at",
    )
    list_filter = (
        "provider",
        "event_type",
        "processed",
        "created_at",
    )
    search_fields = (
        "event_id",
        "event_type",
        "signature",
    )
    readonly_fields = (
        "id",
        "provider",
        "event_id",
        "event_type",
        "signature",
        "payload",
        "processed",
        "processed_at",
        "created_at",
    )
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        (
            "Webhook Event Info",
            {
                "fields": (
                    "id",
                    "provider",
                    "event_id",
                    "event_type",
                    "signature",
                )
            },
        ),
        (
            "Processing Status",
            {
                "fields": (
                    "processed",
                    "processed_at",
                    "created_at",
                )
            },
        ),
        (
            "Payload",
            {
                "fields": ("payload",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False