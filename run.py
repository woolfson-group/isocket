import os
from isocket.factory import create_app

os.environ['ISOCKET_CONFIG'] = 'development'
app = create_app()
app.run(debug=True)
