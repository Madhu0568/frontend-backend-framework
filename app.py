from flask import Flask, request, jsonify
import uuid
import re
from datetime import datetime
from functools import wraps

app = Flask(__name__)

items_db = {}


class ValidationError(Exception):
    def __init__(self, message, field=None):
        self.message = message
        self.field = field


@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": e.message, "field": e.field, "type": "validation_error"}), 400


@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({"error": "Resource not found", "type": "not_found"}), 404


@app.errorhandler(500)
def handle_server_error(e):
    return jsonify({"error": "Internal server error", "type": "server_error"}), 500


def validate_required(data, fields):
    missing = [f for f in fields if f not in data or data[f] is None or str(data[f]).strip() == ""]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}", field=missing[0])


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format", field="email")


def validate_length(value, field_name, min_len=1, max_len=255):
    if len(str(value)) < min_len:
        raise ValidationError(f"{field_name} must be at least {min_len} characters", field=field_name)
    if len(str(value)) > max_len:
        raise ValidationError(f"{field_name} must be at most {max_len} characters", field=field_name)


def json_response(data, status=200, message=None):
    response = {"success": True, "data": data, "timestamp": datetime.utcnow().isoformat()}
    if message:
        response["message"] = message
    return jsonify(response), status


def require_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json", "type": "invalid_content_type"}), 415
        return f(*args, **kwargs)
    return decorated


@app.route("/api/items", methods=["POST"])
@require_json
def create_item():
    data = request.get_json()
    validate_required(data, ["name"])
    validate_length(data["name"], "name", min_len=2, max_len=100)

    if "email" in data and data["email"]:
        validate_email(data["email"])

    item_id = str(uuid.uuid4())[:8]
    item = {
        "id": item_id,
        "name": data["name"].strip(),
        "description": data.get("description", "").strip(),
        "email": data.get("email", "").strip(),
        "category": data.get("category", "general").strip(),
        "tags": data.get("tags", []),
        "metadata": data.get("metadata", {}),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    items_db[item_id] = item
    return json_response(item, status=201, message="Item created successfully")


@app.route("/api/items", methods=["GET"])
def list_items():
    category = request.args.get("category")
    search = request.args.get("search", "").lower()
    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    items = list(items_db.values())

    if category:
        items = [i for i in items if i["category"] == category]
    if search:
        items = [i for i in items if search in i["name"].lower() or search in i["description"].lower()]

    reverse = order == "desc"
    items.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = items[start:end]

    return json_response({
        "items": paginated,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }
    })


@app.route("/api/items/<item_id>", methods=["GET"])
def get_item(item_id):
    item = items_db.get(item_id)
    if not item:
        return jsonify({"error": "Item not found", "type": "not_found"}), 404
    return json_response(item)


@app.route("/api/items/<item_id>", methods=["PUT"])
@require_json
def update_item(item_id):
    item = items_db.get(item_id)
    if not item:
        return jsonify({"error": "Item not found", "type": "not_found"}), 404

    data = request.get_json()

    if "name" in data:
        validate_length(data["name"], "name", min_len=2, max_len=100)
        item["name"] = data["name"].strip()
    if "description" in data:
        item["description"] = data["description"].strip()
    if "email" in data and data["email"]:
        validate_email(data["email"])
        item["email"] = data["email"].strip()
    if "category" in data:
        item["category"] = data["category"].strip()
    if "tags" in data:
        item["tags"] = data["tags"]
    if "metadata" in data:
        item["metadata"] = data["metadata"]

    item["updated_at"] = datetime.utcnow().isoformat()
    return json_response(item, message="Item updated successfully")


@app.route("/api/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = items_db.pop(item_id, None)
    if not item:
        return jsonify({"error": "Item not found", "type": "not_found"}), 404
    return json_response({"id": item_id}, message="Item deleted successfully")


@app.route("/api/items/batch", methods=["POST"])
@require_json
def batch_create():
    data = request.get_json()
    if "items" not in data:
        raise ValidationError("items array is required")

    created = []
    errors = []
    for i, item_data in enumerate(data["items"]):
        try:
            validate_required(item_data, ["name"])
            validate_length(item_data["name"], "name", min_len=2, max_len=100)

            item_id = str(uuid.uuid4())[:8]
            item = {
                "id": item_id,
                "name": item_data["name"].strip(),
                "description": item_data.get("description", "").strip(),
                "category": item_data.get("category", "general").strip(),
                "tags": item_data.get("tags", []),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            items_db[item_id] = item
            created.append(item)
        except ValidationError as e:
            errors.append({"index": i, "error": e.message})

    return json_response({
        "created": len(created),
        "errors": len(errors),
        "items": created,
        "error_details": errors,
    }, status=201, message=f"Batch complete: {len(created)} created, {len(errors)} errors")


@app.route("/api/stats", methods=["GET"])
def get_stats():
    items = list(items_db.values())
    categories = {}
    for item in items:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return json_response({
        "total_items": len(items),
        "categories": categories,
        "category_count": len(categories),
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5004)
