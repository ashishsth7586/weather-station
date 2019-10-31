from flask import Flask, render_template, request
import time
import datetime
import arrow

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

	temperatures, humidities, timezone, from_date_str, to_date_str = get_records()

	time_adjusted_temperatures = []
	time_adjusted_humidities = []

	for record in temperatures:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_adjusted_temperatures.append([local_timedate.format("YYYY-MM-DD HH:mm"), round(record[2], 2)])

	for record in humidities:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_adjusted_humidities.append([local_timedate.format("YYYY-MM-DD HH:mm"), round(record[2], 2)])

	return render_template("lab_env_db.html", 
						temp = time_adjusted_temperatures,
						hum = time_adjusted_humidities,
						temp_items = len(temperatures),
						hum_items = len(humidities),
						from_date = from_date_str,
						to_date = to_date_str,
						timezone = timezone)

def get_records():

	from_date_str = request.args.get('from', time.strftime("%Y-%m-%d %H:%M"))
	to_date_str = request.args.get('to', time.strftime("%Y-%m-%d %H:%M"))
	range_h_form = request.args.get('range_h', '')
	timezone = request.args.get('timezone', 'Etc/UTC')
	range_h_int = "nan"

	try:
		range_h_int = int(range_h_form)
	except:
		print("range_h_form not a number")

	if not validate_date(from_date_str):
		from_date_str = time.strftime("%Y-%m-%d 00:00")
	if not validate_date(to_date_str):
		to_date_str = time.strftime("%Y-%m-%d %H:%M")

	# Create datetime object so that we can convert to UTC from the browser's local time
	from_date_obj = datetime.datetime.strptime(from_date_str, '%Y-%m-%d %H:%M')
	to_date_obj = datetime.datetime.strptime(to_date_str, '%Y-%m-%d %H:%M')

	if isinstance(range_h_int, int):
		arrow_time_from = arrow.utcnow().shift(hours=-range_h_int)
		arrow_time_to = arrow.utcnow()
		from_date_utc = arrow_time_from.strftime("%Y-%m-%d %H:%M")
		to_date_utc = arrow_time_to.strftime("%Y-%m-%d %H:%M")
		from_date_str = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")
		to_date_str = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")
	else:
		# Convert datetimes to UTC so we can retrieve the appropriate records from the database
		from_date_utc = arrow.get(from_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")
		to_date_utc = arrow.get(to_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")

	import sqlite3
	conn = sqlite3.connect("/var/www/lab_app/lab_app.db")
	curs = conn.cursor()

	# curs.execute("SELECT * FROM temperatures")
	# temperatures = curs.fetchall()
	# curs.execute("SELECT * FROM humidities")
	# humidities = curs.fetchall()

	curs.execute("SELECT * FROM temperatures WHERE rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	temperatures = curs.fetchall()
	curs.execute("SELECT * FROM humidities WHERE rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	humidities = curs.fetchall()
	conn.close()

	return [temperatures, humidities, timezone, from_date_str, to_date_str]


def validate_date(d):

	try:
		datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
		return True

	except ValueError:
		return False


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080)
