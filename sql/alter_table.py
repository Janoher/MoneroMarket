# pip3 install requests
# Access database to save into the information
import requests  
import time  
import sqlite3  
from sqlite3 import Error  


# Make importing from moneromarket work as file path is now one back.
# Source: https://stackoverflow.com/questions/4383571/importing-files-from-different-folder
import sys  
sys.path.insert(1, '../')  


from moneromarket import db  
from moneromarket.database.models import Review  






# Source: https://www.sqlitetutorial.net/sqlite-python/update/
# Establish connection to database
def create_connection(db_file):
	connection = None  

	try:
		connection = sqlite3.connect(db_file)  

	except Error as error:
		print(error)  



	return connection  





# Initialize connection to the database...
connection = create_connection("../moneromarket/database/site.db")  

# Print out whether database connected or not
if connection:
	print("Sucessfully connected to the database! (:")  

else:
	print("Failed to connect to the database... ):")  









# source: https://pythontic.com/database/sqlite/alter%20table
# Just use this to add or remove columns, or add or remove tables without having to reset the entire database.
cur = connection.cursor()  
addColumn = "ALTER TABLE order_table ADD COLUMN amount_refunded VARCHAR(300) NULL"  

print("Successfully modified table!")  

cur.execute(addColumn)  









