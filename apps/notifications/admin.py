from django.contrib import admin

from apps.notifications.models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_email",
        "type",
        "status",
        "event_id",
        "created_at",
        "sent_at",
    )
    list_filter = (
        "type",
        "status",
        "created_at",
        "sent_at",
    )
    search_fields = (
        "id",
        "user_email",
        "event_id",
        "subject",
        "body",
        "error_message",
    )
    readonly_fields = (
        "id",
        "created_at",
        "sent_at",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Notification Info",
            {
                "fields": (
                    "id",
                    "user_email",
                    "type",
                    "status",
                    "event_id",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "subject",
                    "body",
                )
            },
        ),
        (
            "Delivery",
            {
                "fields": (
                    "error_message",
                    "created_at",
                    "sent_at",
                )
            },
        ),
    )