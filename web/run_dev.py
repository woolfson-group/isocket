import os

from isocket.factory import create_app

os.environ['ISOCKET_CONFIG'] = 'development'
app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
