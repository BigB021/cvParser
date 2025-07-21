from flask import Blueprint, render_template, redirect

test_bp = Blueprint("test",__name__,template_folder="templates")

@test_bp.route("/")
def test_home():
    return "test yaw yaw"

@test_bp.route("/test/<name>")
def test_home2(name):
    return f"test yaw yaw {name}"

