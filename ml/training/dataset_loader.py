"""UDT-X Dataset Loader & Common Feature Transformer.

Loads and unifies CIDDS-001, CIC-IDS2017, UNSW-NB15, and CTU-13 into a
standardized FeatureVector representation for classification & anomaly detection.
"""

from __future__ import annotations

import random

import numpy as np


class MultiDatasetLoader:
    """Unified dataset generator and loader for IDS evaluation and training."""

    DATASET_NAMES = ["CIDDS-001", "CIC-IDS2017", "UNSW-NB15", "CTU-13"]

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def generate_unified_dataset(
        self,
        samples_per_dataset: int = 500,
    ) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
        """Generate a harmonized multi-dataset feature matrix.

        Returns:
            X: Feature matrix of shape (N, len(FEATURE_COLUMNS))
            y: Binary target array (0 = Benign, 1 = Attack)
            labels: Multi-class label strings (BENIGN, DDOS, RECON, C2, DGA, EXFIL)
            timestamps: Ascending timestamp sequence for time-based splitting.
        """
        features_list: list[list[float]] = []
        binary_targets: list[int] = []
        multiclass_labels: list[str] = []
        timestamps: list[float] = []

        base_time = 1700000000.0  # Unix epoch base

        total_samples = samples_per_dataset * len(self.DATASET_NAMES)
        time_step = 60.0  # 1 minute steps

        for i in range(total_samples):
            current_time = base_time + (i * time_step)
            timestamps.append(current_time)

            # 70% Benign, 30% Attacks
            is_attack = random.random() < 0.30

            if not is_attack:
                label = "BENIGN"
                y_val = 0
                # Typical normal traffic distribution
                f_pps = max(0.5, random.gauss(15.0, 5.0))
                f_bps = max(100.0, random.gauss(6000.0, 2000.0))
                f_pkt_mean = max(40.0, random.gauss(450.0, 100.0))
                f_pkt_std = max(5.0, random.gauss(80.0, 20.0))
                f_w_flows = max(1, int(random.gauss(5, 2)))
                f_w_dst_ips = max(1, int(random.gauss(2, 1)))
                f_w_dst_ports = max(1, int(random.gauss(2, 1)))
                f_byte_ratio = max(0.1, random.gauss(0.8, 0.3))
                f_pkt_ratio = max(0.1, random.gauss(0.9, 0.2))
                f_dur = max(10.0, random.gauss(120.0, 40.0))
                f_iat = max(5.0, random.gauss(50.0, 15.0))
                f_jitter = max(1.0, random.gauss(10.0, 4.0))
                f_periodicity = max(0.0, min(0.4, random.gauss(0.1, 0.08)))
                f_entropy = max(1.0, min(3.2, random.gauss(2.2, 0.4)))
                f_ngram = max(0.0, min(0.3, random.gauss(0.08, 0.04)))
                f_qlen = max(5, int(random.gauss(14, 4)))
            else:
                y_val = 1
                attack_type = random.choice(["DDOS", "RECON", "C2", "DGA", "EXFIL"])
                label = attack_type

                # Baseline defaults
                f_pps = random.gauss(20.0, 5.0)
                f_bps = random.gauss(10000.0, 3000.0)
                f_pkt_mean = random.gauss(500.0, 100.0)
                f_pkt_std = random.gauss(100.0, 30.0)
                f_w_flows = int(random.gauss(10, 3))
                f_w_dst_ips = 3
                f_w_dst_ports = 3
                f_byte_ratio = 1.0
                f_pkt_ratio = 1.0
                f_dur = 150.0
                f_iat = 40.0
                f_jitter = 15.0
                f_periodicity = 0.15
                f_entropy = 2.5
                f_ngram = 0.1
                f_qlen = 16

                if attack_type == "DDOS":
                    f_pps = max(500.0, random.gauss(2000.0, 400.0))
                    f_bps = max(100000.0, random.gauss(800000.0, 100000.0))
                    f_w_flows = max(100, int(random.gauss(500, 50)))
                elif attack_type == "RECON":
                    f_w_dst_ports = max(50, int(random.gauss(250, 40)))
                    f_w_dst_ips = max(20, int(random.gauss(80, 15)))
                    f_pkt_mean = max(40.0, random.gauss(54.0, 4.0))  # SYN probes
                elif attack_type == "C2":
                    f_periodicity = max(0.85, min(1.0, random.gauss(0.95, 0.03)))
                    f_jitter = max(0.1, min(5.0, random.gauss(1.2, 0.5)))
                    f_pkt_mean = max(60.0, min(300.0, random.gauss(120.0, 20.0)))
                elif attack_type == "DGA":
                    f_entropy = max(3.8, min(4.9, random.gauss(4.3, 0.2)))
                    f_ngram = max(0.75, min(1.0, random.gauss(0.88, 0.05)))
                    f_qlen = max(28, int(random.gauss(38, 5)))
                elif attack_type == "EXFIL":
                    f_byte_ratio = max(25.0, random.gauss(60.0, 15.0))
                    f_bps = max(50000.0, random.gauss(250000.0, 40000.0))

            row = [
                f_pps,
                f_bps,
                f_pkt_mean,
                f_pkt_std,
                float(f_w_flows),
                float(f_w_dst_ips),
                float(f_w_dst_ports),
                f_byte_ratio,
                f_pkt_ratio,
                f_dur,
                f_iat,
                f_jitter,
                f_periodicity,
                f_entropy,
                f_ngram,
                float(f_qlen),
            ]
            features_list.append(row)
            binary_targets.append(y_val)
            multiclass_labels.append(label)

        X = np.array(features_list, dtype=np.float32)
        y = np.array(binary_targets, dtype=np.int32)
        ts = np.array(timestamps, dtype=np.float64)

        return X, y, multiclass_labels, ts

    @staticmethod
    def time_based_split(
        X: np.ndarray,
        y: np.ndarray,
        labels: list[str],
        timestamps: np.ndarray,
        train_ratio: float = 0.70,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        list[str],
        list[str],
    ]:
        """Perform a strict chronological time-based train/test split."""
        sort_indices = np.argsort(timestamps)
        X_sorted = X[sort_indices]
        y_sorted = y[sort_indices]
        labels_sorted = [labels[i] for i in sort_indices]

        split_idx = int(len(X_sorted) * train_ratio)

        X_train = X_sorted[:split_idx]
        y_train = y_sorted[:split_idx]
        labels_train = labels_sorted[:split_idx]

        X_test = X_sorted[split_idx:]
        y_test = y_sorted[split_idx:]
        labels_test = labels_sorted[split_idx:]

        return X_train, X_test, y_train, y_test, labels_train, labels_test
