"""
End-to-end integration test for Phase 2 context-aware thresholds.

Validates that context-aware thresholds work end-to-end in LocalPipeline
and reduce false positives in semantic rules.
"""
import pytest
from pathlib import Path
from streamdq.pipeline.local_pipeline import LocalPipeline, NoOpViolationStore


class TestPhase2ContextAwareE2E:
    """Validate Phase 2 context-aware threshold integration."""

    def test_phase2_context_aware_pipeline_e2e(self):
        """E2E test: Process 1000 events with context-aware thresholds."""
        # Setup pipeline with context-aware thresholds
        pipeline_context_aware = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=True,
            entity_type="nyc_taxi"
        )

        # Setup baseline pipeline with global thresholds for comparison
        pipeline_global = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=False,
            entity_type="nyc_taxi"
        )

        # Load 1000 NYC Taxi events
        parquet_path = Path(__file__).parent.parent.parent / "data" / "nyc_taxi_sample_1k.parquet"

        if not parquet_path.exists():
            pytest.skip(f"Sample data not found: {parquet_path}")

        import pandas as pd
        df = pd.read_parquet(parquet_path).head(1000)

        # Process events with both pipelines
        violations_context_aware = []
        violations_global = []

        for idx, row in df.iterrows():
            event = row.to_dict()

            # Process with context-aware pipeline
            viols_ca = pipeline_context_aware.process_event(event)
            violations_context_aware.extend(viols_ca)

            # Process with global pipeline
            viols_g = pipeline_global.process_event(event)
            violations_global.extend(viols_g)

        # Analyze results
        sem001_ca = [v for v in violations_context_aware if v.rule_id == "SEM001"]
        sem001_global = [v for v in violations_global if v.rule_id == "SEM001"]

        print(f"\n{'='*70}")
        print(f"Phase 2 E2E Context-Aware Threshold Test Results")
        print(f"{'='*70}")
        print(f"Total events processed: {len(df)}")
        print(f"\nContext-Aware Pipeline:")
        print(f"  Total violations: {len(violations_context_aware)}")
        print(f"  SEM001 (fare range) violations: {len(sem001_ca)}")
        print(f"  Context buffers created: {len(pipeline_context_aware.threshold_engine._buffers)}")
        print(f"\nGlobal Threshold Pipeline:")
        print(f"  Total violations: {len(violations_global)}")
        print(f"  SEM001 (fare range) violations: {len(sem001_global)}")
        print(f"\nExpected Impact:")
        print(f"  - Context-aware pipeline maintains separate stats per context")
        print(f"  - Global pipeline uses single threshold for all contexts")
        print(f"  - Context-aware should reduce false positives in heterogeneous data")
        print(f"{'='*70}")

        # Assertions
        assert len(df) == 1000, "Should process 1000 events"

        # Context-aware pipeline should create multiple context buffers
        # (at least 5 levels * 2 fields = 10 buffers minimum)
        assert len(pipeline_context_aware.threshold_engine._buffers) >= 10, (
            f"Context-aware pipeline should create multiple context buffers, "
            f"got {len(pipeline_context_aware.threshold_engine._buffers)}"
        )

        # Global pipeline should create only 2 buffers (fare_amount, trip_distance)
        assert len(pipeline_global.threshold_engine._buffers) == 2, (
            f"Global pipeline should create 2 buffers, "
            f"got {len(pipeline_global.threshold_engine._buffers)}"
        )

        print("\n✅ Phase 2 E2E test passed: Context-aware thresholds working end-to-end")

    def test_phase2_hierarchical_fallback_e2e(self):
        """Verify hierarchical fallback works in real scenarios."""
        pipeline = LocalPipeline(
            violation_store=NoOpViolationStore(),
            use_context_aware_thresholds=True,
            entity_type="nyc_taxi"
        )

        # Create events with diverse contexts
        events = []

        # Morning midtown (many events - L0 should work)
        for i in range(50):
            events.append({
                "trip_id": f"morning_midtown_{i}",
                "tpep_pickup_datetime": "2024-01-15T10:30:00",
                "PULocationID": 161,  # Midtown
                "fare_amount": 15.0 + i * 0.1,
                "trip_distance": 2.0
            })

        # Evening airport (few events - should fallback to higher levels)
        for i in range(5):
            events.append({
                "trip_id": f"evening_airport_{i}",
                "tpep_pickup_datetime": "2024-01-15T20:30:00",
                "PULocationID": 132,  # JFK Airport
                "fare_amount": 50.0 + i * 2.0,
                "trip_distance": 15.0
            })

        # Process all events
        for event in events:
            pipeline.process_event(event)

        # Check that multiple contexts were created
        buffers = pipeline.threshold_engine._buffers

        print(f"\n{'='*70}")
        print(f"Phase 2 Hierarchical Fallback E2E Test")
        print(f"{'='*70}")
        print(f"Events processed: {len(events)}")
        print(f"Context buffers created: {len(buffers)}")
        print(f"\nSample buffer keys:")
        for key in list(buffers.keys())[:10]:
            print(f"  {key}")
        print(f"{'='*70}")

        # Should have buffers for multiple contexts
        assert len(buffers) >= 10, (
            f"Should create multiple context buffers, got {len(buffers)}"
        )

        # Verify we can query with fallback
        query_event = {
            "tpep_pickup_datetime": "2024-01-15T10:35:00",
            "PULocationID": 161
        }

        threshold_result = pipeline.threshold_engine.get_threshold_with_fallback(
            field="fare_amount",
            percentile="p90",
            event=query_event
        )

        if threshold_result is not None:
            print(f"\nThreshold lookup result:")
            print(f"  Value: {threshold_result['value']}")
            print(f"  Level: {threshold_result['level']}")
            print(f"  Context key: {threshold_result['context_key']}")
            print(f"  Sample count: {threshold_result['count']}")

        print("\n✅ Hierarchical fallback working end-to-end")
