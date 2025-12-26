from typing import Optional, Callable
from app.services.ai.trainer import BaseTrainer
from app.services.ai.sklearn_trainer import SklearnTrainer

class TrainerFactory:
    @staticmethod
    def create_trainer(model_type: str, model_id: int, progress_callback: Optional[Callable[[float], None]] = None, log_callback=None) -> BaseTrainer:
        # Normalize model type
        model_type = model_type.lower() if model_type else 'sklearn'
        
        if model_type in ['sklearn', 'scikit-learn']:
            return SklearnTrainer(model_id, progress_callback, log_callback)
        # Add other types like 'pytorch' later
        else:
            # Default to sklearn if unknown, or raise error
            return SklearnTrainer(model_id, progress_callback, log_callback)
