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
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = 'SELECT * FROM class_auth WHERE `token` = %s;'
    cur.execute(sql,(token))
    results = cur.fetchall()
    if len(results) == 1:
        return True
    else:
        return False

def log(token,endpoint,response):
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = 'INSERT INTO `class_api-logs` (`endpoint`,`token`,`response`,`dt`) VALUES (%s,%s,%s,%s)'
    dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(sql,(token,endpoint,response,dt))


@app.route("/", methods=['GET','POST'])
def root():
    res = {} 
    res['code'] = 2
    res['msg'] = 'No endpoint specified'
    res['req'] = '/'
    return json.dumps(res,indent=4)
    #return '<b>hello</b>'

@app.route("/sum", methods=['GET','POST'])
def sum():
    res = {}
    res['req'] = '/sum'
    n1 = request.args.get('n1')
    n2 = request.args.get('n2')
    n1f = None
    n2f = None
    try:
        n1f = float(n1)
        n2f = float(n2)
    except Exception as e:
        print(str(e))
        pass
    if n1f is not None and n2f is not None:
        res['sum'] = n1f + n2f
        res['code'] = 2
        res['msg'] = 'ok'
    else:
        res['sum'] = None
        res['code'] = 1
        res['msg'] = 'n1 and n2 must be numeric'
        log(request.args.get('key'),res['req'],'429')
    log(request.args.get('key'),res['req'],'200')
    return json.dumps(res,indent=4)
@app.route("/searchCountry", methods=['GET','POST'])
def searchCountry():
    res = {} 
    res['req'] = '/searchCountry'
    if not auth(request.args.get('key')):
        res['code'] = 1
        res['msg'] = 'auth error'
        log(request.args.get('key'),res['req'],'429')
        return json.dumps(res,indent=4)
    
    country_term = request.args.get('country')
    if country_term is None:
        res['code'] = 1
        res['msg'] = 'country needs to be provided.'
        return json.dumps(res,indent=4)
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = 'SELECT * FROM class_airlines WHERE `country` LIKE %s ORDER BY `country`;'
    st = f'%{country_term}%'
    print(sql,st)
    cur.execute(sql,(st))
    res['code'] = 0
    res['msg'] = 'ok'
    items = []
    for row in cur:
        item = {}
        item['icao'] = row['icao']
        item['country'] = row['country']
        item['airline_name'] = row['airline']
        items.append(item)

    res['results'] = items
    res['num_results'] = len(items)
    log(request.args.get('key'),res['req'],'200')
    return json.dumps(res,indent=4)


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)