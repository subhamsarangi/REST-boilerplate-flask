from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token

from app import db, bcrypt
from app.models import User
from app.schemas import UserSchema
from app.utils import error_response, success_response

auth_bp = Blueprint('auth_bp', __name__)

user_schema = UserSchema()

@auth_bp.route('/register/', methods=['POST'])
def register():
    data = request.get_json()
    errors = user_schema.validate(data, session=db.session)
    if errors:
        return jsonify(errors), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    User.add(data['name'], data['email'], hashed_password)
    return success_response("user registered.", {}, 201)


@auth_bp.route('/login/', methods=['POST'])
def login():
    data = request.get_json()
    user = User.get_user_by_email(data['email'])
    if bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity={'id': user.id, 'is_admin': user.is_admin})
        refresh_token = create_refresh_token(identity={'id': user.id, 'is_admin': user.is_admin})
        return success_response("logged in successfully", {
            'access_token': access_token,
            'refresh_token': refresh_token
        })
    else:
        return error_response('Invalid credentials', 401)


@auth_bp.route("/profile/", methods=["GET"])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    user = User.get_user_data(current_user['id'])
    return success_response("profile fetched", user)


@auth_bp.route('/refresh/', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return success_response("token refreshed", { 'access_token': new_access_token})
