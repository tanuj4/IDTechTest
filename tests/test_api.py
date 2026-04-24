"""
API test suite for NetTrack.

Some tests are already written to demonstrate the testing patterns used here.
The TODOs are yours to complete as part of the assessment.
"""

import json


# ---------------------------------------------------------------------------
# Assets — list / read
# ---------------------------------------------------------------------------


def test_get_assets_returns_list(flask_client):
    """GET /api/assets returns a paginated list with the expected fields."""
    response = flask_client.get("/api/assets")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "assets" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    assert isinstance(data["assets"], list)


def test_get_assets_pagination_metadata(flask_client):
    """Pagination metadata reflects the actual number of records in the database."""
    response = flask_client.get("/api/assets")
    data = json.loads(response.data)

    # The test database is seeded with 12 assets (see conftest.py)
    assert data["total"] == 12
    assert data["page"] == 1
    assert data["per_page"] == 10


def test_get_single_asset(flask_client):
    """GET /api/assets/<id> returns the correct asset."""
    response = flask_client.get("/api/assets/1")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["id"] == 1
    assert "name" in data
    assert "status" in data
    assert "asset_type" in data


def test_get_asset_not_found(flask_client):
    """GET /api/assets/<id> returns 404 for a nonexistent asset."""
    response = flask_client.get("/api/assets/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Assets — create
# ---------------------------------------------------------------------------


def test_create_asset_success(flask_client):
    """POST /api/assets with valid data creates a new asset and returns 201."""
    payload = {
        "name": "New Test Workstation",
        "asset_type": "workstation",
        "client_id": 1,
        "serial_number": "TST-WS-999",
    }
    response = flask_client.post(
        "/api/assets",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["name"] == "New Test Workstation"
    assert data["status"] == "active"


def test_create_asset_missing_fields(flask_client):
    """POST /api/assets with required fields missing should return 400."""
    response = flask_client.post(
        "/api/assets",
        data=json.dumps({"name": "Incomplete Asset"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "asset_type" in data["error"]
    assert "client_id" in data["error"]


# ---------------------------------------------------------------------------
# Assets — toggle status
# ---------------------------------------------------------------------------


def test_toggle_active_asset_becomes_inactive(flask_client):
    """Toggling an active asset should set its status to 'inactive'."""
    response = flask_client.post("/api/assets/1/toggle")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "inactive"


def test_toggle_inactive_asset_becomes_active(flask_client):
    """Toggling an inactive asset should restore it to 'active'."""
    # Asset 2 is seeded with status='inactive'
    response = flask_client.post("/api/assets/2/toggle")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "active"


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------


def test_get_clients(flask_client):
    """GET /api/clients returns all clients."""
    response = flask_client.get("/api/clients")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "clients" in data
    assert len(data["clients"]) == 2


def test_get_client_includes_assets(flask_client):
    """GET /api/clients/<id> includes the client's assets in the response."""
    response = flask_client.get("/api/clients/1")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "assets" in data
    assert isinstance(data["assets"], list)
    assert len(data["assets"]) > 0


def test_delete_client_with_assets_fails(flask_client):
    """Deleting a client with assigned assets should return 400."""
    response = flask_client.delete("/api/clients/1")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "asset" in data["error"].lower()


# ---------------------------------------------------------------------------
# Additional tests — bug fixes, features, edge cases
# ---------------------------------------------------------------------------


def test_pagination_page_two_returns_different_records(flask_client):
    """Page 2 returns different records than page 1 (bug fix verification)."""
    page1 = json.loads(flask_client.get("/api/assets?page=1").data)
    page2 = json.loads(flask_client.get("/api/assets?page=2").data)
    assert len(page1["assets"]) == 10
    assert len(page2["assets"]) == 2
    page1_ids = {a["id"] for a in page1["assets"]}
    page2_ids = {a["id"] for a in page2["assets"]}
    assert page1_ids.isdisjoint(page2_ids)


def test_search_partial_match(flask_client):
    """Search matches partial, case-insensitive names (bug fix verification)."""
    response = flask_client.get("/api/assets?search=work")
    data = json.loads(response.data)
    assert data["total"] > 0
    for asset in data["assets"]:
        assert "work" in asset["name"].lower()


def test_toggle_retired_asset_stays_retired(flask_client):
    """Toggling a retired asset should not change its status."""
    response = flask_client.post("/api/assets/5/toggle")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "retired"


def test_null_last_seen_returns_null(flask_client):
    """Assets with null last_seen return null in API (bug fix verification)."""
    response = flask_client.get("/api/assets/5")
    assert response.status_code == 200
    assert json.loads(response.data)["last_seen"] is None


def test_toggle_creates_audit_log(flask_client):
    """Toggling an asset creates an audit log entry (feature verification)."""
    flask_client.post("/api/assets/1/toggle")
    response = flask_client.get("/api/assets/1/audit")
    data = json.loads(response.data)
    assert len(data["audit_logs"]) == 1
    assert data["audit_logs"][0]["previous_status"] == "active"
    assert data["audit_logs"][0]["new_status"] == "inactive"


def test_decommission_already_retired_returns_400(flask_client):
    """Decommissioning an already retired asset returns 400."""
    response = flask_client.post("/api/assets/5/decommission")
    assert response.status_code == 400
    assert "already retired" in json.loads(response.data)["error"]


def test_export_csv_returns_all_assets(flask_client):
    """CSV export returns header + all assets."""
    response = flask_client.get("/api/assets/export")
    assert response.status_code == 200
    assert "text/csv" in response.content_type
    lines = response.data.decode().strip().split("\n")
    assert len(lines) == 13  # header + 12 assets
