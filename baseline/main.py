"""UDT-X Behavioral Baseline Service CLI Entrypoint."""

import argparse
import logging
import os
import sys

from baseline.worker import BaselineService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.baseline.main")


def main() -> None:
    parser = argparse.ArgumentParser(description="UDT-X Behavioral Baseline Service")
    parser.add_argument(
        "--kafka-brokers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
    )
    parser.add_argument(
        "--input-topic",
        default=os.getenv("INPUT_TOPIC", "flow-events"),
    )
    parser.add_argument(
        "--group-id",
        default=os.getenv("KAFKA_GROUP_ID", "udtx-baseline-service"),
    )
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://udtx_user:udtx_password@localhost:5432/udtx",
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    redis_client = None
    if not args.dry_run:
        try:
            import redis  # type: ignore

            redis_client = redis.Redis.from_url(args.redis_url, decode_responses=True)
            redis_client.ping()
            logger.info("Connected baseline service to Redis at %s", args.redis_url)
        except Exception as exc:
            logger.warning("Redis connection failed, using in-memory store: %s", exc)

    logger.info("Starting UDT-X Behavioral Baseline Service")
    logger.info("  Input Topic : %s", args.input_topic)
    logger.info("  Group ID    : %s", args.group_id)

    service = BaselineService(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        group_id=args.group_id,
        redis_client=redis_client,
        database_url=args.database_url,
        dry_run=args.dry_run,
    )

    try:
        service.start_consumer()
    except KeyboardInterrupt:
        logger.info("Shutting down baseline service.")
        sys.exit(0)


if __name__ == "__main__":
    main()
