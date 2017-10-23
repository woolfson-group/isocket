docker stop isocket_web_1
docker stop isocket_atlas_1
docker rm isocket_web_1
docker rm isocket_atlas_1
docker build -t isocket_web ./web/
docker build -t isocket_atlas ./atlas_visualisation/
docker run -d -p 1803:5006 --name isocket_atlas_1 isocket_atlas
docker run -d -p 1802:80 --restart on-failure --name isocket_web_1 isocket_web
