"""UDT-X Data Exfiltration Detection Engine CLI Entrypoint."""

import argparse
import logging
import os
import sys

from engines.exfiltration.worker import ExfiltrationEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.engines.exfiltration.main")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UDT-X Data Exfiltration Detection Engine"
    )
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
        default=os.getenv("KAFKA_GROUP_ID", "udtx-exfiltration-engine"),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=float(os.getenv("CONFIDENCE_THRESHOLD", "0.50")),
        help="Detection confidence threshold for alert emission (0.0-1.0)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info("Starting UDT-X Data Exfiltration Detection Engine")
    logger.info("  Input Topic  : %s", args.input_topic)
    logger.info("  Output Topic : %s", args.output_topic)
    logger.info("  Threshold    : %.2f", args.threshold)

    engine = ExfiltrationEngine(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        group_id=args.group_id,
        confidence_threshold=args.threshold,
        dry_run=args.dry_run,
    )

    try:
        engine.start_consumer()
    except KeyboardInterrupt:
        logger.info("Shutting down Exfiltration engine.")
        sys.exit(0)


if __name__ == "__main__":
    main()
