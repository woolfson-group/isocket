FROM tiangolo/uwsgi-nginx-flask:flask-python3.5
RUN wget https://github.com/jgm/pandoc/releases/download/1.19.1/pandoc-1.19.1-1-amd64.deb
RUN dpkg -i pandoc-1.19.1-1-amd64.deb
COPY ./requirements.txt ./
RUN pip install -r ./requirements.txt
COPY ./ /app/
WORKDIR /app/
CMD ["bokeh", "serve", "--prefix=bokeh", "--allow-websocket-origin=*", "atlas.py"]
