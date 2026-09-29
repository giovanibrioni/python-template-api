from uuid import uuid4

from httpx import AsyncClient


async def test_create_list_and_get_item(client: AsyncClient) -> None:
    created = await client.post("/api/v1/items", json={"name": "Widget"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Widget"
    item_id = body["id"]

    listed = await client.get("/api/v1/items")
    assert listed.status_code == 200
    assert any(item["id"] == item_id for item in listed.json())

    fetched = await client.get(f"/api/v1/items/{item_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Widget"


async def test_get_missing_item_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/items/{uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}
