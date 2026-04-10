from flask import Blueprint, jsonify, request
import models
from utils import jwt_handler
import datetime
tasks_bp = Blueprint("tasks", __name__)
db = models.tasks_repo

@tasks_bp.route('/api/tasks', methods=['GET'])
@jwt_handler.token_required
def get_tasks(current_user):
    tasks = db.find_tasks_by_user_id(current_user["id"]) or []
    return jsonify(
        {
            "tasks": tasks,
            "Owner": current_user["username"]
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
    payload = request.get_json() or {}
    title = payload.get("title")
    description = payload.get("description")
    due_date = payload.get("due_date")

    if not due_date:
        due_date = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    if not title or not description:
        return jsonify({"error": "title and description are required"}), 400

    task_data = {
        "title": title,
        "description": description,
        "user_id": current_user["id"],
        "due_date": due_date,
    }

    saved_task = db.save_task(task_data)
    return jsonify({"message": "Task created successfully", "task": saved_task}), 201

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@jwt_handler.token_required
def modify_task(current_user, task_id):
    if request.method == 'PUT':
        payload = request.get_json() or {}
        title = payload.get("title")
        description = payload.get("description")
        due_date = payload.get("due_date")
        status = payload.get("status")
        if not title or not description:
            return jsonify({"error": "title and description are required"}), 400

        task_data = {
            "id": task_id,
            "title": title,
            "description": description,
            "user_id": current_user["id"],
            "due_date": due_date,
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
    payload = request.get_json()

    task_ids = payload.get("task_ids")

    if not task_ids or not isinstance(task_ids, list):
        return jsonify({"error": "task_ids must be a list of IDs"}), 400

    deleted_count = db.bulk_delete_tasks(task_ids, current_user["id"])
    return jsonify({"message": f"{deleted_count} tasks deleted successfully"}), 200