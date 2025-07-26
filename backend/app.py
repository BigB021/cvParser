from flask import Flask
from flask_cors import CORS

from routes.router import resume_bp

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = "/home/youssef/Desktop/menara-holdings/cvParser/backend/temp"

app.register_blueprint(resume_bp)


# @app.route("/")
# def home():
#     return "yaw yaw"


if __name__ == "__main__":
    app.run(debug=True)


