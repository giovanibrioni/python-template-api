from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.items.exceptions import ItemNotFoundError
from app.items.models import Item
from app.items.schemas import ItemCreate
from app.items.service import ItemService


class FakeItemRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Item] = {}

    async def add(self, item: Item) -> Item:
        if item.id is None:
            item.id = uuid4()
        if item.created_at is None:
            item.created_at = datetime.now(UTC)
        self.items[item.id] = item
        return item

    async def get_by_id(self, item_id: UUID) -> Item | None:
        return self.items.get(item_id)

    async def list_all(self) -> Sequence[Item]:
        return list(self.items.values())


@pytest.fixture
def service() -> ItemService:
    return ItemService(FakeItemRepository())


async def test_create_stores_item(service: ItemService) -> None:
    created = await service.create(ItemCreate(name="Widget"))

    assert created.name == "Widget"
    assert created.id is not None
    stored = await service.get(created.id)
    assert stored.name == "Widget"


async def test_list_returns_created_items(service: ItemService) -> None:
    await service.create(ItemCreate(name="First"))
    await service.create(ItemCreate(name="Second"))

    names = [item.name for item in await service.list()]
    assert names == ["First", "Second"]


async def test_get_missing_item_raises(service: ItemService) -> None:
    with pytest.raises(ItemNotFoundError):
        await service.get(uuid4())
