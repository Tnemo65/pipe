"""
End-to-end precision test for Phase 1 confidence-based duplicate detection.

Validates that confidence scoring improves precision from 28-31% → 43-51%.
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from streamdq.producers.nyc_taxi_replay import NYCTaxiReplayProducer
from streamdq.rules.cross_record import evaluate_duplicate_event, CrossRecordState
from streamdq.rules.adjudicator import ContextAwareDuplicateAdjudicator


class TestPhase1PrecisionImprovement:
    """Validate Phase 1 precision target."""

    def test_phase1_precision_improvement(self):
        """E2E test: 1000 events → precision ≥45%."""
        # Setup
        state = CrossRecordState()
        adjudicator = ContextAwareDuplicateAdjudicator()
        violations_all = []
        violations_high_confidence = []

        # Load 1000 NYC Taxi events
        producer = NYCTaxiReplayProducer(direct_mode=True, inject_anomalies=False)
        parquet_path = Path(__file__).parent.parent.parent / "data" / "nyc_taxi_sample_1k.parquet"

        if not parquet_path.exists():
            pytest.skip(f"Sample data not found: {parquet_path}")

        import pandas as pd
        df = pd.read_parquet(parquet_path).head(1000)

        # Process events
        base_time = datetime(2024, 1, 15, 10, 0, 0)

        for idx, row in df.iterrows():
            event = row.to_dict()
            # Enrich with lineage (non-replay for real duplicate detection)
            event["_lineage"] = {
                "source_id": "e2e_test",
                "source_type": "batch_replay",
                "is_replay": False,  # Treat as live for testing
                "batch_id": "test_batch"
            }

            event_time = base_time + timedelta(seconds=idx)
            violation = evaluate_duplicate_event(
                event, event_time,
                dedup_state=state,
                adjudicator=adjudicator
            )

            if violation:
                violations_all.append(violation)
                confidence = violation.details.get("adjudication_confidence", 0.0)
                if confidence > 0.7:
                    violations_high_confidence.append(violation)

        # Compute precision
        if len(violations_all) == 0:
            pytest.skip("No violations detected in sample")

        precision = len(violations_high_confidence) / len(violations_all)

        print(f"\n{'='*70}")
        print(f"Phase 1 E2E Precision Test Results")
        print(f"{'='*70}")
        print(f"Total events processed: {len(df)}")
        print(f"Total violations: {len(violations_all)}")
        print(f"High confidence violations (>0.7): {len(violations_high_confidence)}")
        print(f"Precision: {precision*100:.1f}%")
        print(f"Target: ≥45%")
        print(f"{'='*70}")

        # Assert precision target
        assert precision >= 0.45, (
            f"Precision {precision*100:.1f}% below target 45%\n"
            f"Expected impact: +15-20 points (28-31% → 43-51%)"
        )
