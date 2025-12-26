
import asyncio
import time
import httpx

async def test_httpx_speed():
    print("Testing httpx.AsyncClient(trust_env=True)...")
    start_time = time.time()
    async with httpx.AsyncClient(trust_env=True) as client:
        pass
    print(f"trust_env=True time: {time.time() - start_time:.4f}s")
    
    print("Testing httpx.AsyncClient(trust_env=False)...")
    start_time = time.time()
    async with httpx.AsyncClient(trust_env=False) as client:
        pass
    print(f"trust_env=False time: {time.time() - start_time:.4f}s")

if __name__ == "__main__":
    asyncio.run(test_httpx_speed())
