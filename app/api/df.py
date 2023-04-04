import json
from app import db
from app.service import logic
from app.logger import Logger
from app.api import bp
from app.api.errors import bad_request, not_found, error_response
from flask import request, jsonify

log = Logger()
service = logic.Service()

@bp.route('/df/generate', methods=['POST'])
def gen_data_frame():
    try:
        log.status_log(f"Try generate data frames")
        data = request.get_json() or {}

        if 'type' not in data:
            return bad_request(f"must include type field")

        result = service.generate_data_frame(data['type'])

        tmp = json.loads(result)
        #log.dev_log(f"Result json {tmp}")
        #for r in json.loads(result):
            #log.dev_log(f"Record {r}")

        response = jsonify(json.dumps(tmp))
        response.status_code = 200
        
        log.status_log(f"Data frames generation complite.")
        
        return response
    except Exception as error:
        return bad_request(f"Data frames generation error: {error}")