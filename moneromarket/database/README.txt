Open up a terminal and go inside MoneroMarket directory.

Type inside the terminal:
$:  python3
>>> from moneromarket import db, create_app
>>> app = create_app()
>>> app.app_context().push()
>>> db.create_all()


Done!




# Online reference
https://flask-sqlalchemy.palletsprojects.com/en/2.x/contexts/