import requests
import json
import datetime
import time
import math
import pandas as pd


r = requests.post("https://103.176.242.94:7443/REST/user/login",
                    headers={"Content-Type": "application/json"},
                  data=json.dumps({"userid": "iisc", "password": "f6aa28a67554f25438eb351fc0f13beb61b4298f969230c8cea1fa5edc796a09eaee1fc019a68abf5744e8b2b347cbd6668f162b07655d682ecb59f23a1545b7" }), verify=False)

vsessionid = r.json()["result"][0]["vsessionid"]
print(vsessionid)



time_now = math.floor(datetime.datetime.now().timestamp()) * 1000
time_prev = math.floor((datetime.datetime.now() - datetime.timedelta(minutes=1)).timestamp()) * 1000

r = requests.post("https://103.176.242.94:7443/REST/1/event/getevents",
                  headers={"cookie": "VSESSIONID= " + vsessionid, "Content-Type": "application/json"},
                  data=json.dumps({"starttimestamp": time_prev, "endtimestamp": time_now, "lpnumber": None, "channelid": None, "applicationid": None, "page": 1}), verify=False)


def make_request(page=1):
    r = requests.post("https://103.176.242.94:7443/REST/1/event/getevents",
                      headers={"cookie": "VSESSIONID= " + vsessionid, "Content-Type": "application/json"},
                      data=json.dumps({"starttimestamp": time_prev, "endtimestamp": time_now, "lpnumber": None, "channelid": None, "applicationid": None, "page": page}), verify=False)
    return r.json()

data = make_request()

lst = data["result"][0]["eventlist"]
tot_pages = data["result"][0]["totalpages"]

print(tot_pages)

for i in range(2, tot_pages):
    print(i)
    try:
        lst = lst  + (make_request(i)["result"][0]["eventlist"])
    except Exception as e:
        print(e)


df = pd.DataFrame(lst).to_csv("out.csv")
