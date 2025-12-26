import asyncio
import httpx
import time
import random
import logging
from typing import List

# Configuration
API_URL = "http://localhost:8001/api/v2/ai/models"
CONCURRENT_TASKS = 10
TOTAL_TASKS = 20
POLL_INTERVAL = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_and_train_model(client: httpx.AsyncClient, index: int):
    model_name = f"stress_test_model_{index}_{int(time.time())}"
    
    # 1. Create Model
    create_payload = {
        "model_name": model_name,
        "model_version": "v1.0",
        "description": "Stress test model",
        "model_type": "classification",
        "algorithm": "RandomForest",
        "framework": "Scikit-learn",
        "training_dataset": "{\"device_id\": \"test_device\", \"start_time\": \"2023-01-01\", \"end_time\": \"2023-01-02\"}",
        "training_parameters": {
            "n_estimators": 10,
            "max_depth": 5
        }
    }
    
    try:
        response = await client.post(API_URL, json=create_payload)
        response.raise_for_status()
        model_id = response.json()['data']['id']
        logger.info(f"Model {model_id} created.")
        
        # 2. Train Model
        train_payload = {
            "training_dataset": create_payload["training_dataset"],
            "training_parameters": create_payload["training_parameters"]
        }
        
        start_time = time.time()
        response = await client.post(f"{API_URL}/{model_id}/train", json=train_payload)
        response.raise_for_status()
        logger.info(f"Training started for model {model_id}.")
        
        # 3. Poll for completion
        while True:
            response = await client.get(f"{API_URL}/{model_id}")
            response.raise_for_status()
            data = response.json()['data']
            status = data['status']
            
            if status == 'trained':
                duration = time.time() - start_time
                logger.info(f"Model {model_id} finished training in {duration:.2f}s.")
                return True, duration
            elif status == 'error':
                logger.error(f"Model {model_id} failed.")
                return False, 0
            
            await asyncio.sleep(POLL_INTERVAL + random.random()) # Jitter
            
    except Exception as e:
        logger.error(f"Error processing model {index}: {e}")
        return False, 0

async def run_stress_test():
    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = []
        for i in range(TOTAL_TASKS):
            tasks.append(create_and_train_model(client, i))
            if len(tasks) >= CONCURRENT_TASKS:
                await asyncio.gather(*tasks)
                tasks = []
        
        if tasks:
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    start = time.time()
    asyncio.run(run_stress_test())
    total_time = time.time() - start
    logger.info(f"Stress test completed in {total_time:.2f}s")
