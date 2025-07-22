from flask import Blueprint, jsonify, request
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.resume import (
    get_all_resumes,
    get_resume_by_id,
    get_resume_by_email,
    get_resumes_by_name,
    add_resume,
    delete_resume,
    filter_resumes
)

resume_bp = Blueprint("resume", __name__, url_prefix="/resumes")


@resume_bp.route("/", methods=["GET"])
def get_all():
    result = get_all_resumes()
    return jsonify(result), 200 if result["status"] == "success" else 404


@resume_bp.route("/<int:resume_id>", methods=["GET"])
def get_by_id(resume_id):
    result = get_resume_by_id(resume_id)
    status = 200 if result["status"] == "success" else 404
    return jsonify(result), status


@resume_bp.route("/email/<email>", methods=["GET"])
def get_by_email(email):
    result = get_resume_by_email(email)
    status = 200 if result["status"] == "success" else 404
    return jsonify(result), status


@resume_bp.route("/search", methods=["GET"])
def search_by_name():
    name = request.args.get("name")
    if not name:
        return jsonify({"status": "error", "message": "Missing 'name' query param"}), 400
    result = get_resumes_by_name(name)
    status = 200 if result["status"] == "success" else 404
    return jsonify(result), status


@resume_bp.route("/", methods=["POST"])
def create_resume():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing JSON payload"}), 400
        result = add_resume(data)
        status = 201 if result["status"] == "success" else 400
        return jsonify(result), status
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@resume_bp.route("/<int:resume_id>", methods=["DELETE"])
def delete(resume_id):
    result = delete_resume(resume_id)
    status = 200 if result["status"] == "success" else 404
    return jsonify(result), status

@resume_bp.route("/filter", methods=["GET"])
def filter_resumes():
    keyword = request.args.get("keyword")
    city = request.args.get("city")
    degree = request.args.get("degree")
    min_exp = request.args.get("min_exp")

    result = filter_resumes(keyword, city, degree, min_exp)
    status = 200 if result["status"] == "success" else 404
    return jsonify(result), status
