sudo docker stop isocket_web_1
sudo docker stop isocket_atlas_1
sudo docker rm isocket_web_1
sudo docker rm isocket_atlas_1
sudo docker build -t isocket_web ./web/
sudo docker build -t isocket_atlas ./atlas_visualisation/
sudo docker run -d -p 1803:5006 --name isocket_atlas_1 isocket_atlas
sudo docker run -d -p 1802:80 --restart on-failure --name isocket_web_1 isocket_web
