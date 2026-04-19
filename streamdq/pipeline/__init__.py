# Import individual modules directly, not through __init__
# to avoid pyspark dependency at module load time
from streamdq.pipeline.local_pipeline import LocalPipeline

__all__ = ["LocalPipeline"]
# SparkPipeline imported directly when needed:
# from streamdq.pipeline.spark_pipeline import StreamDQPipeline
