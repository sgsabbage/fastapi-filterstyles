from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, ClassVar, Literal, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

FT = TypeVar("FT", bound="BaseModel")
T = TypeVar("T")


class BaseFilter(BaseModel):
    default_operator: ClassVar[str] = "eq"

    def __bool__(self) -> bool:
        return bool(self.__fields_set__)


DefaultList = Annotated[list[T], Field(default_factory=list)]
FlagField = Annotated[Optional[Literal[True]], Field(flag=True)]

# Null checks
#     "is_empty"
#     "is_not_empty"

# Equality
#     "eq"
#     "neq"

# Comparison
#     "gt"
#     "lt"
#     "gte"
#     "lte"

# Date
#     "is_before"
#     "is_after"

# Partial matches
#     "starts_with"
#     "ends_with"
#     "contains"
#     "not_contains"

# Membership
#     "in"


class StringFilter(BaseFilter):
    eq: DefaultList[str]
    neq: DefaultList[str]
    contains: DefaultList[str]
    not_contains: DefaultList[str]
    starts_with: DefaultList[str]
    ends_with: DefaultList[str]
    is_empty: FlagField
    is_not_empty: FlagField
    in_: list[str] = Field(
        default_factory=list,
        alias="in",
    )
    not_in: DefaultList[str]


class UUIDFilter(BaseFilter):
    eq: DefaultList[UUID]
    neq: DefaultList[UUID]
    is_empty: FlagField
    is_not_empty: FlagField
    in_: list[UUID] = Field(
        default_factory=list,
        alias="in",
    )
    not_in: DefaultList[UUID]


class IntFilter(BaseFilter):
    eq: DefaultList[int]
    neq: DefaultList[int]
    gt: DefaultList[int]
    lt: DefaultList[int]
    gte: DefaultList[int]
    lte: DefaultList[int]
    is_empty: FlagField
    is_not_empty: FlagField


class FloatFilter(BaseFilter):
    eq: DefaultList[float]
    neq: DefaultList[float]
    gt: DefaultList[float]
    lt: DefaultList[float]
    gte: DefaultList[float]
    lte: DefaultList[float]
    is_empty: FlagField
    is_not_empty: FlagField


class DecimalFilter(BaseFilter):
    eq: DefaultList[Decimal]
    neq: DefaultList[Decimal]
    gt: DefaultList[Decimal]
    lt: DefaultList[Decimal]
    gte: DefaultList[Decimal]
    lte: DefaultList[Decimal]
    is_empty: FlagField
    is_not_empty: FlagField


class DateFilter(BaseFilter):
    eq: DefaultList[date]
    neq: DefaultList[date]
    gt: DefaultList[date]
    lt: DefaultList[date]
    gte: DefaultList[date]
    lte: DefaultList[date]
    is_empty: FlagField
    is_not_empty: FlagField
    is_before: DefaultList[date]
    is_after: DefaultList[date]


class DateTimeFilter(BaseFilter):
    eq: DefaultList[datetime]
    neq: DefaultList[datetime]
    gt: DefaultList[datetime]
    lt: DefaultList[datetime]
    gte: DefaultList[datetime]
    lte: DefaultList[datetime]
    is_empty: FlagField
    is_not_empty: FlagField
    is_before: DefaultList[datetime]
    is_after: DefaultList[datetime]
