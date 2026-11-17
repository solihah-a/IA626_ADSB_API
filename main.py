import json,pymysql,time
from flask import Flask
from flask import request,redirect
import datetime
import yaml

app = Flask(__name__)

db_config = None
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
    db_config = config['mysql']     

def auth(token):
    if token is None:
        return False
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cur:
            sql = "SELECT COUNT(*) FROM `adeboysa_auth` WHERE `token` = %s"
            cur.execute(sql, (token,))
            count = cur.fetchone()[0]
        return count == 1
    finally:
        conn.close()

def log(token, endpoint, response):
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cur:
            sql = """
                INSERT INTO `adeboysa_api_logs`
                (`endpoint`, `token`, `response`, `dt`)
                VALUES (%s, %s, %s, %s)
            """
            dt = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'
            )
            cur.execute(sql, (endpoint, token, str(response), dt))
            conn.commit()
    finally:
        conn.close()

@app.route("/", methods=['GET','POST'])
def root():
    res = {} 
    res['code'] = 2
    res['msg'] = 'No endpoint specified'
    res['req'] = '/'
    return json.dumps(res,indent=4)
    #return '<b>hello</b>'

def send_response(res, token):
    endpoint = res["req"]

    try:
        log(token, endpoint, json.dumps(res, default=str))
    except pymysql.MySQLError:
        print(f"Warning: Could not log request to {endpoint}")

    if res["code"] == 1:
        status = 200
    elif res["msg"] == "Invalid API key":
        status = 401
    elif "database" in res["msg"].lower():
        status = 503
    else:
        status = 400

    return app.response_class(
        response=json.dumps(res, indent=4, default=str),
        status=status,
        mimetype="application/json"
    )

@app.route("/getData", methods=["GET"])
def getData():
    res = {
        "code": 0,
        "msg": "",
        "req": "getData",
        "sqltime": 0.0,
        "results": []
    }
    token = request.args.get("key")
    start = request.args.get("start")
    end = request.args.get("end")

    if not token:
        res["msg"] = "Missing API key"
        return send_response(res, token)

    if not start or not end:
        res["msg"] = "Both start and end dates are required"
        return send_response(res, token)

    try:
        if not auth(token):
            res["msg"] = "Invalid API key"
            return send_response(res, token)
    except pymysql.MySQLError:
        res["msg"] = "Database authentication unavailable"
        return send_response(res, token)

    try:
        start_dt = datetime.datetime.strptime(
            start, "%Y-%m-%d %H:%M:%S"
        )
        end_dt = datetime.datetime.strptime(
            end, "%Y-%m-%d %H:%M:%S"
        )
        if start_dt > end_dt:
            res["msg"] = "Start date must be before or equal to end date"
            return send_response(res, token)
    except ValueError:
        res["msg"] = "Invalid date format. Use YYYY-MM-DD HH:MM:SS"
        return send_response(res, token)

    conn = None

    try:
        conn = pymysql.connect(**db_config)

        sql = """
            SELECT *
            FROM class_datapoints
            WHERE date_time BETWEEN %s AND %s
            ORDER BY date_time
            LIMIT 500
        """

        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql_start = time.time()
            cur.execute(sql, (start_dt, end_dt))
            records = cur.fetchall()
            res["sqltime"] = round(time.time() - sql_start, 4)

        res["code"] = 1
        res["msg"] = f"Successfully retrieved {len(records)} records"
        res["results"] = records

    except pymysql.MySQLError:
        res["msg"] = "Unable to retrieve ADS-B records from the database"

    finally:
        if conn is not None:
            conn.close()
    
    return send_response(res, token)


@app.route("/countInPolygon", methods=["GET"])
def countInPolygon():
    res = {
        "code": 0,
        "msg": "",
        "req": "countInPolygon",
        "sqltime": 0.0,
        "count": 0
    }

    token = request.args.get("key")
    polygon = request.args.get("polygon")

    if not token:
        res["msg"] = "Missing API key"
        return send_response(res, token)

    if not polygon:
        res["msg"] = "Missing polygon coordinates"
        return send_response(res, token)

    try:
        if not auth(token):
            res["msg"] = "Invalid API key"
            return send_response(res, token)
    except pymysql.MySQLError:
        res["msg"] = "Database authentication unavailable"
        return send_response(res, token)

    try:
        points = []
        for pair in polygon.split(","):
            coordinates = pair.strip().split()

            if len(coordinates) != 2:
                raise ValueError("Each point needs two coordinates")

            longitude = float(coordinates[0])
            latitude = float(coordinates[1])

            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude is out of range")

            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude is out of range")

            points.append((longitude, latitude))

        if len(points) < 4:
            raise ValueError("A closed polygon needs at least four points")

        if points[0] != points[-1]:
            raise ValueError("The polygon must be closed")

        if len(set(points[:-1])) < 3:
            raise ValueError("A polygon needs three distinct points")
        
        area = 0.0
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            area += x1 * y2 - x2 * y1
            
        if abs(area) < 1e-10:
            raise ValueError("Polygon must have a non-zero area")
    except ValueError as error:
        res["msg"] = f"Invalid polygon: {error}"
        return send_response(res, token)

    conn = None

    try:
        polygon_wkt = "POLYGON((" + ", ".join(
            f"{longitude} {latitude}"
            for longitude, latitude in points
        ) + "))"

        conn = pymysql.connect(**db_config)
        sql = """
            SELECT COUNT(*) AS aircraft_count
            FROM class_datapoints
            WHERE ST_Within(
                geo_point,
                ST_GeomFromText(%s, 0)
            )
        """
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql_start = time.time()
            cur.execute(sql, (polygon_wkt,))
            record = cur.fetchone()
            res["sqltime"] = round(time.time() - sql_start, 4)
        res["count"] = record["aircraft_count"]
        res["code"] = 1
        res["msg"] = "Successfully counted ADS-B records inside polygon"
    except pymysql.MySQLError:
        res["msg"] = "Unable to count ADS-B records from the database"
    finally:
        if conn is not None:
            conn.close()
    return send_response(res, token)

@app.route("/getAvgSpeedByFlight", methods=["GET"])
def getAvgSpeedByFlight():
    res = {
        "code": 0,
        "msg": "",
        "req": "getAvgSpeedByFlight",
        "sqltime": 0.0,
        "results": []
    }

    token = request.args.get("key")
    start = request.args.get("start")
    end = request.args.get("end")

    if not token:
        res["msg"] = "Missing API key"
        return send_response(res, token)

    try:
        if not auth(token):
            res["msg"] = "Invalid API key"
            return send_response(res, token)
    except pymysql.MySQLError:
        res["msg"] = "Database authentication unavailable"
        return send_response(res, token)

    try:
        start_dt = None
        end_dt = None
        if start:
            start_dt = datetime.datetime.strptime(
                start, "%Y-%m-%d %H:%M:%S"
            )
        if end:
            end_dt = datetime.datetime.strptime(
                end, "%Y-%m-%d %H:%M:%S"
            )
        if start_dt and end_dt and start_dt > end_dt:
            res["msg"] = "Start date must be before or equal to end date"
            return send_response(res, token)
    except ValueError:
        res["msg"] = "Invalid date format. Use YYYY-MM-DD HH:MM:SS"
        return send_response(res, token)


    conn = None

    try:
        conn = pymysql.connect(**db_config)

        sql = """
            SELECT flight_num, AVG(gs) AS avg_speed
            FROM class_datapoints
        """

        conditions = []
        params = []

        if start_dt:
            conditions.append("date_time >= %s")
            params.append(start_dt)

        if end_dt:
            conditions.append("date_time <= %s")
            params.append(end_dt)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += """
            GROUP BY flight_num
            ORDER BY flight_num
            LIMIT 500
        """
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql_start = time.time()
            cur.execute(sql, params)
            records = cur.fetchall()
            res["sqltime"] = round(time.time() - sql_start, 4)

        for record in records:
            if record["avg_speed"] is not None:
                record["avg_speed"] = float(record["avg_speed"])
        res["results"] = records
        res["code"] = 1
        res["msg"] = f"Successfully calculated averages for {len(records)} flights"
    except pymysql.MySQLError:
        res["msg"] = "Unable to calculate average flight speeds from the database"
    finally:
        if conn is not None:
            conn.close()

    return send_response(res, token)


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)