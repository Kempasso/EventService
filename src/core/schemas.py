from typing import Optional, Literal

from pydantic import BaseModel, Field

class RangeFilter[RangeType](BaseModel):
    min: Optional[RangeType] = None
    max: Optional[RangeType] = None

class OrderItem(BaseModel):
    column: str
    ascending: bool = True

class TableRequest[Filters: BaseModel](BaseModel):
    filters: Optional[Filters] = None
    order: Optional[list[OrderItem]] = None
    page: int = Field(ge=0, default=1)
    page_size: int = Field(gt=0, le=50, default=10)
    sort_by: Optional[str] = None
    sort_order: Optional[Literal['asc', 'desc']] = None

class TableResponse[ItemModel: BaseModel](BaseModel):
    page: int
    pages: int
    total_count: int
    items: list[ItemModel]