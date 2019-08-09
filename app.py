from flask import Flask

app = Flask(__name__)

from solve import run


@app.route('/submit', methods=["POST"])
def submit():
	return run(request.json)


if __name__ == '__main__':
	app.run()