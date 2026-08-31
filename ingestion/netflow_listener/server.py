"""UDT-X NetFlow / IPFIX UDP Listener Service."""

import argparse
import asyncio
import logging

from ingestion.kafka_producer import UDTXKafkaProducer
from ingestion.netflow_listener.parser import decode_netflow_packet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("udtx.netflow_listener")


class NetflowUDPProtocol(asyncio.DatagramProtocol):
    """Async UDP Protocol handler for incoming NetFlow & IPFIX packets."""

    def __init__(self, producer: UDTXKafkaProducer) -> None:
        self.producer = producer
        self.packets_received = 0
        self.flows_published = 0

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport
        logger.info("NetFlow UDP listener bound and waiting for packets...")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.packets_received += 1
        count = 0
        for flow_event in decode_netflow_packet(data):
            event_dict = flow_event.model_dump(mode="json")
            self.producer.send_event(event_dict, key=flow_event.flow_id)
            count += 1
            self.flows_published += 1

        if self.packets_received % 1000 == 0:
            logger.info(
                "Processed %d UDP packets, published %d flows",
                self.packets_received,
                self.flows_published,
            )

    def error_received(self, exc: Exception) -> None:
        logger.error("UDP socket error: %s", exc)


async def run_server(host: str, port: int, producer: UDTXKafkaProducer) -> None:
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: NetflowUDPProtocol(producer),
        local_addr=(host, port),
    )
    logger.info("UDT-X NetFlow listener active on udp://%s:%d", host, port)

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        transport.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UDT-X NetFlow v5/v9 and IPFIX UDP Ingestion Listener."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="UDP bind address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=2055,
        help="UDP bind port (default: 2055, IPFIX: 4739)",
    )
    parser.add_argument(
        "--kafka-brokers",
        type=str,
        default="localhost:19092",
        help="Kafka broker address",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="raw-events",
        help="Target Kafka topic",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run without publishing to Kafka",
    )

    args = parser.parse_args()

    producer = UDTXKafkaProducer(
        bootstrap_servers=args.kafka_brokers,
        topic=args.topic,
        client_id="udtx-netflow-listener",
        dry_run=args.dry_run,
    )

    try:
        asyncio.run(run_server(args.host, args.port, producer))
    except KeyboardInterrupt:
        logger.info("Shutting down NetFlow listener...")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
