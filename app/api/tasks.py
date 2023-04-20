from app import db
from app.api import bp
from app.api.errors import bad_request, not_found
from app.logger import Logger
from app.models import User, Task
from app.service import logic, video_service

from flask import request, jsonify, url_for

log = Logger()
service = logic.Service()
vs = video_service.VideoService()

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
    
    log.dev_log(f"Create Request: {request}")

    if 'user_id' not in data or 'url' not in data or 'reaction' not in data:
        return bad_request('Must include user_id, url and reaction fields')

    needCaption = False
    
    if 'caption' in data:
        if data['caption'] == 'Unknow':
            needCaption = True
    else:
        needCaption = True

    try:
        user = User()
        user_id = str(data['user_id'])
        user = User.query.filter_by(external_user_id=user_id).first()
        user.to_dict(user)
        data['user_id'] = user.id
        if user:
            task = Task()
            task = Task.query.filter_by(user_id=data['user_id'], url=data['url']).first()
            if task:
                if needCaption:
                    data['caption'] = task.caption

                db.session.commit()
                log.msg_log(f"Update user_id: {user.id} task_id: {task.id}")
            else:
                if needCaption:
                    vi = vs.get_youtube_object(data['url'])
                    
                    if str(type(vi)) == "<class 'str'>":
                        data['caption'] = 'Unknow'
                    else:
                        details = vi.vid_info.get('videoDetails', {})
                        data['caption'] = details.get('title', '')

                task = Task()
                task.from_dict(data, new_task=True)
                db.session.add(task)
                db.session.commit()
                log.msg_log(f"Create user_id: {user.id} task_id: {task.id}")

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
    log.status_log(f"Process tasks: Begin")
    data = request.get_json() or {}

    if 'status' not in data:
        status = 0
    else:
        status = data['status']

    tasks = Task.to_collection_short_dict(Task.query.filter_by(status=status).order_by('created'))
    for task in tasks['items']:
        service.get_video_from_youtube(task)

    log.status_log(f"Process tasks: Complited!")
    response = jsonify(tasks)
    response.status_code = 200
    return response

@bp.route('/tasks/<int:id>/run', methods=['POST'])
def run_task(id):
    log.status_log(f"Process task: {id} - Begin")
    data = request.get_json() or {}

    task = Task.query.get_or_404(id).to_dict()
    service.get_video_from_youtube(task)
    
    log.status_log(f"Process task: {id} - Complite!")
    response = jsonify(task)
    response.status_code = 200
    return response