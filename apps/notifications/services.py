import logging

from django.core.mail import send_mail
from django.utils import timezone

from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def create_and_send_email(
        *,
        user_email: str,
        notification_type: str,
        subject: str,
        body: str,
        event_id: str,
    ) -> Notification:
        notification = Notification.objects.create(
            user_email=user_email,
            type=notification_type,
            subject=subject,
            body=body,
            event_id=event_id,
            status=Notification.Status.PENDING,
        )

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,
                recipient_list=[user_email],
                fail_silently=False,
            )

            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()
            notification.error_message = ""
            notification.save(update_fields=["status", "sent_at", "error_message"])

            logger.info(
                "Notification email sent successfully",
                extra={
                    "notification_id": str(notification.id),
                    "event_id": str(event_id),
                    "user_email": user_email,
                    "type": notification_type,
                },
            )
            return notification

        except Exception as exc:
            notification.status = Notification.Status.FAILED
            notification.error_message = str(exc)
            notification.save(update_fields=["status", "error_message"])

            logger.exception(
                "Failed to send notification email",
                extra={
                    "notification_id": str(notification.id),
                    "event_id": str(event_id),
                },
            )
            raise