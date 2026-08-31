"""UDT-X Feature Extraction Service CLI Entrypoint."""

import argparse
import logging
import os
import sys

from features.worker import FeatureExtractionWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.features.main")


def main() -> None:
    """Run the Feature Extraction worker CLI service."""
    parser = argparse.ArgumentParser(
        description="UDT-X Real-Time Feature Extraction Engine"
    )
    parser.add_argument(
        "--kafka-brokers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
        help="Kafka/Redpanda broker addresses",
    )
    parser.add_argument(
        "--input-topic",
        default=os.getenv("INPUT_TOPIC", "flow-events"),
        help="Kafka topic to consume canonical FlowEvents from",
    )
    parser.add_argument(
        "--output-topic",
        default=os.getenv("OUTPUT_TOPIC", "feature-vectors"),
        help="Kafka topic to publish FeatureVector messages to",
    )
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        help="Redis URL for sliding window state",
    )
    parser.add_argument(
        "--group-id",
        default=os.getenv("KAFKA_GROUP_ID", "udtx-feature-engine-group"),
        help="Kafka consumer group ID",
    )
    parser.add_argument(
        "--window-seconds",
        type=int,
        default=int(os.getenv("WINDOW_SECONDS", "60")),
        help="Sliding time window duration in seconds",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without connecting to live Kafka brokers",
    )

    args = parser.parse_args()

    logger.info("Starting UDT-X Feature Extraction Engine")
    logger.info("  Brokers      : %s", args.kafka_brokers)
    logger.info("  Input Topic  : %s", args.input_topic)
    logger.info("  Output Topic : %s", args.output_topic)
    logger.info("  Redis URL    : %s", args.redis_url)
    logger.info("  Window (sec) : %d", args.window_seconds)

    worker = FeatureExtractionWorker(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        redis_url=args.redis_url,
        group_id=args.group_id,
        window_seconds=args.window_seconds,
        dry_run=args.dry_run,
    )

    try:
        worker.start_consumer()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal; shutting down gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
