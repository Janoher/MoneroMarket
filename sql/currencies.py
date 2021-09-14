# pip3 install requests
# Access database to save into the information
import requests ;
import time ;
import sqlite3 ;
from sqlite3 import Error ;


# Make importing from moneromarket work as file path is now one back.
# Source: https://stackoverflow.com/questions/4383571/importing-files-from-different-folder
import sys ;
sys.path.insert(1, '../') ;


from moneromarket import db ;
from moneromarket.database.models import Currency ;



# Source: https://www.youtube.com/watch?v=iIGNhBcj4zs
# Source: https://coinmarketcap.com/api/documentation/v1/#operation/getV2CryptocurrencyQuotesHistorical
apikey = "48871def-b149-4933-b528-49f4ac8eeb0b" ;
headers = { "X-CMC_PRO_API_KEY": apikey, "Accepts" : "application/json"} ;
url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest" ;




# Source: https://www.sqlitetutorial.net/sqlite-python/update/
# Establish connection to database
def create_connection(db_file):
	connection = None ;

	try:
		connection = sqlite3.connect(db_file) ;

	except Error as error:
		print(error) ;



	return connection ;



# Update the currency price within the database
def update_database(connection, task):
	sql = ''' UPDATE currency
			  SET price = ?
			  WHERE country = ?'''


	cur = connection.cursor() ;
	cur.execute(sql, task) ;
	connection.commit() ;



# Initialize connection to the database...
connection = create_connection("../moneromarket/database/site.db") ;

# Print out whether database connected or not
if connection:
	print("Sucessfully connected to the database! (:") ;

else:
	print("Failed to connect to the database... ):") ;








# Loop indefinetely
while True:
	print("Starting to process currencies. Time: " + str(time.ctime())) ;

	# Get USA & Bitcoin & Ethrium price
	params = { "start" : 1, "limit" : 40, "convert": "USD"} ;
	json = requests.get(url, params=params, headers=headers).json() ;


	# Get list data
	coins = json["data"] ;
	monero_index = 1 ;
	bitcoin = 0.0 ;
	ethrium = 0.0 ;
	usd = 0.0 ;

	for coin in coins:
		# Record BTC <-> USD
		if coin["symbol"] == "BTC":
			bitcoin = coin["quote"]["USD"]["price"] ;

		# Record ETH <-> USD
		if coin["symbol"] == "ETH":
			ethrium = coin["quote"]["USD"]["price"] ;


		if coin["symbol"] == "XMR":
			usd = coin["quote"]["USD"]["price"] ;

			# Get cryptocurrecy prices against Monero
			bitcoin = coin["quote"]["USD"]["price"] / bitcoin ;
			ethrium = coin["quote"]["USD"]["price"] / ethrium ;
			
			break ;


		monero_index += 1 ;





	# Prepare to get the rest of the currency prices
	eur = gbp = aud = cad = chf = cny = jpy = krw = inr = rub = 0.0 ;


	# Euro
	params = { "start" : monero_index, "limit" : 1, "convert": "EUR"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	eur = coin[0]["quote"]["EUR"]["price"] ;



	# Britain
	params = { "start" : monero_index, "limit" : 1, "convert": "GBP"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	gbp = coin[0]["quote"]["GBP"]["price"] ;



	# Australia
	params = { "start" : monero_index, "limit" : 1, "convert": "AUD"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	aud = coin[0]["quote"]["AUD"]["price"] ;



	# Canada
	params = { "start" : monero_index, "limit" : 1, "convert": "CAD"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	cad = coin[0]["quote"]["CAD"]["price"] ;



	# Switzerland
	params = { "start" : monero_index, "limit" : 1, "convert": "CHF"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	chf = coin[0]["quote"]["CHF"]["price"] ;



	# Chinese
	params = { "start" : monero_index, "limit" : 1, "convert": "CNY"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	cny = coin[0]["quote"]["CNY"]["price"] ;



	# Japanese
	params = { "start" : monero_index, "limit" : 1, "convert": "JPY"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	jpy = coin[0]["quote"]["JPY"]["price"] ;



	# South Korea
	params = { "start" : monero_index, "limit" : 1, "convert": "KRW"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	krw = coin[0]["quote"]["KRW"]["price"] ;



	# India
	params = { "start" : monero_index, "limit" : 1, "convert": "INR"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	inr = coin[0]["quote"]["INR"]["price"] ;




	# Russian
	params = { "start" : monero_index, "limit" : 1, "convert": "RUB"} ;
	json = requests.get(url, params=params, headers=headers).json() ;

	coin = json["data"] ;
	rub = coin[0]["quote"]["RUB"]["price"] ;





	# Save entries into database
	with connection:
		update_database(connection, (usd, "USD")) ;
		update_database(connection, (eur, "EUR")) ;
		update_database(connection, (gbp, "GBP")) ;
		update_database(connection, (cad, "CAD")) ;
		update_database(connection, (aud, "AUD")) ;
		update_database(connection, (chf, "CHF")) ;
		update_database(connection, (cny, "CNY")) ;
		update_database(connection, (jpy, "JPY")) ;
		update_database(connection, (krw, "KRW")) ;
		update_database(connection, (inr, "INR")) ;
		update_database(connection, (rub, "RUB")) ;
		update_database(connection, (bitcoin, "BTC")) ;
		update_database(connection, (ethrium, "ETH")) ;

	

	# Print message
	print("\n\nFinished processing currencies. Time: " + str(time.ctime())) ;
	print("Will refresh in 1 hour.\n\n") ;


	# Refresh every hour
	# Source: https://www.tutorialspoint.com/python/time_sleep.htm
	time.sleep(3600) ;


















