Experimental web backend for TANGO


DESCRIPTION

This is an attempt at using "modern" - perhaps too modern - web standards to make a TANGO web service. It provides an (incomplete) GraphQL interface to the TANGO database, and websocket communication for attributes. Included is a pretty useless browser user interface demo.

This is all very experimental, inefficient and broken in many ways, especially the UI. It should be viewed as a proof of concept.


BUILDING/RUNNING

The server is written in Python and currently requires >=3.5 (although it should be easy to support slightly older python 3 versions.) It requres the "asyncio-support" branch of PyTango (from vinmic). "aiohttp" is used for the web server part. "requirements.txt" should list the necessary libraries.

  $ python3.5 aioserver.py

The UI can be accessed at "http://localhost:5002/index.html". It displays an interactive "device tree" and allows clicking attributes to add/remove listening.

The UI is written in javascript ES6, using React/redux to handle the UI and webpack to compile and build. A prebuilt "bundle" is included in the repo, but if you want to modify the code, you'll need to install nodejs and npm (according to your platform), and then do:

  $ npm install
  $ webpack

in the project root. This should produce a new "static/js/bundle.js".

Also included is a local version of GraphiQL, the GraphQL query playground, at http://localhost:5002/graphiql.html. Nice for debugging and exploring.

An example query (some more examples in schema.py):

{
    devices(pattern: "sys/tg_test/1") {
        name
        attributes { 
            device
            name
        }
    }
}

TODO/IDEAS

- Serialization. Some experiments with BSON are included; perhaps look into msgpack, protobuf..? Performance testing.
- Figure out event subscription with asyncio.
- Only supports "push" right now, read/write attributes across websockets would make sense.
- An actually useful interface, something like a "dashboard" that can be configured to display various attributes?
- Make the database client async
