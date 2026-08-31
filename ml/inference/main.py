"""UDT-X ML Streaming Inference CLI Entrypoint."""

import argparse
import logging
import os
import sys

from ml.inference.worker import MLInferenceEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("udtx.ml.inference.main")


def main() -> None:
    parser = argparse.ArgumentParser(description="UDT-X ML Streaming Inference Engine")
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
        default=os.getenv("OUTPUT_TOPIC", "ml-scores"),
    )
    parser.add_argument(
        "--group-id",
        default=os.getenv("KAFKA_GROUP_ID", "udtx-ml-inference-engine"),
    )
    parser.add_argument(
        "--registry-dir",
        default=os.getenv("ML_REGISTRY_DIR", "ml/registry"),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info("Starting UDT-X ML Inference Engine")
    logger.info("  Input Topic  : %s", args.input_topic)
    logger.info("  Output Topic : %s", args.output_topic)

    engine = MLInferenceEngine(
        bootstrap_servers=args.kafka_brokers,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        group_id=args.group_id,
        registry_dir=args.registry_dir,
        dry_run=args.dry_run,
    )

    try:
        engine.start_consumer()
    except KeyboardInterrupt:
        logger.info("Shutting down ML inference engine.")
        sys.exit(0)


if __name__ == "__main__":
    main()
