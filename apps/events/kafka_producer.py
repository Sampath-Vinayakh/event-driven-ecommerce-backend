import json
import logging

from confluent_kafka import Producer
from django.conf import settings

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self):
        self.producer = Producer(
            {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "client.id": "ecommerce-backend",
            }
        )

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(
                "Kafka message delivery failed",
                extra={
                    "topic": msg.topic() if msg else None,
                    "partition": msg.partition() if msg else None,
                    "offset": msg.offset() if msg else None,
                    "error": str(err),
                },
            )
        else:
            logger.info(
                "Kafka message delivered",
                extra={
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                    "key": msg.key().decode("utf-8") if msg.key() else None,
                },
            )

    def publish(self, *, topic: str, key: str, value: dict):
        self.producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=json.dumps(value).encode("utf-8"),
            callback=self._delivery_report,
        )
        self.producer.poll(0)

    def flush(self):
        self.producer.flush()