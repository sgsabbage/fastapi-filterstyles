from inspect import Parameter, Signature
from typing import Annotated, Any, Callable, Type, TypeVar, Union, get_args

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.routing import APIRoute
from fastapi_filterstyles.fields import BaseFilter
from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField

FT = TypeVar("FT", bound="BaseModel")
T = TypeVar("T")


def delimited_filter(filter_cls: Type[FT]) -> Callable[..., FT]:
    """
    Creates a filter dependency that accepts query strings in a delimited format
    e.g. ?name=contains:shell&name=neq:shell+beach
    """

    def dependency(**kwargs: str) -> FT:
        params: dict[str, Union[dict[str, list[str]], str, None]] = {}
        for key, field in filter_cls.__fields__.items():
            arg_val = kwargs.get(key)
            if not issubclass(field.type_, BaseFilter):
                params[key] = arg_val
                continue

            operations: dict[str, Any] = {}
            params[key] = operations

            if arg_val is None:
                continue

            filter_fields = field.type_.__fields__

            for val in arg_val:
                val_array = val.split(":")
                op = val_array[0]

                if op in filter_fields and filter_fields[op].field_info.extra.get(
                    "flag"
                ):
                    operations[op] = True
                    continue
                if len(val_array) == 1:
                    op = field.type_.default_operator
                fil = val_array[-1]
                if op not in operations:
                    operations[op] = []
                operations[op].append(fil)
        try:
            return filter_cls(**params)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
            )

    params = []
    # BaseModel.__fields__ is replaced with BaseModel.model_fields in Pydantic v2
    if (fields := getattr(filter_cls, "model_fields", None)) is None:
        fields = filter_cls.__fields__

    for key, field in fields.items():
        if issubclass(field.type_, BaseFilter):
            extra = field.field_info.extra
            description = (
                f"{field.field_info.description} "
                if field.field_info.description
                else ""
            )
            operators = extra.get(
                "operators",
                [
                    sub_field.field_info.alias or field_name
                    for field_name, sub_field in field.type_.__fields__.items()
                ],
            )
            description += (
                f"Allowed operators: `{'`, `'.join(operators)}`. "
                f"Default operator `{field.type_.default_operator}`"
            )
            name = field.field_info.alias or key
            parameter = Parameter(
                name=name,
                annotation=list[str],
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Query(
                    None,
                    description=description,
                    pattern=rf"^({':|'.join(operators)}:)?[^:]+$",
                    examples=extra.get("examples", None),
                ),
            )
        else:
            name = field.field_info.alias or key
            parameter = Parameter(
                name=name,
                annotation=field.type_,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
            )
        params.append(parameter)

    dependency.__signature__ = Signature(parameters=params)  # type: ignore
    return dependency


def deep_object_filter(filter_cls: Type[FT]) -> Callable[..., FT]:
    """
    Creates a filter dependency that accepts query strings in OpenAPI's
    deep object format
    e.g. ?name[contains]=shell&name[neq]=shell+beach

    For the OpenAPI documentation to be updated correctly, update_deep_objects() must be
    run on the FastAPI app instance.
    """
    params = []

    filter_fields: dict[str, ModelField] = {}

    for key, value in filter_cls.__fields__.items():
        if issubclass(value.type_, BaseFilter):
            filter_fields[key] = value
            schema = value.type_.schema()
            if operators := value.field_info.extra.get("operators"):
                schema["properties"] = {
                    k: v for k, v in schema["properties"].items() if k in operators
                }
            for p, p_value in value.type_.__fields__.items():
                if args := get_args(p_value.annotation):
                    annotation = args[0]
                else:
                    annotation = p_value.annotation
                params.append(
                    Parameter(
                        name=f"{key}__{p}",
                        annotation=Annotated[
                            annotation,
                            Query(include_in_schema=False, alias=f"{key}[{p}]"),
                        ],
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        default=None,
                    )
                )
            parameter = Parameter(
                name=key,
                annotation=Annotated[
                    None,
                    Query(include_in_schema=False, deep_object=True, schema=schema),
                ],
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
            )
        else:
            parameter = Parameter(
                name=key,
                annotation=value.type_,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
            )
        params.append(parameter)

    def dependency(**kwargs: str) -> FT:
        params: dict[str, Any] = {}
        for key in filter_fields:
            params[key] = {}
        for k, v in kwargs.items():
            if k in filter_fields or v is None:
                continue
            split_key = k.split("__")
            if len(split_key) == 1:
                params[k] = v
                continue
            params[split_key[0]][split_key[1]] = v
        try:
            return filter_cls(**params)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
            )

    dependency.__signature__ = Signature(parameters=params)  # type: ignore

    return dependency


def update_deep_objects(app: FastAPI) -> None:
    """
    Updates all of the app's routes to ensure that the deep object schema
    is created successfully and can be viewed as part of the documentation
    """
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        parameters = []
        for dependency in route.dependant.dependencies:
            for field in dependency.query_params:
                args = get_args(field.annotation)
                if len(args) == 2 and getattr(args[1], "extra", {}).get("deep_object"):
                    schema = args[1].extra["schema"]
                    operators = schema["properties"].keys()
                    parameters.append(
                        {
                            "name": field.name,
                            "in": "query",
                            "style": "deepObject",
                            "schema": schema,
                            "description": f"Allowed keys: `{'`, `'.join(operators)}`.",
                        }
                    )
        if parameters:
            route.openapi_extra = {"parameters": parameters}
