import requests, json


url = 'http://127.0.0.1:5000/searchCountry?country=fra&key=1234'
r =requests.get(url)
resp = json.loads(r.text)
print(resp['msg'])


n=0
while n < 1:
    url = 'http://127.0.0.1:5000/searchCountry?country=fra&key=123'
    r =requests.get(url)
    resp = json.loads(r.text)
    print(resp['msg'])
    print(len(resp['results']), 'records')
    n+=1