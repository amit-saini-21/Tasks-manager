from flask import Blueprint, jsonify, request
from utils import jwt_handler
import models

notes_bp = Blueprint("notes", __name__)
db = models.notes_repo


def _validate_note_payload(payload):
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    if not title or not content:
        return None, None
    return title, content


def _parse_id_list(raw_ids):
    if not isinstance(raw_ids, list) or not raw_ids:
        return None
    parsed_ids = []
    for value in raw_ids:
        if not isinstance(value, int) or value <= 0:
            return None
        parsed_ids.append(value)
    return list(dict.fromkeys(parsed_ids))

@notes_bp.route('/api/notes', methods=['GET'])
@jwt_handler.token_required
def get_notes(current_user):
    notes = db.find_notes_by_user_id(current_user["id"]) or []
    return jsonify(
        {
            "notes": notes,
            "owner": current_user["username"],
        }
    ), 200


@notes_bp.route('/api/notes', methods=['POST'])
@jwt_handler.token_required
def create_note(current_user):
    payload = request.get_json(silent=True) or {}
    title, content = _validate_note_payload(payload)

    if not title or not content:
        return jsonify({"error": "title and content are required"}), 400

    notes_data = {
        "title": title,
        "content": content,
        "user_id": current_user["id"],
    }

    saved_note = db.save_notes(notes_data)
    return jsonify({"message": "Note created successfully", "note": saved_note}), 201

@notes_bp.route('/api/notes/<int:note_id>', methods=['PUT', 'DELETE'])
@jwt_handler.token_required
def modify_note(current_user, note_id):
    if request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        title, content = _validate_note_payload(payload)

        if not title or not content:
            return jsonify({"error": "title and content are required"}), 400

        note_data = {
            "id": note_id,
            "title": title,
            "content": content,
            "user_id": current_user["id"],
        }
        updated_note = db.update_note(note_data)
        if updated_note:
            return jsonify({"message": "Note updated successfully", "note": updated_note}), 200
        else:
            return jsonify({"error": "Note not found or unauthorized"}), 404

    if request.method == 'DELETE':
        deleted = db.delete_note(note_id, current_user["id"])
        if deleted:
            return jsonify({"message": "Note deleted successfully"}), 200
        else:
            return jsonify({"error": "Note not found or unauthorized"}), 404

    return jsonify({"error": "Method not allowed"}), 405

@notes_bp.route('/api/notes/bulk', methods = ['DELETE'])
@jwt_handler.token_required
def bulk_delete_notes(current_user):
    payload = request.get_json(silent=True) or {}
    note_ids = _parse_id_list(payload.get("note_ids"))

    if note_ids is None:
        return jsonify({"error": "note_ids must be a non-empty list of positive integer IDs"}), 400
    
    deleted_ids = db.bulk_delete_notes(note_ids, current_user["id"])
    return jsonify({"message": f"{len(deleted_ids)} notes deleted successfully", "deleted_ids": deleted_ids}), 200

