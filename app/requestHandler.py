from flask import (
	render_template,
	url_for,
	request as flaskRequest,
	jsonify
)

import json


def RequestHandler(miniBase):

	flask = miniBase.flask

	@flask.route("/")
	@flask.route("/index")
	def index():
		return render_template('index.html')