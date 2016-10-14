import os
from isocket_app.factory import create_app

os.environ['ISOCKET_CONFIG'] = 'development'
app = create_app()
app.run(debug=True)
