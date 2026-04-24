from flask import Blueprint, jsonify, request, Response
import csv
import io
from datetime import datetime, timezone
from app import db
from app.models import Asset, AuditLog

assets_bp = Blueprint("assets", __name__, url_prefix="/api")

PER_PAGE = 10


@assets_bp.route("/assets", methods=["GET"])
def list_assets():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    asset_type = request.args.get("type", "").strip()
    status = request.args.get("status", "").strip()

    query = Asset.query

    if search:
        query = query.filter(Asset.name.ilike(f"%{search}%"))

    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)

    if status:
        query = query.filter(Asset.status == status)

    total = query.count()

    offset = (page - 1) * PER_PAGE
    assets = query.order_by(Asset.name).offset(offset).limit(PER_PAGE).all()

    return jsonify(
        {
            "assets": [a.to_dict() for a in assets],
            "total": total,
            "page": page,
            "per_page": PER_PAGE,
            "pages": max(1, (total + PER_PAGE - 1) // PER_PAGE),
        }
    )


@assets_bp.route("/assets/<int:asset_id>", methods=["GET"])
def get_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    return jsonify(asset.to_dict())


@assets_bp.route("/assets/<int:asset_id>/audit", methods=["GET"])
def get_asset_audit(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    logs = (
        AuditLog.query.filter_by(asset_id=asset_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return jsonify({"audit_logs": [log.to_dict() for log in logs]})


@assets_bp.route("/assets/export", methods=["GET"])
def export_assets():
    search = request.args.get("search", "").strip()
    asset_type = request.args.get("type", "").strip()
    status = request.args.get("status", "").strip()

    query = Asset.query

    if search:
        query = query.filter(Asset.name.ilike(f"%{search}%"))
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if status:
        query = query.filter(Asset.status == status)

    assets = query.order_by(Asset.name).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Name",
            "Type",
            "Serial Number",
            "Status",
            "Client",
            "Assigned To",
            "Last Seen",
            "Notes",
            "Created At",
        ]
    )

    for a in assets:
        writer.writerow(
            [
                a.id,
                a.name,
                a.asset_type,
                a.serial_number or "",
                a.status,
                a.client.name if a.client else "",
                a.assigned_to or "",
                a.last_seen.isoformat() if a.last_seen else "",
                a.notes or "",
                a.created_at.isoformat(),
            ]
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=assets-{today}.csv"},
    )


@assets_bp.route("/assets", methods=["POST"])
def create_asset():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    required_fields = ["name", "asset_type", "client_id"]
    missing = [f for f in required_fields if f not in data or not data[f]]
    if missing:
        return jsonify({"error": f'Missing required fields: {", ".join(missing)}'}), 400

    name = data["name"]
    asset_type = data["asset_type"]
    client_id = data["client_id"]

    asset = Asset(
        name=name,
        asset_type=asset_type,
        client_id=client_id,
        serial_number=data.get("serial_number"),
        assigned_to=data.get("assigned_to"),
        notes=data.get("notes"),
        status=data.get("status", "active"),
    )
    db.session.add(asset)
    db.session.commit()
    return jsonify(asset.to_dict()), 201


@assets_bp.route("/assets/<int:asset_id>", methods=["PUT"])
def update_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    if "name" in data:
        asset.name = data["name"]
    if "asset_type" in data:
        asset.asset_type = data["asset_type"]
    if "serial_number" in data:
        asset.serial_number = data["serial_number"]
    if "assigned_to" in data:
        asset.assigned_to = data["assigned_to"]
    if "notes" in data:
        asset.notes = data["notes"]
    if "client_id" in data:
        asset.client_id = data["client_id"]

    db.session.commit()
    return jsonify(asset.to_dict())


@assets_bp.route("/assets/<int:asset_id>", methods=["DELETE"])
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    return jsonify({"message": "Asset deleted"}), 200


@assets_bp.route("/assets/<int:asset_id>/toggle", methods=["POST"])
def toggle_asset_status(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    previous_status = asset.status

    if asset.status == "active":
        asset.status = "inactive"
    elif asset.status == "inactive":
        asset.status = "active"
    # retired assets cannot be toggled further

    if asset.status != previous_status:
        log = AuditLog(
            asset_id=asset.id,
            previous_status=previous_status,
            new_status=asset.status,
            requester_ip=request.remote_addr,
        )
        db.session.add(log)

    db.session.commit()
    return jsonify(asset.to_dict())


@assets_bp.route("/assets/<int:asset_id>/decommission", methods=["POST"])
def decommission_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if asset.status == "retired":
        return jsonify({"error": "Asset is already retired"}), 400
    previous_status = asset.status
    asset.status = "retired"

    log = AuditLog(
        asset_id=asset.id,
        previous_status=previous_status,
        new_status="retired",
        requester_ip=request.remote_addr,
    )
    db.session.add(log)

    db.session.commit()
    return jsonify(asset.to_dict())
