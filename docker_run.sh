sudo docker run -d -p 5006:5006 --name isocket_atlas_1 isocket_atlas
sudo docker run -d -p 5000:80 --link isocket_atlas_1 --name isocket_web_1 isocket_web
