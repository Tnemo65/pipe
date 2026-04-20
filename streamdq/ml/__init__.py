"""
StreamDQ ML Module

Machine learning components for adaptive context learning:
- Threshold prediction (XGBoost)
- Duplicate confidence scoring (LightGBM)
- Anomaly detection (Isolation Forest + Autoencoder)
"""

from .threshold_predictor import MLThresholdPredictor

__all__ = ["MLThresholdPredictor"]
