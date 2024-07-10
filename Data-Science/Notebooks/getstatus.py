import requests
import json


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

req = "https://rs.iudx.org.in/ngsi-ld/v1/async/status?searchId=$0"


headers = {"token": token}

outs = []

with open("./output.json", "r") as f:
    reqs = json.load(f)
    url = req.replace("$0",reqs["result"][0]["searchId"])
    r = requests.get(url, headers=headers)
    with open("downloadurls", "w") as ff:
        json.dump(r.json(), ff)

# with open("./output.json", "r") as f:
#     reqs = f.readlines()
#     print(reqs)
#     for l in reqs:
#         url = req.replace("$0",json.loads(l[:-1])["result"][0]["searchId"])
#         r = requests.get(url, headers=headers)
#         outs.append(r.json())

# print(outs)
# 
# with open("downloadurls", "w") as f:
#     json.dump(outs,f)


