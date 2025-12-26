from app.celery_app import app
from app.models.ai_monitoring import AIModel, ModelStatus
from app.log import logger
import asyncio
from asgiref.sync import async_to_sync
from tortoise import Tortoise
from app.settings.config import settings
from datetime import datetime
import json
import pandas as pd
import numpy as np
import os
from app.services.ai.factory import TrainerFactory
from app.services.ai.data_loader import TDengineLoader

@app.task(bind=True)
def train_model(self, model_id: int, train_config: dict):
    """
    Celery task for training AI model.
    """
    async_to_sync(run_training)(self, model_id, train_config)

async def run_training(task, model_id: int, train_config: dict):
    # Initialize Tortoise for this specific event loop
    # Force reset _inited flag to ensure new connections are created for the new loop
    Tortoise._inited = False
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    model = None
    try:
        # Retry logic for fetching the model (handle transaction latency)
        for i in range(5):
            try:
                model = await AIModel.get(id=model_id)
                break
            except Exception:
                if i == 4: # Last attempt
                    logger.error(f"Task {task.request.id}: Model {model_id} not found after 5 attempts. Task will be discarded.")
                    return # Exit gracefully, acknowledging task
                logger.warning(f"Task {task.request.id}: Model {model_id} not found, retrying in 1s... ({i+1}/5)")
                await asyncio.sleep(1.0)
        
        if not model:
            logger.warning(f"Task {task.request.id}: Model {model_id} is None, aborting.")
            return

        # Update task info
        # Safely get task_id
        task_id = task.request.id if task.request else None
        model.task_id = task_id
        model.started_at = datetime.now()
        model.status = ModelStatus.TRAINING
        model.progress = 5.0
        await model.save()
        
        # 1. Load Data
        loader = TDengineLoader()
        dataset_config = train_config.get('training_dataset')
        
        if isinstance(dataset_config, str):
            try:
                dataset_config = json.loads(dataset_config)
            except:
                pass
        
        if not isinstance(dataset_config, dict):
            dataset_config = {}

        device_id = dataset_config.get('device_id')
        start_time = dataset_config.get('start_time')
        end_time = dataset_config.get('end_time')
        
        df = pd.DataFrame()
        if device_id and start_time and end_time:
             try:
                 df = await loader.load(device_id, start_time, end_time)
             except Exception as load_error:
                 logger.warning(f"Failed to load data from TDengine: {load_error}")
        
        if df.empty:
             logger.warning("Using dummy data for training due to empty result or missing config")
             # Dummy data
             df = pd.DataFrame({
                 'feature1': np.random.rand(100),
                 'feature2': np.random.rand(100),
                 'label': np.random.randint(0, 2, 100)
             })

        model.progress = 20.0
        await model.save()

        # 2. Initialize Trainer
        loop = asyncio.get_running_loop()
        logger.info(f"Task {model_id}: Starting training with loop {loop}")
        
        def progress_callback(p):
            # Scale trainer progress (0-100) to overall task progress (20-90)
            # Trainer reports 0-100, we map it to 20-90 range
            scaled_p = 20.0 + (p * 0.7)
            logger.info(f"Task {model_id}: Progress callback p={p}, scaled={scaled_p}")
            
            # Update Celery state
            if task.request.id:
                try:
                    task.update_state(state='PROGRESS', meta={'progress': scaled_p})
                except Exception as e:
                    logger.warning(f"Failed to update task state: {e}")
            
            # Update DB safely from thread
            async def update_db_progress():
                try:
                    logger.info(f"Task {model_id}: Updating DB progress to {scaled_p}")
                    # Re-fetch model to avoid staleness, or just update
                    await AIModel.filter(id=model_id).update(progress=scaled_p)
                except Exception as e:
                    logger.error(f"Failed to update progress in DB: {e}")
            
            try:
                # Use call_soon_threadsafe instead of run_coroutine_threadsafe to ensure it runs in the loop
                # But call_soon_threadsafe expects a callback, not a coroutine.
                # So we use create_task inside the callback.
                def schedule_update():
                    loop.create_task(update_db_progress())
                
                loop.call_soon_threadsafe(schedule_update)
            except Exception as e:
                logger.error(f"Failed to schedule DB update: {e}")
            
        def log_callback(msg):
            # Update DB safely from thread
            async def update_db_log():
                try:
                    # Append log. Note: Concurrency might be an issue if logs come too fast.
                    # Ideally we should use a separate table for logs or just overwrite/append carefully.
                    # Here we append.
                    model_obj = await AIModel.get(id=model_id)
                    current_log = model_obj.error_log or ""
                    new_log = current_log + f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n"
                    # Truncate if too long (e.g. 10000 chars)
                    if len(new_log) > 10000:
                         new_log = new_log[-10000:]
                    model_obj.error_log = new_log
                    await model_obj.save(update_fields=['error_log'])
                except Exception as e:
                    logger.error(f"Failed to update log in DB: {e}")

            try:
                def schedule_log_update():
                    loop.create_task(update_db_log())
                loop.call_soon_threadsafe(schedule_log_update)
            except Exception as e:
                logger.error(f"Failed to schedule DB log update: {e}")

        trainer = TrainerFactory.create_trainer(
            model_type=model.framework,
            model_id=model_id,
            progress_callback=progress_callback,
            log_callback=log_callback
        )
        
        # 3. Train
        params = train_config.get('training_parameters', {})
        params['algorithm'] = model.algorithm
        
        # Add real-time log simulation (or implement real logging if trainer supports it)
        # For now we just log start
        model.error_log = "Starting training...\n"
        await model.save()
        
        # Run synchronous training code in thread pool
        # loop is already defined above
        trained_model = await loop.run_in_executor(None, trainer.train, df, params)
        
        model.error_log += "Training completed.\nStarting evaluation...\n"
        await model.save()
        
        # 4. Evaluate
        metrics = await loop.run_in_executor(None, trainer.evaluate, trained_model, df)
        
        model.error_log += f"Evaluation completed. Metrics: {json.dumps(metrics)}\nSaving model...\n"
        await model.save()
        
        # 5. Save
        save_dir = f"data/ai_models/{model.model_name}/{model.model_version}"
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "model.joblib")
        saved_path = await loop.run_in_executor(None, trainer.save, trained_model, path)
        
        # 6. Update DB
        model.status = ModelStatus.TRAINED
        model.progress = 100.0
        model.finished_at = datetime.now()
        model.training_metrics = metrics
        model.model_file_path = saved_path
        model.model_file_size = os.path.getsize(saved_path)
        await model.save()
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if model:
            model.status = ModelStatus.ERROR
            model.error_log = str(e)
            await model.save()
        raise e
    finally:
        # Close connections to avoid leaking them or leaving them attached to a closed loop
        await Tortoise.close_connections()
