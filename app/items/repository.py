from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.items.models import Item


class ItemRepository(Protocol):
    async def add(self, item: Item) -> Item: ...

    async def get_by_id(self, item_id: UUID) -> Item | None: ...

    async def list_all(self) -> Sequence[Item]: ...


class SqlAlchemyItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: Item) -> Item:
        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)
        return item

    async def get_by_id(self, item_id: UUID) -> Item | None:
        return await self._session.get(Item, item_id)

    async def list_all(self) -> Sequence[Item]:
        result = await self._session.scalars(select(Item).order_by(Item.created_at, Item.id))
        return result.all()
