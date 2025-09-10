from datetime import datetime, timezone
from typing import Any, Iterable, Sequence, TypeAlias, overload

from beanie import Document
from beanie.odm.operators.update.general import Set
from beanie.odm.queries.find import FindMany, FindOne
from beanie.odm.operators.find.logical import (
    LogicalOperatorForListOfExpressions
)
from motor.motor_asyncio import AsyncIOMotorClientSession

ColumnItem: TypeAlias = str | Any


class BeanieRepository[TDoc: Document]:
    model_cls: TDoc

    def __init__(self, model_cls: TDoc):
        self.model_cls = model_cls

    async def count(self, where: dict | None = None) -> int:
        where = where or {}
        return await self.model_cls.find(where).count()

    async def create(self, **values) -> TDoc:
        doc = self.model_cls(**values)
        return await doc.insert()

    async def add_many(self, items: Iterable[TDoc]) -> list[TDoc]:
        return await self.model_cls.insert_many(items)

    async def get_one(
        self,
        *,
        where: dict | LogicalOperatorForListOfExpressions | None = None,
        order_by: Sequence[ColumnItem] | None = None,
        ascending: Sequence[bool] | bool = True,
        skip: int = 0,
        fetch_links: bool = False,
        project: dict[str, int] | None = None,
        session: AsyncIOMotorClientSession | None = None,
    ) -> TDoc | None:
        """
        Возвращает один документ (или None). По сути это get_many(..., limit=1)[0].
        """
        where = where or {}
        query = self.model_cls.find(where, session=session)
        query = self._apply_sorting(query, order_by, ascending)
        query = self._apply_projection(query, project)
        query = query.skip(skip).limit(1)
        query.fetch_links = fetch_links
        return await query.first_or_none()

    async def get_many(
        self,
        *,
        where: dict | LogicalOperatorForListOfExpressions | None = None,
        order_by: Sequence[ColumnItem] | None = None,
        ascending: Sequence[bool] | bool = True,
        limit: int | None = None,
        skip: int | None = None,
        fetch_links: bool = False,
        project: dict[str, int] | None = None,
        session: AsyncIOMotorClientSession | None = None,
    ) -> list[TDoc]:
        where = where or {}
        query = self.model_cls.find(where, session=session)
        query = self._apply_sorting(query, order_by, ascending)
        query = self._apply_projection(query, project)
        if skip:
            query = query.skip(skip)
        if limit:
            query = query.limit(limit)
        query.fetch_links = fetch_links
        return await query.to_list()

    async def get_unique(
        self,
        *,
        where: dict | LogicalOperatorForListOfExpressions,
        fetch_links: bool = False,
        session: AsyncIOMotorClientSession | None = None,
    ) -> TDoc | None:
        """
        Гарантирует, что результат либо 0, либо 1 документ.
        Если найдено больше 1 — возбуждает ValueError (намекает, что нужен unique индекс).
        """
        query = self.model_cls.find(where, session=session)
        query.fetch_links = fetch_links
        docs = await query.limit(2).to_list()
        if len(docs) > 1:
            raise ValueError(
                f"get_unique: найдено более одного документа по фильтру {where}. "
                "Добавь уникальный индекс или используй get_one."
            )
        return docs[0] if docs else None

    @overload
    async def update(self, *, where: dict, **values) -> int: ...

    @overload
    async def update(self, *docs: TDoc, **values) -> int: ...

    async def update(
        self,
        *docs: TDoc,
        where: dict | LogicalOperatorForListOfExpressions | None = None,
        **values,
    ) -> int:
        """
        Обновление:
        - update(where=..., field=value) -> массовое обновление, возвращает число изменённых.
        - update(doc1, doc2, ..., field=value) -> сохранит каждую переданную сущность.
        """
        if not values:
            return 0

        if where is not None:
            res = await self.model_cls.find(where).update_many(Set(values))
            return int(res.modified_count)

        if docs:
            # обновляем переданные документы в памяти и .save() по каждому
            modified = 0
            for d in docs:
                for k, v in values.items():
                    setattr(d, k, v)
                out = await d.save()
                modified += 1 if out is not None else 0
            return modified

        raise ValueError("Нужно либо where=..., либо передать документы для обновления")

    @overload
    async def delete(self, *docs: TDoc, soft: bool = True) -> int: ...

    @overload
    async def delete(self, *, where: dict, soft: bool = True) -> int: ...

    async def delete(
        self, *docs: TDoc, where: dict | None = None,
        soft: bool = True,
    ) -> int:
        """
        Удаление:
        - soft=True: выставляет deleted_at (если поле есть), иначе бросает исключение.
        - soft=False: физическое удаление.
        Возвращает число затронутых документов.
        """
        if soft:
            if not hasattr(self.model_cls, "deleted_at"):
                raise AttributeError(
                    f"{self.model_cls.__name__} не содержит поля deleted_at — "
                    "мягкое удаление невозможно"
                )
            tz = timezone.utc  # Mongo хранит naive/aware — решай единообразно
            if where is not None:
                res = await self.model_cls.find(where).update_many(
                    Set({"deleted_at": datetime.now(tz)})
                )
                return int(res.modified_count)
            if docs:
                modified = 0
                for doc in docs:
                    setattr(doc, "deleted_at", datetime.now(tz))
                    out = await doc.save()
                    modified += 1 if out is not None else 0
                return modified
            raise ValueError("Нужно либо where=..., либо передать документы для удаления")

        if where is not None:
            res = await self.model_cls.find(where).delete()
            return int(getattr(res, "deleted_count", 0))
        if docs:
            deleted = 0
            for d in docs:
                out = await d.delete()
                deleted += 1 if out is not None else 0
            return deleted

        raise ValueError("Нужно либо where=..., либо передать документы для удаления")

    async def upsert_one(
        self,
        *,
        where: dict,
        set_values: dict | None = None,
        set_on_insert: dict | None = None,
    ) -> TDoc:

        set_values = set_values or {}
        set_on_insert = set_on_insert or {}

        await self.model_cls.find(where).upsert_one(
            on_insert={**where, **set_on_insert},  # что вставлять, если нет
            on_update=Set(set_values),             # что обновлять, если есть
        )
        return await self.model_cls.find_one(where)


    def _resolve_field(self, item: ColumnItem):
        if isinstance(item, str):
            return getattr(self.model_cls, item)
        return item

    def _apply_sorting(
        self,
        query: FindMany[TDoc] | FindOne[TDoc],
        order_by: Sequence[ColumnItem] | None,
        ascending: Sequence[bool] | bool,
    ):
        if not order_by:
            return query

        if isinstance(ascending, (list, tuple)):
            if not isinstance(order_by, (list, tuple)):
                raise ValueError("Iterable `ascending` требует iterable `order_by`")
            if len(ascending) != len(order_by):
                raise ValueError("`ascending` и `order_by` должны быть одинаковой длины")
            pairs = zip(order_by, ascending)
        else:
            pairs = ((f, ascending) for f in order_by)

        sort_items = []
        for f, asc in pairs:
            fld = self._resolve_field(f)
            sort_items.append(+fld if asc else -fld)
        return query.sort(*sort_items)

    def _apply_projection(
        self,
        query: FindMany[TDoc] | FindOne[TDoc],
        project: dict[str, int] | None,
    ):
        return query.project(project) if project else query
