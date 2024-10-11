import importlib
from functools import partial
from inspect import Signature
from pathlib import Path
from typing import Annotated, Any, Callable, Self

from pydantic import BaseModel, Field, FilePath, ValidationError

from yoot.exceptions import TaskDefinitionError
from yoot.tracker import Tracker


class TaskMetadata(BaseModel):
    inputs: Annotated[set[str], Field(default_factory=set)]
    outputs: Annotated[set[str], Field(default_factory=set)]
    params: dict[str, Any] | None = None


class TaskSchema(TaskMetadata):
    func: str


class ValidatedTaskSchema(TaskMetadata):
    file: FilePath
    name: str

    @classmethod
    def from_unvalidated(cls, schema: TaskSchema) -> Self:
        split_func = schema.func.split(":")

        if len(split_func) != 2:
            raise TaskDefinitionError(f"Invalid function definition: {schema.func}")

        file, func_name = split_func
        try:
            return cls(file=Path(file), func_name=func_name, **schema.model_dump())
        except ValidationError as e:
            raise TaskDefinitionError("Invalid task schema.") from e


type TaskFunction[TParams: BaseModel] = Callable[
    [Tracker, TParams | None, str], dict[str, Any] | None
]


class Task[TParams: BaseModel](BaseModel):
    name: str
    func: TaskFunction[TParams]
    param_schema: type[TParams] | None = None

    @classmethod
    def define(
        cls,
        func: TaskFunction[TParams] | None = None,
        *,
        name: str | None = None,
        params: type[TParams] | None = None,
    ):
        if func is None:
            return partial(cls.define, name=name, params=params)

        name = name or func.__name__
        return cls(name=name, func=func, param_schema=params)


class TaskDefinition(TaskMetadata):
    name: str

    def _validate_schema(self, schema: TaskSchema):
        split_func = schema.func.split(":")
        if len(split_func) != 2:
            raise TaskDefinitionError(f"Invalid function definition: {schema.func}")

        file, func_name = split_func

        spec = importlib.util.spec_from_file_location("my_module", file_path)
        my_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(my_module)

        return getattr(my_module, func_name)

    def validate(self, task: Task, schema: TaskSchema):
        signature = Signature.from_callable(task.func)

        arg_names = set(signature.parameters)
        if "tracker" not in arg_names:
            raise TaskDefinitionError(
                f"Task {task.name} is missing the 'tracker' parameter."
            )
        arg_names.remove("tracker")

        if self.params and task.param_schema is None:
            raise TaskDefinitionError(
                f"Task {task.name} does not accept parameters but Task definition defines them."
            )

        if self.params is None and task.param_schema:
            raise TaskDefinitionError(
                f"Task {task.name} requires parameters but Task definition does not define them."
            )

        if self.params and task.param_schema:
            try:
                params = task.param_schema.parse_obj(self.params)
            except ValidationError as e:
                raise TaskDefinitionError(
                    f"Task {task.name} parameters are invalid."
                ) from e
        else:
            params = None
        arg_names.discard("params")

        if arg_names != set(self.inputs):
            raise TaskDefinitionError(
                f"Task {task.name} inputs do not match the Task definition."
            )

        return ValidatedTaskDefinition(
            name=self.name,
            params=params,
            inputs=self.inputs,
            outputs=self.outputs,
        )


class ValidatedTaskDefinition[TParams: BaseModel](TaskDefinition):
    params: TParams | None = None

    def validate_outputs(self, outputs: dict[str, Any]):
        actual_outputs_set = set(outputs.keys())

        missing_outputs = self.outputs - actual_outputs_set
        extra_outputs = actual_outputs_set - self.outputs

        if missing_outputs:
            raise TaskDefinitionError(
                f"Task is missing expected outputs: {', '.join(missing_outputs)}."
            )

        if extra_outputs:
            raise TaskDefinitionError(
                f"Task has unexpected outputs: {', '.join(extra_outputs)}."
            )
