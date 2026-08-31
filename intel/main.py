"""UDT-X Threat Intelligence CLI Entrypoint."""

import argparse
import logging
import os
import sys

from intel.worker import IntelEnrichmentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.intel.main")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UDT-X Threat Intelligence & MITRE Mapping Service"
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
        default=os.getenv("OUTPUT_TOPIC", "enriched-alerts"),
    )
    parser.add_argument(
        "--group-id",
        default=os.getenv("KAFKA_GROUP_ID", "udtx-intel-enrichment-service"),
    )
    parser.add_argument(
        "--mitre-map-path",
        default=os.getenv("MITRE_MAP_PATH", "intel/mitre_map.json"),
    )
    parser.add_argument(
        "--ioc-feed-path",
        default=os.getenv("IOC_FEED_PATH", "intel/data/sample_iocs.json"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info("Starting UDT-X Threat Intelligence & MITRE Mapping Service")
    logger.info("  Input Topic    : %s", args.input_topic)
    logger.info("  Output Topic   : %s", args.output_topic)
    logger.info("  MITRE Map Path : %s", args.mitre_map_path)

    service = IntelEnrichmentService(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        group_id=args.group_id,
        mitre_map_path=args.mitre_map_path,
        ioc_feed_path=args.ioc_feed_path,
        dry_run=args.dry_run,
    )

    try:
        service.start_consumer()
    except KeyboardInterrupt:
        logger.info("Shutting down intel enrichment service.")
        sys.exit(0)


if __name__ == "__main__":
    main()
