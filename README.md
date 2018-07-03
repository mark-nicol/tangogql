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
			   attributes {\
				   name,\
				   datatype,\
				   }\
			   }\
		   }'

q = 'query{\
	devices(pattern: "sys/tg_test/1"){\
	   name,\
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

resp = requests.post('http://w-v-kitslab-web-0:5005/db', json={'query': query})
print(resp.json())
```
