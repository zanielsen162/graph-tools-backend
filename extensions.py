from flask_jwt_extended import JWTManager
from authlib.integrations.flask_client import OAuth

jwt = JWTManager()
oauth = OAuth()