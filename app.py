# /usr/bin/env python3

import bottle
import sqlite3
import json
import uuid
from contextlib import closing

app = application = bottle.Bottle()

MINIMAL_CORS = {
	'Content-type' : 'application/json',
	'Access-Control-Allow-Origin' : 'localhost:8081',
} # 'Access-Control-Allow-Headers' : 'Origin'

DB_PATH = '/tmp/ContenidoTematico.db' # '/mnt/sdcard/basecita3.db'

@app.route('/_/', method='GET')
def entry_point():
	return bottle.template('index', root='./views/')

@app.route('/@/', method='GET')
def entry_point():
	return bottle.template('topics', root='./views/')

@app.route("/<filepath:re:.*\.(css|js)>", method='GET')
def asset_files(filepath):
	return bottle.static_file(filepath, root='./static/')

@app.error(404)
def error404(error):
	return 'Nothing here, sorry'

@app.route('/COURSES/v1/', method='GET')
def get_courses():
	try:
		with sqlite3.connect(DB_PATH) as connection:
			with closing(connection.cursor()) as cursor:
				cursor.execute("SELECT UPPER([Id]) AS id, UPPER([Name]) AS nm FROM [Courses] WHERE [Status]=7", ())
				cursor.row_factory = sqlite3.Row
				ds_ = [dict(r) for r in cursor.fetchall()]
				return bottle.HTTPResponse(body=json.dumps({'data': ds_}), status=200, headers=MINIMAL_CORS)
	except sqlite3.OperationalError as e:
		return bottle.HTTPResponse(body=json.dumps({'msg': str(e)}), status=500)


@app.route('/COURSES/v1/', method='POST')
def add_course():
	try:
		incomming_data = json.load(bottle.request.body)
	except ValueError:
		return bottle.HTTPResponse(body=json.dumps({'msg':'No valid JSON object'}), status=500)
	try:
		id_ = str(uuid.uuid4())
		parameters_ = (id_, incomming_data['name_'], )
		with sqlite3.connect(DB_PATH) as connection:
			with closing(connection.cursor()) as cursor:
				cursor.execute("INSERT INTO [Courses] VALUES (UPPER(?), LOWER(?), 7)", parameters_)
				connection.commit()
				cursor.execute("SELECT UPPER([Id]) AS id, UPPER([Name]) AS nm FROM [Courses] WHERE [Id]=? AND [Status]>=5", (str(id_).upper(), ))
				cursor.row_factory = sqlite3.Row
				ds_ = [dict(r) for r in cursor.fetchall()]
				return bottle.HTTPResponse(body=json.dumps({'data': ds_}), status=201, headers=MINIMAL_CORS)
	except sqlite3.OperationalError as e:
		return bottle.HTTPResponse(body=json.dumps({'msg': str(e)}), status=500)


@app.route('/COURSES/v1/set/description/', method='PATCH')
def update_name_on_course():
	try:
		data_2_update = json.load(bottle.request.body) # bottle.request.json
	except ValueError:
		return bottle.HTTPResponse(body=json.dumps({'msg':'No valid JSON object'}), status=500)

	try:
		id_ = str(data_2_update['id_']).upper()
		parameters_ = ( data_2_update['name_'], id_, )

		with sqlite3.connect(DB_PATH) as connection:
			with closing(connection.cursor()) as cursor:
				cursor.execute("UPDATE [Courses] SET [Name]=LOWER(?) WHERE [Id]=UPPER(?) AND ([Status] & 2)=2", parameters_)
				connection.commit()
				cursor.execute("SELECT UPPER([Id]) AS id, UPPER([Name]) AS nm FROM [Courses] WHERE [Id]=? AND [Status]>=5", (id_, ))
				cursor.row_factory = sqlite3.Row
				ds_ = [dict(r) for r in cursor.fetchall()]
				return bottle.HTTPResponse(body=json.dumps({'data': ds_}), status=200, headers=MINIMAL_CORS)
	except sqlite3.OperationalError as e:
		return bottle.HTTPResponse(body=json.dumps({'msg': str(e)}), status=500)


if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8081, reloader=True, debug=True)