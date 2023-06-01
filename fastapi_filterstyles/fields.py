from typing import (
    Annotated,
    ClassVar,
    TypeVar,
)
from uuid import UUID

from pydantic import BaseModel, Field

FT = TypeVar("FT", bound="BaseModel")
T = TypeVar("T")

class BaseFilter(BaseModel):
    default_operator: ClassVar[str] = "eq"


DefaultList = Annotated[list[T], Field(default_factory=list)]


class StringFilter(BaseFilter):
    eq: DefaultList[str]
    neq: DefaultList[str]
    contains: DefaultList[str]


class UUIDFilter(BaseFilter):
    eq: DefaultList[UUID]
    neq: DefaultList[UUID]
