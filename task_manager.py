import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from models.intent import ParsedIntent
from models.task import Task, TaskStatus, StepResult, StepStatus


class TaskManager:
    def __init__(self, mongodb):
        self.db = mongodb
        self.collection = self.db["tasks"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("conversation_id")
            self.collection.create_index("status")
            self.collection.create_index(
                "expires_at",
                expireAfterSeconds=0,
                partialFilterExpression={"expires_at": {"$exists": True}}
            )
        except Exception:
            pass

    async def create_task(
        self,
        user_message: str,
        intent: ParsedIntent,
        conversation_id: str = None
    ) -> Task:
        now = datetime.utcnow()
        task = Task(
            id=str(uuid.uuid4())[:12],
            conversation_id=conversation_id,
            user_message=user_message,
            intent=intent.model_dump() if hasattr(intent, 'model_dump') else intent.dict(),
            status=TaskStatus.IN_PROGRESS,
            steps=[],
            results={},
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=2)
        )

        self.collection.insert_one(task.model_dump() if hasattr(task, 'model_dump') else task.dict())
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        doc = self.collection.find_one({"id": task_id})
        if doc:
            doc.pop("_id", None)
            return Task(**doc)
        return None

    async def update_step(self, task_id: str, step: StepResult):
        self.collection.update_one(
            {"id": task_id},
            {
                "$push": {"steps": step.model_dump() if hasattr(step, 'model_dump') else step.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    async def update_step_result(self, task_id: str, step_id: str, result: str, status: StepStatus):
        self.collection.update_one(
            {"id": task_id, "steps.step_id": step_id},
            {
                "$set": {
                    "steps.$.result": result,
                    "steps.$.status": status.value,
                    "steps.$.completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

    async def complete_task(self, task_id: str, results: dict = None):
        update = {
            "$set": {
                "status": TaskStatus.COMPLETED.value,
                "updated_at": datetime.utcnow()
            }
        }
        if results:
            update["$set"]["results"] = results
        self.collection.update_one({"id": task_id}, update)

    async def fail_task(self, task_id: str, error: str):
        self.collection.update_one(
            {"id": task_id},
            {
                "$set": {
                    "status": TaskStatus.FAILED.value,
                    "results": {"error": error},
                    "updated_at": datetime.utcnow()
                }
            }
        )

    async def pause_task(self, task_id: str):
        self.collection.update_one(
            {"id": task_id},
            {"$set": {"status": TaskStatus.PAUSED.value, "updated_at": datetime.utcnow()}}
        )

    async def get_pending_tasks(self, conversation_id: str) -> List[Task]:
        cursor = self.collection.find({
            "conversation_id": conversation_id,
            "status": {"$in": [TaskStatus.IN_PROGRESS.value, TaskStatus.PAUSED.value]}
        })
        tasks = []
        for doc in cursor:
            doc.pop("_id", None)
            tasks.append(Task(**doc))
        return tasks
