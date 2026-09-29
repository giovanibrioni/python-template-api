from uuid import UUID

from app.core.exceptions import AppError


class ItemNotFoundError(AppError):
    def __init__(self, item_id: UUID) -> None:
        self.item_id = item_id
        super().__init__(f"Item not found: {item_id}")
