import json
import os

from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import BaseChallenge
from flask import Blueprint
from .blueprint import load_bp
from .models import WriteUpChallenges

PLUGIN_PATH = os.path.dirname(__file__)
with open(f"{PLUGIN_PATH}/config.json", 'r') as fd:
    CONFIG = json.load(fd)


# class WriteUpChallenge(BaseChallenge):
#     id = "writeup"  # Unique identifier used to register challenges
#     name = "Write-Up"  # Name of a challenge type
#     templates = {  # Templates used for each aspect of challenge editing & viewing
#         "create": "/plugins/challenges/assets/create.html",
#         "update": "/plugins/challenges/assets/update.html",
#         "view": "/plugins/challenges/assets/view.html",
#     }
#     scripts = {  # Scripts that are loaded when a template is loaded
#         "create": "/plugins/challenges/assets/create.js",
#         "update": "/plugins/challenges/assets/update.js",
#         "view": "/plugins/challenges/assets/view.js",
#     }
#     # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
#     route = "/plugins/challenges/assets/"
#     # Blueprint used to access the static_folder directory.
#     blueprint = Blueprint(
#         "standard", __name__, template_folder="templates", static_folder="assets"
#     )
#     challenge_model = WriteUpChallenges


def load(app):
    app.db.create_all()
    register_plugin_assets_directory(app, base_path=f"{PLUGIN_PATH}/assets")

    bp = load_bp(CONFIG["route"], CONFIG["base_route"], PLUGIN_PATH)
    app.register_blueprint(bp)

    print("Write-Ups plugin is ready!")
