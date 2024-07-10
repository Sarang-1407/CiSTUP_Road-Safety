import requests
import json
from datetime import datetime 
from datetime import timedelta 



# start_time = "2022-12-01T00:00:00+05:30"
# end_time = "2023-02-15T00:00:00+05:30"
# 
# client_id = "6d040f36-002a-4858-a6bc-e9e7a61e290e"
# client_secret = "437ade5029d251f062ee988a1524938b6044d263"

rid = "5b778007-797e-4313-b34c-c7c4812365bb"
start_time = "2024-03-01T05:00:00+05:30"
end_time = "2024-03-10T05:30:00+05:30"

client_id = "434e8bf5-6114-43ea-bc56-dfbc9fcb6d54"
client_secret = "3e4b53e3d1fc5c615f81f426579b8d8fb0fd2df2"

authapi = "https://authorization.iudx.org.in/auth/v1/token"
authheaders = {"content-type": "application/json","clientId": client_id, "clientSecret" : client_secret}
body = { "itemId": rid, "role": "consumer", "itemType": "resource" }
r = requests.post(authapi, json.dumps(body), headers=authheaders, verify=True)
token = r.json()["results"]["accessToken"]
print(token)


headers = {"token": token}


time_format = "%Y-%m-%dT%H:%M:%S+05:30"

start_time_obj =  datetime.strptime(start_time, time_format)
end_time_obj =  datetime.strptime(end_time, time_format)


req = "https://rs.iudx.org.in/ngsi-ld/v1/async/search?id=" + rid + "&timerel=during&time=$0&endtime=$1"


''' One shot 
'''
r = requests.get(req.replace("$0", start_time).replace("$1", end_time), headers=headers)
print(r.status_code)
with open("output.json", "w") as f:
    json.dump(r.json(), f)



''' Iterative 
last_time = end_time
start_time_obj =  datetime.strptime(start_time, time_format)
for i in range(0,30):
    end_time_obj =  start_time_obj + timedelta(days=1)
    r = req.replace("$0", start_time_obj.strftime(time_format)) \
            .replace("$1", end_time_obj.strftime(time_format))
    start_time_obj =  end_time_obj
    resp = requests.get(r, headers=headers)
    print(resp.status_code)
    with open("output", "a") as f:
        json.dump(resp.json(),f)
        f.write("\n")

'''

