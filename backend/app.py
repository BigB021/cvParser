from flask import Flask

from routes.router import resume_bp

app = Flask(__name__)

app.register_blueprint(resume_bp)


@app.route("/")
def home():
    return "yaw yaw"


if __name__ == "__main__":
    app.run(debug=True)


