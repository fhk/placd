from flask import Flask, request
from flask_cors import CORS, cross_origin

from solve import run


app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/submit', methods=["POST"])
@cross_origin()
def submit():
	return run(request.get_json())


if __name__ == '__main__':
	app.run()
