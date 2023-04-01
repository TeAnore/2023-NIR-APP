from app import db
from app.service import logic
from app.models import User, Task, Video
from app.logger import Logger
from app.api import bp
from app.api.errors import bad_request, not_found, error_response
from flask import request, jsonify, url_for
from psycopg2.errors import IntegrityConstraintViolation, RestrictViolation, NotNullViolation, ForeignKeyViolation, UniqueViolation, CheckViolation, ExclusionViolation, InvalidCursorState

log = Logger()

@bp.route('/videos/<int:id>', methods=['GET'])
def get_video(id):
    return jsonify(Video.query.get_or_404(id).to_dict())

@bp.route('/videos', methods=['GET'])
def get_videos():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Video.to_collection_dict(Video.query, page, per_page, 'api.get_videos')
    return jsonify(data)