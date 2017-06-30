FROM python:3.5
COPY ./requirements.txt .
RUN pip install -r ./requirements.txt
COPY . /app
WORKDIR /app
CMD ["bokeh", "serve", "atlas.py", "--allow-websocket-origin=localhost:19878"]
