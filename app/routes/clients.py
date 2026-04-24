from flask import Blueprint, jsonify, request
from app import db
from app.models import Client, Asset

clients_bp = Blueprint("clients", __name__, url_prefix="/api")


@clients_bp.route("/clients", methods=["GET"])
def list_clients():
    clients = Client.query.order_by(Client.name).all()
    return jsonify({"clients": [c.to_dict() for c in clients]})


@clients_bp.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify(client.to_dict(include_assets=True))


@clients_bp.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json()
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Client name is required"}), 400

    name = data["name"].strip()[:200]
    contact_email = data.get("contact_email")
    phone = data.get("phone")

    if contact_email and not isinstance(contact_email, str):
        return jsonify({"error": "contact_email must be a string"}), 400
    if contact_email:
        contact_email = contact_email.strip()[:200]

    if phone and not isinstance(phone, str):
        return jsonify({"error": "phone must be a string"}), 400
    if phone:
        phone = phone.strip()[:50]

    client = Client(
        name=name,
        contact_email=contact_email,
        phone=phone,
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(client.to_dict()), 201


@clients_bp.route("/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    if "name" in data:
        name = data["name"].strip()[:200] if isinstance(data["name"], str) else ""
        if not name:
            return jsonify({"error": "Client name cannot be empty"}), 400
        client.name = name
    if "contact_email" in data:
        client.contact_email = (
            data["contact_email"].strip()[:200]
            if isinstance(data["contact_email"], str)
            else None
        )
    if "phone" in data:
        client.phone = (
            data["phone"].strip()[:50] if isinstance(data["phone"], str) else None
        )

    db.session.commit()
    return jsonify(client.to_dict())


@clients_bp.route("/clients/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)

    if client.assets:
        return (
            jsonify(
                {
                    "error": f"Cannot delete client with {len(client.assets)} assigned asset(s). Reassign or remove them first."
                }
            ),
            400,
        )

    db.session.delete(client)
    db.session.commit()
    return jsonify({"message": "Client deleted"}), 200
