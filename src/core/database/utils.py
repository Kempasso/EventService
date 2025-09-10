from pydantic import BaseModel
from beanie import Document
from beanie.odm.operators.find.logical import And

from src.core.schemas import RangeFilter


def parse_filters[Filters: BaseModel](
    filters: Filters | None,
    model: Document
):
    clause = {}
    if filters is None:
        return clause

    for field in filters.model_fields:
        if item := getattr(model, field):
            match getattr(filters, field):
                case RangeFilter(min=min_val, max=max_val):
                    if min_val is not None:
                        clause = And(clause, item >= min_val)
                    if max_val is not None:
                        clause = And(clause, item <= max_val)