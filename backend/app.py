from flask import Flask

from routes.test_route import test_bp

app = Flask(__name__)

app.register_blueprint(test_bp)


@app.route("/")
def home():
    return "yaw yaw"


if __name__ == "__main__":
    app.run(debug=True)


