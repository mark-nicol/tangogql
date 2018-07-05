Experimental web backend for TANGO


### Description

This is an attempt at using "modern" - perhaps too modern - web standards to make a TANGO web service. It provides websocket communication for subscribing to attributes, and an (incomplete) GraphQL interface to the TANGO database.

### Running

The server is written in Python and currently requires python 3.4 or later (I think).

It uses Taurus, which is not officially supporting python 3 yet, but Vincent Michel has made a port of the "core" part of Taurus (e.g. minus the Qt parts) which can be found at `https://gitlab.maxiv.lu.se/vinmic/python3-taurus-core`

"aiohttp" is used for the web server part, "graphite" for the GraphQL part. "requirements.txt" should list the necessary libraries, which can be installed using "pip".

Once all is installed, start the server by doing:

```
  $ python aioserver.py
```

The requests are made to the url http://localhost:5004/db

#### Examples

```
import requests
query = 'query{  devices { name  }}'  # e.g. get the names of all devices
query = 'query{  devices(pattern: "*tg_test*") { name  }}'
#accessing attributes:
query='query{\
			devices(pattern: "sys/tg_test/1"){\
			   	name,\
			   	state,\
			   	attributes {\
				   name,\
				   datatype,\
				   }\
			   	}\
		   	}'

q = 'query{\
	devices(pattern: "sys/tg_test/1"){\
	   	name,\
		state,\
	   	attributes(pattern: "*scalar*") {\
			name,\
			datatype,\
			dataformat,\
			label,\
			unit,\
			description,\
			value,\
			quality,\
			timestamp\
		}\
        server{\
          id,\
          host\
        }\
	}\
}'

# Delete device property return ok = True if success
query ='mutation{deleteDeviceProperty(device:"sys/tg_test/1", name: "Hej"){
  	ok}
	}'

#Put device property return ok = True if sucess, the value field can be an empty string
query = 'mutation{putDeviceProperty(device:"sys/tg_test/1", name: "Hej", value: "test"){
  ok}}'

#Delete device property return ok = True if success
query = 'mutation{deleteDeviceProperty(device:"sys/tg_test/1",name:"Hej"){ok}}' 

#Set value for an attribute return ok = True if success and error message if not
mutation{SetAttributeValue(device:"sys/tg_test/1", name: "double_scalar",value: 2){
ok,
message
}}

#execute a command 
mutation{executeCommand(device: "sys/tg_test/1" command:"DevString" argin: "Hej"){
  ok,
  message,
  output
}}

resp = requests.post('http://w-v-kitslab-web-0:5005/db', json={'query': query})
print(resp.json())
```
