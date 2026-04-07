import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_conversations_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversations"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient) -> None:
    resp = await client.post("/api/conversations", json={"title": "Test Chat"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Chat"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_and_list(client: AsyncClient) -> None:
    await client.post("/api/conversations", json={"title": "Chat A"})
    await client.post("/api/conversations", json={"title": "Chat B"})
    resp = await client.get("/api/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["conversations"]) == 2


@pytest.mark.asyncio
async def test_get_conversation(client: AsyncClient) -> None:
    create_resp = await client.post("/api/conversations", json={"title": "Detail Test"})
    conv_id = create_resp.json()["id"]

    resp = await client.get(f"/api/conversations/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == conv_id
    assert data["title"] == "Detail Test"
    assert data["messages"] == []


@pytest.mark.asyncio
async def test_get_conversation_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/conversations/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_title(client: AsyncClient) -> None:
    create_resp = await client.post("/api/conversations", json={"title": "Old Title"})
    conv_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/conversations/{conv_id}", json={"title": "New Title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_conversation(client: AsyncClient) -> None:
    create_resp = await client.post("/api/conversations", json={"title": "To Delete"})
    conv_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/conversations/{conv_id}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/conversations/{conv_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_not_found(client: AsyncClient) -> None:
    resp = await client.delete("/api/conversations/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_ordered_by_most_recent(client: AsyncClient) -> None:
    await client.post("/api/conversations", json={"title": "First"})
    await client.post("/api/conversations", json={"title": "Second"})

    list_resp = await client.get("/api/conversations")
    titles = [c["title"] for c in list_resp.json()["conversations"]]
    assert titles[0] == "Second"
    assert titles[1] == "First"
