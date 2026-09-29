from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.items.repository import SqlAlchemyItemRepository
from app.items.schemas import ItemCreate, ItemPublic
from app.items.service import ItemService

router = APIRouter(prefix="/items", tags=["items"])


def get_item_service(session: SessionDep) -> ItemService:
    return ItemService(SqlAlchemyItemRepository(session))


ServiceDep = Annotated[ItemService, Depends(get_item_service)]


@router.post("", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate, service: ServiceDep) -> ItemPublic:
    item = await service.create(payload)
    return ItemPublic.model_validate(item)


@router.get("", response_model=list[ItemPublic])
async def list_items(service: ServiceDep) -> list[ItemPublic]:
    items = await service.list()
    return [ItemPublic.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=ItemPublic)
async def get_item(item_id: UUID, service: ServiceDep) -> ItemPublic:
    item = await service.get(item_id)
    return ItemPublic.model_validate(item)
