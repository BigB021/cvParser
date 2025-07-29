from flask import Blueprint, jsonify, request, current_app, send_from_directory
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser.cv_parser import process_and_store_resume
from models.resume import (
    get_all_resumes,
    get_resume_by_id,
    get_resume_by_email,
    get_resumes_by_name,
    add_resume,
    delete_resume,
    apply_filters
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
    if result["status"] == "error":
        return jsonify(result), 404
    return jsonify(result), 200


@resume_bp.route("/filter", methods=["GET"])
def filter_resumes():
    keyword = request.args.get("keyword")
    city = request.args.get("city")
    degree = request.args.get("degree")
    skill = request.args.get("skill") 
    min_exp = request.args.get("min_exp")

    result = apply_filters(keyword, city, degree, skill, min_exp)
    status = 200 if result["status"] == "success" else 404
    return jsonify(result), status


@resume_bp.route("/upload", methods=["POST"])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    # Save file temporarily
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file.save(upload_path)

    # Process and store resume
    try:
        data = process_and_store_resume(upload_path)
        #os.remove(upload_path)
        return jsonify({"status": "success", "data": data}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Serve the pdf folder as static files 
@resume_bp.route("/pdfs/<path:filename>", methods=["GET"])
def serve_pdf(filename):
    return send_from_directory('pdfs', filename)