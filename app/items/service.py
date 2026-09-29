from collections.abc import Sequence
from uuid import UUID

import structlog

from app.items.exceptions import ItemNotFoundError
from app.items.models import Item
from app.items.repository import ItemRepository
from app.items.schemas import ItemCreate

logger = structlog.get_logger()


class ItemService:
    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    async def create(self, data: ItemCreate) -> Item:
        item = Item(name=data.name)
        item = await self._repository.add(item)
        logger.info("item_created", item_id=str(item.id))
        return item

    async def get(self, item_id: UUID) -> Item:
        item = await self._repository.get_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(item_id)
        return item

    async def list(self) -> Sequence[Item]:
        return await self._repository.list_all()
