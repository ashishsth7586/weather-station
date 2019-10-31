from flask import Flask, render_template, request
import time
import datetime


app = Flask(__name__)
app.debug = True

@app.route("/")
def hello():
	return render_template('hello.html', message="Main Page! Welcome :) ")

@app.route("/lab_temp")
def lab_temp():
	import sys
	import Adafruit_DHT
	humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 17)
	if humidity is not None and temperature is not None:
		return render_template("lab_temp.html", temp=temperature, hum=humidity)

	else:
		return render_template("no_sensor.html")

@app.route("/lab_env_db", methods=['GET'])
def lab_env_db():

	from_date_str = request.args.get('from', time.strftime("%Y-%m-%d %H:%M"))
	to_date_str = request.args.get('to', time.strftime("%Y-%m-%d %H:%M"))

	if not validate_date(from_date_str):
		from_date_str = time.strftime("%Y-%m-%d 00:00")
	if not validate_date(to_date_str):
		to_date_str = time.strftime("%Y-%m-%d %H:%M")

	import sqlite3
	conn = sqlite3.connect("/var/www/lab_app/lab_app.db")
	curs = conn.cursor()

	# curs.execute("SELECT * FROM temperatures")
	# temperatures = curs.fetchall()
	# curs.execute("SELECT * FROM humidities")
	# humidities = curs.fetchall()

	curs.execute("SELECT * FROM temperatures WHERE rDateTime BETWEEN ? AND ?", (from_date_str, to_date_str))
	temperatures = curs.fetchall()
	curs.execute("SELECT * FROM humidities WHERE rDateTime BETWEEN ? AND ?", (from_date_str, to_date_str))
	humidities = curs.fetchall()
	conn.close()
	return render_template("lab_env_db.html", temp=temperatures, hum=humidities)

def validate_data(d):
	try:
		datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
		return True
	except ValueError:
		return False

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080)
