from typing import Optional, Literal

from pydantic import BaseModel, Field

class RangeFilter[RangeType](BaseModel):
    min: Optional[RangeType] = None
    max: Optional[RangeType] = None

class TableRequest[Filters: BaseModel](BaseModel):
    filters: Optional[Filters] = None
    page: int = Field(ge=0, default=1)
    page_size: int = Field(gt=0, le=50, default=10)

class TableResponse[ItemModel: BaseModel](BaseModel):
    page: int
    pages: int
    total_count: int
    items: list[ItemModel]