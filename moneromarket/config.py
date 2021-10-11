import os ;
import json ;


# With open("") will change to where file is located at on testing server, else it is <insert here>.
config = None ;
# with open("/etc/config.json") as config_file:
# 	config = json.load(config_file) ;


class Config:
	SECRET_KEY = "123"# config.get("SECRET_KEY") ;
	SQLALCHEMY_DATABASE_URI = "123"#config.get("SQLALCHEMY_DATABASE_URI") ;





# For me I had a problem when it came to nginx being able to access my static directory.
# I kept getting "Forbidden 403" when trying to access static directory, and css wouldn't load when gunicorn was ran.

# Solution that worked for me:
#   cd ~
#   sudo usermod -a -G your_user www-data
#   sudo chown -R :www-data /path/to/your/static/folder

# your_user is the username you assigned,  example for this video was coreyms
# /path/to/your/static/folder you can get by going to your static folder and then typing in:
#   pwd

# That will show you the path to your static folder
# Example of pwd for this video was /home/coreyms/Flask_Blog/flaskblog/static

# Above is for Ubuntu/Debian

# For CentOS/Fedora, type:
#   cd ~
#   sudo usermod -a -G your_user nginx
#   chmod 710 /home/your_user


# Source:   https://stackoverflow.com/questions/16808813/nginx-serve-static-file-and-got-403-forbidden
# YouTube:  https://www.youtube.com/watch?v=goToXTC96Co&list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH&index=15



'''
Source: https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet
For generating the same fernet key using Ledger, type this in a python3 terminal:
	>>> import base64
	>>> import os
	>>> from cryptography.fernet import Fernet
	>>> from cryptography.hazmat.primitives import hashes
	>>> from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
	>>> password = b"MoneroMarket fernet"
	>>> salt = b'\xa6\xc7a\xbc\xeb\n\x95\xa7tu\xdeS@\xa6\xf7\xee'
	>>> kdf = PBKDF2HMAC(
	...     algorithm=hashes.SHA256(),
	...     length=32,
	...     salt=salt,
	...     iterations=100000,
	... )
	>>> key = base64.urlsafe_b64encode(kdf.derive(password))
	>>> print(key)
'''
