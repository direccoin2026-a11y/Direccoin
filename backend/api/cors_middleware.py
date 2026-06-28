from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/v1/estado')
def estado():
    return jsonify({"altura": 1000, "conexion": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8339)
