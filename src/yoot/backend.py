

from yoot.task import TaskDefinition


class Backend:
    async def run(self, tasks: dict[str, TaskDefinition]) -> None:
        