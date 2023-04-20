import json
from app import db
from app.service import logic, data_frame_logic
from app.logger import Logger
from app.api import bp
from app.api.errors import bad_request, not_found, error_response
from flask import request, jsonify

log     = Logger()
service = logic.Service()
dfs     = data_frame_logic.DFService()

@bp.route('/df/generate', methods=['POST'])
def gen_data_frame():
    try:
        log.status_log(f"Try generate data frames")
        data = request.get_json() or {}

        if 'type' not in data:
            return bad_request(f"must include type field")

        result = dfs.generate_data_frame(data['type'])
        #tmp = json.loads(result)
        #response = jsonify(json.dumps(tmp))
        msg = f"Data frame type {data['type']} generation complite."
        response = jsonify({"result":msg})
        response.status_code = 200
        
        log.status_log(f"Data frames generation complite.")
        
        return response
    except Exception as error:
        return bad_request(f"Data frames generation error: {error}")