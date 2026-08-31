"""UDT-X DDoS Detection Engine CLI Entrypoint."""

import argparse
import logging
import os
import sys

from engines.ddos.worker import DDoSEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.engines.ddos.main")


def main() -> None:
    parser = argparse.ArgumentParser(description="UDT-X DDoS Detection Engine")
    parser.add_argument(
        "--kafka-brokers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
    )
    parser.add_argument(
        "--input-topic",
        default=os.getenv("INPUT_TOPIC", "feature-vectors"),
    )
    parser.add_argument(
        "--output-topic",
        default=os.getenv("OUTPUT_TOPIC", "raw-alerts"),
    )
    parser.add_argument(
        "--group-id",
        default=os.getenv("KAFKA_GROUP_ID", "udtx-ddos-engine"),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=float(os.getenv("CONFIDENCE_THRESHOLD", "0.50")),
        help="DDoS confidence threshold for alert emission (0.0-1.0)",
    )
    parser.add_argument(
        "--ewma-alpha",
        type=float,
        default=float(os.getenv("EWMA_ALPHA", "0.2")),
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=int(os.getenv("WARMUP_SAMPLES", "5")),
    )
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    logger.info("Starting UDT-X DDoS Detection Engine")
    logger.info("  Input Topic  : %s", args.input_topic)
    logger.info("  Output Topic : %s", args.output_topic)
    logger.info("  Threshold    : %.2f", args.threshold)

    engine = DDoSEngine(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        group_id=args.group_id,
        confidence_threshold=args.threshold,
        ewma_alpha=args.ewma_alpha,
        warmup_samples=args.warmup,
        dry_run=args.dry_run,
    )

    try:
        engine.start_consumer()
    except KeyboardInterrupt:
        logger.info("Shutting down DDoS engine.")
        sys.exit(0)


if __name__ == "__main__":
    main()
