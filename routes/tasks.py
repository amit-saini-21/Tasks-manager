from flask import Blueprint, jsonify, request
import models
from utils import jwt_handler
import datetime

tasks_bp = Blueprint("tasks", __name__)
db = models.tasks_repo

ALLOWED_TASK_STATUSES = {"pending", "in_progress", "completed"}


def _parse_due_date(raw_due_date, default_to_tomorrow=True):
    if raw_due_date in (None, ""):
        if default_to_tomorrow:
            return (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).date()
        return None

    if isinstance(raw_due_date, datetime.date):
        return raw_due_date

    if isinstance(raw_due_date, str):
        candidate = raw_due_date.strip()
        if not candidate:
            return (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).date()
        try:
            return datetime.date.fromisoformat(candidate)
        except ValueError:
            return None

    return None


def _parse_id_list(raw_ids):
    if not isinstance(raw_ids, list) or not raw_ids:
        return None

    parsed_ids = []
    for value in raw_ids:
        if not isinstance(value, int) or value <= 0:
            return None
        parsed_ids.append(value)
    return list(dict.fromkeys(parsed_ids))

@tasks_bp.route('/api/tasks', methods=['GET'])
@jwt_handler.token_required
def get_tasks(current_user):
    tasks = db.find_tasks_by_user_id(current_user["id"]) or []
    return jsonify(
        {
            "tasks": tasks,
            "owner": current_user["username"]
        }), 200

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_handler.token_required
def get_task(current_user, task_id):
    task = db.find_task_by_id(task_id,current_user["id"])
    if task:
        return jsonify({"task": task}), 200
    else:
        return jsonify({"error": "Task not found or unauthorized"}), 404
    

@tasks_bp.route('/api/tasks', methods=['POST'])
@jwt_handler.token_required
def create_task(current_user):
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    due_date = _parse_due_date(payload.get("due_date"), default_to_tomorrow=True)
    status = payload.get("status") or "pending"

    if not title or not description:
        return jsonify({"error": "title and description are required"}), 400
    if due_date is None:
        return jsonify({"error": "due_date must be a valid ISO date string (YYYY-MM-DD)"}), 400
    if status not in ALLOWED_TASK_STATUSES:
        return jsonify({"error": "status must be one of pending, in_progress, completed"}), 400

    task_data = {
        "title": title,
        "description": description,
        "user_id": current_user["id"],
        "due_date": due_date,
        "status": status,
    }

    saved_task = db.save_task(task_data)
    return jsonify({"message": "Task created successfully", "task": saved_task}), 201

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@jwt_handler.token_required
def modify_task(current_user, task_id):
    if request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        title = (payload.get("title") or "").strip()
        description = (payload.get("description") or "").strip()
        existing_task = db.find_task_by_id(task_id, current_user["id"])
        if not existing_task:
            return jsonify({"error": "Task not found or unauthorized"}), 404

        due_date = _parse_due_date(payload.get("due_date"), default_to_tomorrow=False)
        status = payload.get("status") or existing_task.get("status", "pending")

        if not title or not description:
            return jsonify({"error": "title and description are required"}), 400
        if payload.get("due_date") is not None and due_date is None:
            return jsonify({"error": "due_date must be a valid ISO date string (YYYY-MM-DD)"}), 400
        if status not in ALLOWED_TASK_STATUSES:
            return jsonify({"error": "status must be one of pending, in_progress, completed"}), 400

        task_data = {
            "id": task_id,
            "title": title,
            "description": description,
            "user_id": current_user["id"],
            "due_date": due_date if due_date is not None else existing_task.get("due_date"),
            "status": status
        }
        updated_task = db.update_task(task_data)
        if updated_task:
            return jsonify({"message": "Task updated successfully", "task": updated_task}), 200
        else:
            return jsonify({"error": "Task not found or unauthorized"}), 404
    if request.method == 'DELETE':
        deleted = db.delete_task(task_id, current_user["id"])
        if deleted:
            return jsonify({"message": "Task deleted successfully"}), 200
        else:
            return jsonify({"error": "Task not found or unauthorized"}), 404
        
    return jsonify({"error": "Invalid request method"}), 405

@tasks_bp.route('/api/tasks/bulk', methods = ['DELETE'])
@jwt_handler.token_required
def bulk_delete_tasks(current_user):
    payload = request.get_json(silent=True) or {}

    task_ids = _parse_id_list(payload.get("task_ids"))

    if task_ids is None:
        return jsonify({"error": "task_ids must be a non-empty list of positive integer IDs"}), 400

    deleted_ids = db.bulk_delete_tasks(task_ids, current_user["id"])
    return jsonify({"message": f"{len(deleted_ids)} tasks deleted successfully", "deleted_ids": deleted_ids}), 200