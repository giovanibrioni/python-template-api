from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.items.models import Item
from app.items.repository import SqlAlchemyItemRepository


async def test_add_get_and_list(session: AsyncSession) -> None:
    repository = SqlAlchemyItemRepository(session)
    created = await repository.add(Item(name="Widget"))

    fetched = await repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Widget"
    assert fetched.created_at is not None

    items = await repository.list_all()
    assert [item.id for item in items] == [created.id]


async def test_get_by_id_missing(session: AsyncSession) -> None:
    repository = SqlAlchemyItemRepository(session)
    assert await repository.get_by_id(uuid4()) is None
