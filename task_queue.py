import asyncio
import json
import time
import uuid
import threading
from typing import Dict, List, Callable, Any, Optional


class TaskQueue:
    """异步任务队列 — 自动化任务排队执行，不阻塞页面请求"""

    def __init__(self, max_concurrent: int = 4, max_queue: int = 50):
        self.max_concurrent = max_concurrent
        self.max_queue = max_queue
        self._queue: asyncio.Queue = None
        self._running = 0
        self._results: Dict[str, dict] = {}
        self._event: Dict[str, asyncio.Event] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._workers: list = []
        self._started = False

    def init(self, loop: asyncio.AbstractEventLoop, max_concurrent: int = None):
        if self._started:
            return
        if max_concurrent is not None:
            self.max_concurrent = max_concurrent
        self._queue = asyncio.Queue(maxsize=self.max_queue)
        for _ in range(self.max_concurrent):
            self._workers.append(loop.create_task(self._worker_loop()))
        self._started = True
        print(f"[TaskQueue] Initialized: max_concurrent={self.max_concurrent}, max_queue={self.max_queue}")

    def set_concurrency(self, n: int):
        """动态调整并发数"""
        old = self.max_concurrent
        self.max_concurrent = max(1, min(n, 50))
        print(f"[TaskQueue] Concurrency: {old} -> {self.max_concurrent}")

    async def submit(self, task_id: str, coro_func, *args, **kwargs) -> str:
        if self._queue.qsize() >= self.max_queue:
            return None
        self._results[task_id] = {
            "status": "queued",
            "queue_pos": self._queue.qsize() + 1,
            "events": [],
            "started_at": None,
            "finished_at": None,
        }
        self._event[task_id] = asyncio.Event()
        await self._queue.put((task_id, coro_func, args, kwargs))
        return task_id

    async def wait_event(self, task_id: str, timeout: float = 1.0):
        evt = self._event.get(task_id)
        if evt:
            try:
                await asyncio.wait_for(evt.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass
            evt.clear()

    def get_result(self, task_id: str) -> dict:
        return self._results.get(task_id, {"status": "unknown"})

    def push_event(self, task_id: str, event: dict):
        r = self._results.get(task_id)
        if r:
            r["events"].append(event)

    def pop_events(self, task_id: str) -> list:
        r = self._results.get(task_id)
        if r and r["events"]:
            events = r["events"][:]
            r["events"] = []
            return events
        return []

    def cleanup(self, task_id: str):
        self._results.pop(task_id, None)
        self._event.pop(task_id, None)

    @property
    def queue_size(self):
        return self._queue.qsize() if self._queue else 0

    @property
    def running_count(self):
        return self._running

    async def _worker_loop(self):
        while True:
            task_id, coro_func, args, kwargs = await self._queue.get()
            self._running += 1
            r = self._results.get(task_id, {})
            r["status"] = "running"
            r["started_at"] = time.time()
            try:
                await coro_func(task_id, *args, **kwargs)
                r["status"] = "completed"
            except Exception as e:
                r["status"] = "failed"
                r["error"] = str(e)[:500]
                self.push_event(task_id, {"type": "error", "content": str(e)[:200]})
            finally:
                r["finished_at"] = time.time()
                self._running -= 1
                evt = self._event.get(task_id)
                if evt:
                    evt.set()
                self._queue.task_done()


auto_task_queue = TaskQueue(max_concurrent=4, max_queue=50)
