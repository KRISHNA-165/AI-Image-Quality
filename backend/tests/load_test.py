"""
Concurrent Load & Performance Benchmark for QualiVision AI Engine.
Demonstrates asynchronous non-blocking throughput across concurrent clients.
"""

import asyncio
import time
import io
import httpx
from PIL import Image

BASE_URL = "http://localhost:8000/api/v1"

def create_dummy_png():
    img = Image.new("RGB", (256, 256), color=(120, 150, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

async def send_single_analysis(client: httpx.AsyncClient, img_bytes: bytes, req_id: int):
    start = time.perf_counter()
    files = {"file": (f"load_test_{req_id}.png", img_bytes, "image/png")}
    response = await client.post(f"{BASE_URL}/analyze", files=files, timeout=30.0)
    duration_ms = (time.perf_counter() - start) * 1000
    return response.status_code, duration_ms

async def run_load_benchmark(total_requests: int = 20, concurrency: int = 5):
    print(f"=== Starting Load Test: {total_requests} requests @ concurrency {concurrency} ===")
    img_bytes = create_dummy_png()
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient() as client:
        async def _bounded_send(i):
            async with semaphore:
                return await send_single_analysis(client, img_bytes, i)

        start_all = time.perf_counter()
        results = await asyncio.gather(*[_bounded_send(i) for i in range(total_requests)])
        total_time = time.perf_counter() - start_all

    statuses = [r[0] for r in results]
    latencies = [r[1] for r in results]

    success_count = sum(1 for s in statuses if s == 201)
    avg_lat = sum(latencies) / len(latencies)
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]
    rps = total_requests / total_time

    print(f"\n--- Benchmark Results ---")
    print(f"Total Requests:      {total_requests}")
    print(f"Successful (201):    {success_count}/{total_requests}")
    print(f"Total Duration:      {total_time:.2f}s")
    print(f"Throughput:          {rps:.2f} req/s")
    print(f"Average Latency:     {avg_lat:.2f}ms")
    print(f"P95 Latency:         {p95_lat:.2f}ms")
    print("-------------------------\n")

    return success_count == total_requests

if __name__ == "__main__":
    asyncio.run(run_load_benchmark(total_requests=10, concurrency=4))
