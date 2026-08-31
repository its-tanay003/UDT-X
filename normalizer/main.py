"""UDT-X Flow Normalizer Service Entrypoint."""

import argparse
import logging
import sys

from normalizer.worker import FlowNormalizerWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("udtx.normalizer")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UDT-X Telemetry Normalization & DLQ Service."
    )
    parser.add_argument(
        "--kafka-brokers",
        type=str,
        default="localhost:19092",
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--input-topic",
        type=str,
        default="raw-events",
        help="Input raw events topic",
    )
    parser.add_argument(
        "--output-topic",
        type=str,
        default="flow-events",
        help="Output canonical FlowEvents topic",
    )
    parser.add_argument(
        "--dlq-topic",
        type=str,
        default="raw-events-dlq",
        help="Dead letter queue topic for failed records",
    )
    parser.add_argument(
        "--group-id",
        type=str,
        default="udtx-flow-normalizer-group",
        help="Kafka consumer group ID",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without connecting to live Kafka",
    )

    args = parser.parse_args()

    logger.info("Initializing UDT-X Flow Normalizer...")
    worker = FlowNormalizerWorker(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        dlq_topic=args.dlq_topic,
        group_id=args.group_id,
        dry_run=args.dry_run,
    )

    try:
        worker.run_consumer_loop()
    except Exception as exc:
        logger.error("Normalizer service crashed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
