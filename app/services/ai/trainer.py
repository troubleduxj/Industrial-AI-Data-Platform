from abc import ABC, abstractmethod
from typing import Any, Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class BaseTrainer(ABC):
    def __init__(self, model_id: int, progress_callback: Optional[Callable[[float], None]] = None, log_callback: Optional[Callable[[str], None]] = None):
        self.model_id = model_id
        self.progress_callback = progress_callback
        self.log_callback = log_callback

    @abstractmethod
    def train(self, data: Any, params: Dict[str, Any]) -> Any:
        """执行训练，返回训练好的模型对象"""
        pass
    
    # ... existing methods ...

    def update_progress(self, current_step: int, total_steps: int):
        if self.progress_callback and total_steps > 0:
            progress = (current_step / total_steps) * 100
            # Ensure progress is between 0 and 100
            progress = max(0.0, min(100.0, progress))
            self.progress_callback(round(progress, 2))

    def log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        logger.info(f"Model {self.model_id}: {message}")
