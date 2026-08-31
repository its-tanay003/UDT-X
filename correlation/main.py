"""UDT-X Correlation Service CLI Entrypoint."""

import argparse
import logging
import os
import sys

from correlation.worker import CorrelationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.correlation.main")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UDT-X Incident Correlation & Evidence Graph Service"
    )
    parser.add_argument(
        "--kafka-brokers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
    )
    parser.add_argument(
        "--input-topic",
        default=os.getenv("INPUT_TOPIC", "raw-alerts"),
    )
    parser.add_argument(
        "--output-topic",
        default=os.getenv("OUTPUT_TOPIC", "correlated-incidents"),
    )
    parser.add_argument(
        "--group-id",
        default=os.getenv("KAFKA_GROUP_ID", "udtx-correlation-service"),
    )
    parser.add_argument(
        "--neo4j-uri",
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    )
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=int(os.getenv("CORRELATION_WINDOW_MINUTES", "30")),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info("Starting UDT-X Incident Correlation & Evidence Graph Service")
    logger.info("  Input Topic     : %s", args.input_topic)
    logger.info("  Output Topic    : %s", args.output_topic)
    logger.info("  Window Minutes  : %d", args.window_minutes)
    logger.info("  Neo4j URI       : %s", args.neo4j_uri)

    service = CorrelationService(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        group_id=args.group_id,
        neo4j_uri=args.neo4j_uri,
        window_minutes=args.window_minutes,
        dry_run=args.dry_run,
    )

    try:
        service.start_consumer()
    except KeyboardInterrupt:
        logger.info("Shutting down correlation service.")
        sys.exit(0)


if __name__ == "__main__":
    main()
