Experimental web backend for TANGO


DESCRIPTION

This is an attempt at using "modern" - perhaps too modern - web standards to make a TANGO web service. It provides websocket communication for subscribing to attributes, and an (incomplete) GraphQL interface to the TANGO database.

It also includes an experimental "dashboard" web browser user interface that can interactively be configured to display TANGO attributes in various ways.  It allows dragging and dropping attributes from a Jive-like tree onto various "cards" that can be moved around on the screen. The state of the dashboard is currentlty saved in the URL so making e.g. a bookmark should be enough to persist it.


BUILDING/RUNNING

The server is written in Python and currently requires python 3.4 or later (I think).

It uses Taurus, which is not officially supporting python 3 yet, but Vincent Michel has made a port of the "core" part of Taurus (e.g. minus the Qt parts) which can be found at https://gitlab.maxiv.lu.se/vinmic/python3-taurus-core

"aiohttp" is used for the web server part, "graphite" for the GraphQL part. "requirements.txt" should list the necessary libraries, which can be installed using "pip".

Once all is installed, start the server by doing:

  $ python3.5 aioserver.py

The UI can be accessed at http://localhost:5004/index.html

The UI is written in javascript ES6, using React/redux to handle the UI and webpack to compile and build. A prebuilt "bundle" is included in the repo, but if you want to modify the code, you'll need to install nodejs and npm (according to your platform), and then do:

  $ npm install
  $ webpack

in the project root. This should produce a new "static/js/bundle.js", which is what the browser needs.

Also included is a local version of GraphiQL, the GraphQL query playground, at http://localhost:5003/graphiql.html Nice for debugging and exploring.

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

This should result in a JSON object that contains all attributes of the TangoTest device (provided it's running).


TODO/IDEAS

- Error handling
- Robustness
- General performance
- Only supports subscriptions right now, but read/write attributes across websockets would probably make sense.
- Serialization. Uses JSON, which is very space-inefficient when it comes to floating point arrays and such. Some experiments with BSON have been done; perhaps look into msgpack, protobuf..?
- The UI is pretty basic and not very well thought through. Think about whether to generalize it or if it should stay as a relatively simple "read-only" interface.
