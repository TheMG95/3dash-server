from flask import Flask
from flask import request
from flask import abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from json import loads
import time

cluster = MongoClient("Your MongoDB Credentials here")
db = cluster["Cluster Name"]
collection = db["Collection Name"]

app = Flask(__name__)

limiter = Limiter(app, key_func=get_remote_address)


@app.route("/push_level_data", methods=["POST"])
@limiter.limit("10/day")
def push_level_data():
	data = request.form
	loaded_data = loads(data["data"])
	if loaded_data["name"] is not None and loaded_data["author"] is not None and loaded_data["difficulty"] is not None:
		if len(loaded_data["name"]) <= 24 and len(loaded_data["author"]) <= 24 and type(loaded_data["difficulty"]) == int:
			if loaded_data["difficulty"] <= 5:
				id = collection.find({}).sort("_id", -1).limit(1)[0]["_id"] + 1
				level = {
					"_id": id,
					"data": data["data"],
					"upload_date": time.time(),
					"uploader_ip": request.headers.get('X-Forwarded-For', request.remote_addr)
				}
				collection.insert_one(level)
				return str(id)
	abort(400)


@app.route("/get_recent", methods=["GET"])
@limiter.limit("2/second; 240 per hour")
def get_recent():
	levels = collection.find({}).sort("_id", -1).limit(20)
	string = ""
	for level in levels:
		data = loads(level['data'])
		string += f"{level['_id']}\n{data['name']}\n{data['author']}\n{data['difficulty']}\n"
	return string


@app.route("/get_json", methods=["POST"])
@limiter.limit("2/second; 240 per hour")
def get_json():
	try:
		id = int(request.form["id"])
	except:
		abort(400)
	level = collection.find_one({"_id": id})
	if level is not None:
		return level["data"]
	else:
		abort(404)


if __name__ == "__main__":
	app.run()
