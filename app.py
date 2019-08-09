from flask import Flask, request

app = Flask(__name__)

from solve import run


@app.route('/submit', methods=["POST"])
def submit():
	return run(request.get_json())


if __name__ == '__main__':
	app.run()