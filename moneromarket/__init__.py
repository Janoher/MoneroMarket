from flask import Flask ;
from flask_sqlalchemy import SQLAlchemy ;
from flask_bcrypt import Bcrypt ;
from flask_login import LoginManager ;

from moneromarket.config import Config


db = SQLAlchemy() ;
bcrypt = Bcrypt() ;
login_manager = LoginManager() ;


# Redirect to login page if not logged in and trying to access something that you need to be logged into to view first
login_manager.login_view = "users.login" ;
login_manager.login_message_category = "alert-blue" ;


def create_app(config =Config):

	app = Flask(__name__) ;
	app.config.from_object(config) ;

	db.init_app(app) ;
	bcrypt.init_app(app) ;
	login_manager.init_app(app) ;


	from moneromarket.main.routes import main ;
	from moneromarket.users.routes import users ;
	from moneromarket.listings.routes import listings ;
	from moneromarket.messages.routes import messages ;
	from moneromarket.orders.routes import orders ;
	from moneromarket.errors.handlers import errors ;
	from moneromarket.wallets.routes import wallets ;
	from moneromarket.employees.routes import employees ;
	from moneromarket.reviews.routes import reviews ;

	app.register_blueprint(main) ;
	app.register_blueprint(users) ;
	app.register_blueprint(listings) ;
	app.register_blueprint(messages) ;
	app.register_blueprint(orders) ;
	app.register_blueprint(errors) ;
	app.register_blueprint(wallets) ;
	app.register_blueprint(employees) ;
	app.register_blueprint(reviews) ;

	return app ;



# pip3 install flask
# pip3 install flask-wtf
# pip3 install flask-bcrypt
# pip3 install flask-login
# pip3 install -U flask-paginate
# pip3 install flask-sqlalchemy
# pip3 install email_validator
# pip3 install Image



# pip3 install cryptography 
# pip3 install qrcode
# pip3 install requests
# pip3 install numpy



# Try the first one. If it doesn't work, install XCode and run it.
# pip3 install monero


# https://www.monero.how/how-to-run-monero-node







































