from app import db
from app.service import logic
from app.models import User, Task
from app.logger import Logger
from app.api import bp
from app.api.errors import bad_request, not_found, error_response
from flask import request, jsonify, url_for
from psycopg2.errors import IntegrityConstraintViolation, RestrictViolation, NotNullViolation, ForeignKeyViolation, UniqueViolation, CheckViolation, ExclusionViolation, InvalidCursorState

log = Logger()
service = logic.Service()

@bp.route('/tasks/<int:id>', methods=['GET'])
def get_task(id):
    return jsonify(Task.query.get_or_404(id).to_dict())

@bp.route('/tasks', methods=['GET'])
def get_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Task.to_collection_dict(Task.query, page, per_page, 'api.get_tasks')
    return jsonify(data)

@bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json() or {}
    print(f"Create task data: {data}")

    if 'user_id' not in data or 'url' not in data or 'reaction' not in data:
        return bad_request('must include user_id, url and reaction fields')

    try:
        task = Task()
        user = User()
        user_id = str(data['user_id'])
        user = User.query.filter_by(external_user_id=user_id).first()
        user.to_dict(user)
        data['user_id'] = user.id
        data['platform_type'] = service.get_platform_type(data['platform'], data['url'])

        if user:
            task = Task.query.filter_by(user_id=data['user_id'], url=data['url']).first()
            if task:
                task.from_dict(data, new_task=False)
                db.session.commit()
                log.msg_log(f"Update user_id:{user.id} task_id: {task.id}")
            else:
                task.from_dict(data, new_task=True)
                db.session.add(task)
                db.session.commit()
                log.msg_log(f"Create user_id:{user.id} task_id: {task.id}")

            response = jsonify(task.to_dict())
            response.status_code = 201
            response.headers['Location'] = url_for('api.get_task', id=task.id)

            return response            

        else:
            return not_found(f"User with id: {user_id} not found.")

    except Exception as error:
        log.error_log(f"Error on task creating: {error}")
        return bad_request(f"Error on task creating: {error}")

@bp.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    data = request.get_json() or {}
    print(f"Update task data: {data}")

    try:
        task = Task()        
        task = Task.query.filter_by(id=id).first()
        if task:
            task.from_dict(data, new_task=False)
            db.session.commit()
            return jsonify(task.to_dict())
        else:
            return not_found(f"Task with id: {id} not found.")

    except Exception as error:
        return bad_request(f"Error on task creating: {error}")

@bp.route('/tasks/run', methods=['POST'])
def run_tasks():
    log.status_log(f"Try run download tasks")
    data = request.get_json() or {}

    if 'status' not in data:
        status = 0
    else:
        status = data['status']

    tasks = Task.to_collection_short_dict(Task.query.filter_by(status=status).order_by('created'))

    service.get_video_from_youtube(tasks)
    
    log.status_log(f"Task complited!")
    response = jsonify(tasks)
    response.status_code = 200
    return response

@bp.route('/tasks/<int:id>/run', methods=['POST'])
def run_task(id):
    log.status_log(f"Try run download tasks")
    data = request.get_json() or {}

    tasks = Task.to_collection_short_dict(Task.query.filter_by(id=id))

    service.get_video_from_youtube(tasks)
    
    log.status_log(f"Task complited!")
    response = jsonify(tasks)
    response.status_code = 200
    return response

@bp.route('/tasks/set-key', methods=['POST'])
def set_key():
    log.status_log(f"Try set video keys")
    data = request.get_json() or {}

    tasks = Task.to_collection_short_dict(Task.query.all())

    for t in tasks['items']:
        if t['video_key']: 
            task = Task()
            task = Task.query.get(t['id'])

            video_key = {'video_key':str(t['url'][-11:])}
            
            task.from_dict(video_key, new_task=False)
            db.session.commit()

    log.status_log(f"Task complited!")
    response = jsonify("Task complited!")
    response.status_code = 200
    return response