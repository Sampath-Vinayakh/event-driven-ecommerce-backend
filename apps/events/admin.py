from django.contrib import admin

from apps.events.models import OutboxEvent, ProcessedEvent


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_type",
        "aggregate_type",
        "aggregate_id",
        "status",
        "created_at",
        "published_at",
    )
    list_filter = (
        "status",
        "event_type",
        "aggregate_type",
        "created_at",
    )
    search_fields = (
        "id",
        "event_type",
        "aggregate_type",
        "aggregate_id",
        "error_message",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "published_at",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Event Info",
            {
                "fields": (
                    "id",
                    "event_type",
                    "aggregate_type",
                    "aggregate_id",
                    "status",
                )
            },
        ),
        (
            "Payload",
            {
                "fields": (
                    "payload",
                    "metadata",
                    "error_message",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "published_at",
                )
            },
        ),
    )


@admin.register(ProcessedEvent)
class ProcessedEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_id",
        "consumer_name",
        "processed_at",
    )
    list_filter = (
        "consumer_name",
        "processed_at",
    )
    search_fields = (
        "id",
        "event_id",
        "consumer_name",
    )
    readonly_fields = (
        "id",
        "processed_at",
    )
    ordering = ("-processed_at",)