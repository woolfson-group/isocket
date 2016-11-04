# iSocket
iSocket web applicaton.

Version 0.0.2 (November 4, 2016), Woolfson Group, University of Bristol.

[![CircleCI](https://circleci.com/gh/woolfson-group/isocket.svg?style=shield&circle-token=355d5025e9404cf5b00fc2e6150f05bfbccc3036)](https://circleci.com/gh/woolfson-group/isocket)


---
To run the Atlas app via bokeh server:

In one terminal, navigate to the isocket folder and run bokeh server (in the isocket virtual environment):

    $ bokeh serve --host localhost:5000 --host localhost:5006 isocket_app/atlas/atlas.py

Then run flask as normal (flask run.py). 
