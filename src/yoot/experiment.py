from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field, FilePath, ValidationError

from yoot.exceptions import TaskDefinitionError




class ExperimentSchema(BaseModel):
    tasks: dict[str, TaskSchema]
    
    def validate(self) -> None:
        for name, task in self.tasks.items():
            if not task.inputs:
                raise ValueError(f"Task {name} has no inputs.")
            if not task.outputs:
                raise ValueError(f"Task {name} has no outputs.")
            if task.params:
                for param in task.params:
                    if param not in task.inputs:
                        raise ValueError(f"Task {name} has a parameter {param} that is not an input.")
    
    def get_task(self, name: str) -> TaskSchema:
        
        

        
