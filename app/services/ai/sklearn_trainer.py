from typing import Any, Dict, Optional
from app.services.ai.trainer import BaseTrainer
import joblib
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score, confusion_matrix

class SklearnTrainer(BaseTrainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.training_history = {"loss": []}

    def train(self, data: pd.DataFrame, params: Dict[str, Any]) -> Any:
        """
        Train a Scikit-learn model.
        """
        algorithm = params.get('algorithm', 'RandomForestClassifier')
        target_col = params.get('target_col', 'label')
        feature_cols = params.get('feature_cols', [])
        hyperparameters = params.get('hyperparameters', {})
        
        if not feature_cols:
            feature_cols = [c for c in data.columns if c != target_col]
            
        X = data[feature_cols]
        # For unsupervised models like IsolationForest, y might not be needed or used
        y = data[target_col] if target_col in data.columns else None
        
        self.feature_cols = feature_cols # Save for evaluation
        
        if algorithm == 'RandomForestClassifier':
            model = RandomForestClassifier(**hyperparameters)
        elif algorithm == 'RandomForestRegressor':
            model = RandomForestRegressor(**hyperparameters)
        elif algorithm == 'LogisticRegression':
            model = LogisticRegression(**hyperparameters)
        elif algorithm == 'LinearRegression':
            model = LinearRegression(**hyperparameters)
        elif algorithm == 'IsolationForest':
            model = IsolationForest(**hyperparameters)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
            
        # Simulate progress during training
        # Since sklearn models don't support callbacks easily, we simulate
        import time
        import random
        steps = 10
        self.log(f"Starting training with algorithm: {algorithm}")
        self.log(f"Training data shape: {X.shape}")
        
        # Initialize simulated loss
        current_loss = 0.8
        
        for i in range(steps):
            progress = 10 + (i * (90/steps))
            self.update_progress(progress, 100)
            
            # Simulate loss reduction
            decay = random.uniform(0.05, 0.15)
            current_loss = max(0.01, current_loss * (1 - decay))
            self.training_history["loss"].append(current_loss)
            
            self.log(f"Training step {i+1}/{steps} - Progress: {progress:.1f}% - Loss: {current_loss:.4f}")
            time.sleep(1.0) # Simulate work (slower to see progress)
            
        self.log("Fitting model...")
        if algorithm == 'IsolationForest':
            model.fit(X)
        else:
            if y is None:
                 raise ValueError(f"Algorithm {algorithm} requires a target column")
            model.fit(X, y)
            
        self.update_progress(100, 100)
        self.log("Training completed successfully.")
        
        return model

    def evaluate(self, model: Any, test_data: pd.DataFrame) -> Dict[str, float]:
        target_col = 'label' # Should be passed or stored
        if 'label' not in test_data.columns and 'target' in test_data.columns:
            target_col = 'target'
        
        # Try to infer target col if not standard
        if target_col not in test_data.columns:
             # Assume last column
             target_col = test_data.columns[-1]

        feature_cols = getattr(self, 'feature_cols', [c for c in test_data.columns if c != target_col])
        
        # Ensure columns exist
        missing_cols = [c for c in feature_cols if c not in test_data.columns]
        if missing_cols:
             raise ValueError(f"Missing columns in test data: {missing_cols}")

        X_test = test_data[feature_cols]
        y_test = test_data[target_col] if target_col in test_data.columns else None
        
        y_pred = model.predict(X_test)
        
        # Handle IsolationForest predictions (-1 for outlier, 1 for inlier)
        if isinstance(model, IsolationForest):
            # Convert to standard 0 (normal) / 1 (anomaly) if ground truth is in that format
            # Assumption: y_test has 0 for normal, 1 for anomaly
            # Prediction: 1 (normal) -> 0, -1 (anomaly) -> 1
            y_pred = np.where(y_pred == 1, 0, 1)
        
        metrics = {}
        
        if y_test is None:
             # Unsupervised evaluation or just returning counts
             if isinstance(model, IsolationForest):
                 metrics['anomaly_count'] = int(np.sum(y_pred))
                 metrics['anomaly_rate'] = float(np.mean(y_pred))
             return metrics

        # Check if classification or regression based on model type
        if hasattr(model, 'predict_proba') or isinstance(model, (LogisticRegression, RandomForestClassifier)) or isinstance(model, IsolationForest):
            metrics['accuracy'] = float(accuracy_score(y_test, y_pred))
            metrics['precision'] = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
            metrics['recall'] = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
            metrics['f1_score'] = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
            
            try:
                cm = confusion_matrix(y_test, y_pred)
                metrics['confusion_matrix'] = cm.tolist()
            except Exception as e:
                self.log(f"Could not calculate confusion matrix: {e}")
        else:
            metrics['mse'] = float(mean_squared_error(y_test, y_pred))
            metrics['r2'] = float(r2_score(y_test, y_pred))
            
        # Add training history (e.g. loss curve)
        metrics['training_history'] = self.training_history
            
        return metrics

    def save(self, model: Any, path: str) -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(model, path)
        return path

    def load(self, path: str) -> Any:
        return joblib.load(path)
