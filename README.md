# iSocket
iSocket web application.

Version 0.2.3 (December 18, 2016), Woolfson Group, University of Bristol.

[![CircleCI](https://circleci.com/gh/woolfson-group/isocket.svg?style=shield&circle-token=355d5025e9404cf5b00fc2e6150f05bfbccc3036)](https://circleci.com/gh/woolfson-group/isocket)


---
To run the Atlas app via bokeh server:

In one terminal, navigate to the isocket folder and run bokeh server (in the isocket virtual environment):

    $ bokeh serve isocket/atlas/atlas.py --allow-websocket-origin="localhost:5000"

(This assumes the bokeh application is being served at "localhost:5006/atlas" as defined in atlas/views.py, and that the flask app is running at "localhost:5000" (default)).
Then run flask as normal (flask run.py). 
