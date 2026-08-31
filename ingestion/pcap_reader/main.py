"""UDT-X PCAP Ingestion Service Entrypoint."""

import argparse
import logging
import sys
import time
from pathlib import Path

from ingestion.kafka_producer import UDTXKafkaProducer
from ingestion.pcap_reader.pcap_extractor import extract_flows_from_pcap

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("udtx.pcap_reader")


def process_pcap_file(pcap_path: Path, producer: UDTXKafkaProducer) -> tuple[int, int]:
    """Extract flows from a single PCAP and publish to Kafka."""
    logger.info("Processing PCAP file: %s", pcap_path)
    count = 0
    total_bytes = 0

    try:
        for flow_event in extract_flows_from_pcap(pcap_path):
            event_dict = flow_event.model_dump(mode="json")
            producer.send_event(event_dict, key=flow_event.flow_id)
            count += 1
            total_bytes += flow_event.bytes
        producer.flush()
        logger.info(
            "Successfully processed %s: extracted %d flows (%d bytes)",
            pcap_path.name,
            count,
            total_bytes,
        )
    except Exception as exc:
        logger.error("Error processing %s: %s", pcap_path, exc)
    return count, total_bytes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UDT-X PCAP File Ingestion Engine to Kafka."
    )
    parser.add_argument("--pcap", type=str, help="Path to single .pcap / .pcapng file")
    parser.add_argument(
        "--watch-dir", type=str, help="Directory to watch for new PCAPs"
    )
    parser.add_argument(
        "--kafka-brokers",
        type=str,
        default="localhost:19092",
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="raw-events",
        help="Target Kafka topic for raw records",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and print without sending to Kafka",
    )

    args = parser.parse_args()

    producer = UDTXKafkaProducer(
        bootstrap_servers=args.kafka_brokers,
        topic=args.topic,
        client_id="udtx-pcap-reader",
        dry_run=args.dry_run,
    )

    if args.pcap:
        pcap_file = Path(args.pcap)
        if not pcap_file.exists():
            logger.error("File does not exist: %s", pcap_file)
            sys.exit(1)
        process_pcap_file(pcap_file, producer)

    elif args.watch_dir:
        watch_path = Path(args.watch_dir)
        watch_path.mkdir(parents=True, exist_ok=True)
        logger.info("Watching directory %s for .pcap files...", watch_path)
        processed: set[Path] = set()

        try:
            while True:
                for pcap_file in watch_path.glob("*.pcap*"):
                    if pcap_file not in processed:
                        process_pcap_file(pcap_file, producer)
                        processed.add(pcap_file)
                time.sleep(2)
        except KeyboardInterrupt:
            logger.info("Stopping directory watcher...")
    else:
        logger.error("Please specify either --pcap or --watch-dir")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
