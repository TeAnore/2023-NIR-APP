from app import db
from app.models import User
from app.api import bp
from app.api.errors import bad_request, not_found
from flask import jsonify, request, url_for

@bp.route('/users/<int:id>/followers', methods=['GET'])
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page, 'api.get_followers', id=id)
    return jsonify(data)

@bp.route('/users/<int:id>/followed', methods=['GET'])
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page, 'api.get_followed', id=id)
    return jsonify(data)

@bp.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    name = ''
    name = request.args.get('name', type=str)
    user = User()
    if User.query.filter_by(id=id).first():
        user=User.query.filter_by(id=id).first()
        return jsonify(user.to_dict(user))
    
    external_user_id = str(id)
    if User.query.filter_by(external_user_id=external_user_id).first():
        user=User.query.filter_by(external_user_id=external_user_id).first()
        return jsonify(user.to_dict(user))
    if name:
        if User.query.filter_by(username=name).first():
            user=User.query.filter_by(username=name).first()
            return jsonify(user.to_dict(user))
        else:
            return not_found(f"User with id {id} and name {name} not found.")
    else: 
        return not_found(f"User with id {id} not found.")

@bp.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)

@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}

    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    
    if 'user_id' in data:
        data['external_user_id'] = data['user_id']

    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json() or {}

    if 'username' in data and data['username'] != user.username and User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    
    if 'email' in data and data['email'] != user.email and User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())

