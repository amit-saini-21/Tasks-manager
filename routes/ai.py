from flask import Blueprint, request, jsonify
import os
from utils import jwt_handler
import models
from google import genai


ai_bp = Blueprint("ai",__name__)

tasks_db = models.tasks_repo
notes_db = models.notes_repo

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

_api_key = os.getenv("GEMINI_API_KEY") 
client = genai.Client(api_key=_api_key) if _api_key else None


def _call_model(prompt):
    if client is None:
        return None, jsonify({"error": "GEMINI_API_KEY is not configured"}), 500

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt
        )
        ai_output = getattr(response, "text", None)
        if not ai_output:
            return None, jsonify({"error": "No AI output returned"}), 502
        return ai_output, None, None
    except Exception as e:
        error_text = str(e)
        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text or "quota" in error_text.lower():
            return (
                None,
                jsonify(
                    {
                        "error": "AI quota exceeded",
                        "details": "Your Gemini API project has no remaining quota or billing is not enabled.",
                        "next_steps": [
                            "Enable billing and quota in Google AI Studio / Google Cloud project.",
                            "Wait for retry window or lower request rate.",
                            "Use a different API key/project with available quota."
                        ],
                        "docs": "https://ai.google.dev/gemini-api/docs/rate-limits"
                    }
                ),
                429,
            )
        return None, jsonify({"error": error_text}), 500


def _get_user_context(user_id):
    user_notes = notes_db.find_notes_by_user_id(user_id) or []
    user_tasks = tasks_db.find_tasks_by_user_id(user_id) or []
    pending_tasks = [task for task in user_tasks if str(task.get("status", "")).lower() == "pending"]
    return {
        "notes_count": len(user_notes),
        "tasks_count": len(user_tasks),
        "pending_count": len(pending_tasks),
        "recent_task_titles": [task.get("title") for task in user_tasks[:5] if task.get("title")],
    }

@ai_bp.route('/api/ai/suggest', methods = ['POST'])
@jwt_handler.token_required
def ai_suggest(current_user):
    payload = request.get_json() or {}
    user_input = payload.get('data')
    if not user_input:
        return jsonify({"error": "Input data is required"}), 400

    context = _get_user_context(current_user["id"])
    prompt = (
        "You are a productivity assistant for a notes and tasks app. "
        "Give practical and concise advice with numbered steps and no fluff.\n"
        f"User stats: notes={context['notes_count']}, tasks={context['tasks_count']}, "
        f"pending={context['pending_count']}.\n"
        f"Recent tasks: {context['recent_task_titles']}\n"
        f"User request: {user_input}"
    )

    ai_output, error_response, status_code = _call_model(prompt)
    if error_response is not None:
        return error_response, status_code

    return jsonify({"suggestion": ai_output, "model": DEFAULT_MODEL}), 200


@ai_bp.route('/api/ai/notes/suggest', methods=['POST'])
@jwt_handler.token_required
def suggest_note_improvement(current_user):
    payload = request.get_json() or {}
    title = payload.get("title", "")
    content = payload.get("content", "")
    tone = payload.get("tone", "professional")

    if not content:
        return jsonify({"error": "content is required"}), 400

    prompt = (
        "Improve the following note for clarity and actionability. "
        "Keep the response short and structured with these sections: "
        "1) Better Title 2) Improved Note 3) Key Takeaways 4) Next Actions.\n"
        f"Tone: {tone}\n"
        f"Current title: {title}\n"
        f"Current content: {content}"
    )

    ai_output, error_response, status_code = _call_model(prompt)
    if error_response is not None:
        return error_response, status_code

    return jsonify({"suggestion": ai_output, "model": DEFAULT_MODEL}), 200


@ai_bp.route('/api/ai/tasks/suggest', methods=['POST'])
@jwt_handler.token_required
def suggest_task_plan(current_user):
    payload = request.get_json() or {}
    title = payload.get("title", "")
    description = payload.get("description", "")
    due_date = payload.get("due_date", "")

    if not title:
        return jsonify({"error": "title is required"}), 400

    user_tasks = tasks_db.find_tasks_by_user_id(current_user["id"]) or []
    active_tasks = [
        task for task in user_tasks
        if str(task.get("status", "pending")).lower() in ("pending", "in_progress")
    ]
    workload_titles = [task.get("title") for task in active_tasks[:8] if task.get("title")]

    prompt = (
        "Create a practical execution plan for this task. "
        "Return short, actionable output with sections: "
        "1) Priority (low/medium/high) 2) Step-by-step plan 3) Risks 4) Time estimate 5) First action now.\n"
        f"Task title: {title}\n"
        f"Task description: {description}\n"
        f"Due date: {due_date}\n"
        f"Current active tasks (for workload context): {workload_titles}"
    )

    ai_output, error_response, status_code = _call_model(prompt)
    if error_response is not None:
        return error_response, status_code

    return jsonify({"suggestion": ai_output, "model": DEFAULT_MODEL}), 200