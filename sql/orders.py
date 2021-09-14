# pip3 install requests
# Access database to save into the information
import requests ;
import time ;
import sqlite3 ;
from sqlite3 import Error ;


# Make importing from moneromarket work as file path is now one back.
# Source: https://stackoverflow.com/questions/4383571/importing-files-from-different-folder
import os ;
import sys ;
sys.path.insert(1, '../') ;


from moneromarket import db ;
from moneromarket.database.models import Order, Message, User, Post ;
from moneromarket.orders.utils import delete_picture_qrcode ;

# Monero
from monero.wallet import Wallet ;
from monero.backends.jsonrpc import JSONRPCWallet ;
from monero.daemon import Daemon ;
from monero.address import address ;

from cryptography.fernet import Fernet ;
import json ;
from moneromarket.config import config ;

from datetime import datetime, timedelta ;
from decimal import Decimal ;
import numpy ;




# Vendor no show, insuffiecient funds, unconfirmed    ======  ALL EQUAL REFUND!





# Source: https://www.sqlitetutorial.net/sqlite-python/update/
# Establish connection to database
def create_connection(db_file):
	connection = None ;

	try:
		connection = sqlite3.connect(db_file) ;

	except Error as error:
		print(error) ;



	return connection ;










def update_confirmations(connection, wallet, daemon):

	try:
		# Data needed
		key = config.get("FERNET_KEY") ;
		fernet=Fernet(key.encode())

		# Traffic wallet through TOR
		# daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050") ;
		# wallet = Wallet(port=28088) ;


		cur = connection.cursor() ;
		cur.execute("SELECT public_address, confirmations, account_number, qr_code, id FROM order_table WHERE (status = ? OR status = ?) AND confirmations < 10", ("PENDING", "WAITING FOR PAYMENT")) ;

		orders = cur.fetchall() ;


		count_for_no_incoming = 0 ;
		for order in orders:

			# If an incoming payment hasn't been received yet
			try:
				if not wallet.accounts[int(fernet.decrypt(order[2].encode()).decode())].incoming()[0]:
					count_for_no_incoming += 1 ;
					continue ;

			except IndexError:
				count_for_no_incoming += 1 ;
				continue ;


			#confirmation = wallet.accounts[int(fernet.decrypt(order[2].encode()).decode())].confirmations(wallet.accounts[int(fernet.decrypt(order[2].encode()).decode())].incoming(local_address=fernet.decrypt(order[0].encode()).decode())[0]) ;
			confirmation = wallet.confirmations(wallet.accounts[int(fernet.decrypt(order[2].encode()).decode())].incoming(local_address=fernet.decrypt(order[0].encode()).decode())[0]) ;
			print("confirmations: " + str(confirmation)) ;





			# Delete qr_code when confirmation is true
			qr_code = order[3] ;
			if confirmation != 0 and order[3] != "None":
				previous_picture = os.path.join("../moneromarket/", "static/img/qrcodes", order[3]) ;
				if os.path.exists(previous_picture):
					os.remove(previous_picture) ;

				# Change to None
				qr_code = "None" ;



			sql = ''' UPDATE order_table
			  SET confirmations = ?,
			  	  qr_code = ?,
			  	  status = ?
			WHERE id = ? '''


			cur = connection.cursor() ;
			if confirmation > 0:
				cur.execute(sql, (confirmation, qr_code, "PENDING", order[4])) ;
			else:
				cur.execute(sql, (confirmation, qr_code, "WAITING FOR PAYMENT", order[4])) ;
			connection.commit() ;



		print(str(len(orders) - count_for_no_incoming) + " confirmations were updated.") ;
		print(str(count_for_no_incoming) + " orders didn't receive a payment yet..\n") ;
		#sql = ''' UPDATE order_table
		#	  SET confirmations = wallet.confirmations(wallet.incoming(local_address=fernet.decrypt(public_address.encode()).decode())[0])
		#	WHERE confirmations < 10 '''

	except:
		print("Not connected to internet, try again later...") ;
		return False ;






# Update the currency price within the database
def check_if_confirmations_are_10(connection):

	try:
		# Data needed
		key = config.get("FERNET_KEY") ;
		fernet=Fernet(key.encode())



		# Select all orders to message 
		cur = connection.cursor() ;
		cur.execute("SELECT id, post_id, user_id, return_address, public_address, payment_id, buying_amount, vendor_id FROM order_table WHERE status = ? AND confirmations >= 10", ("PENDING",)) ;
		# get_order_sql = ''' SELECT id, post_id, user_id
		# 			   FROM order
		#			  WHERE status = "PENDING"
		#			    AND confirmations >= 10 '''



		# vendor_title = "New order request from " ;	# Insert username when generating new message...
		message_status = "UNOPENED" ;
		message_type = "TRANSACTION" ;
		message_admin = 1 ;	# ADMIN is user id 1
		# vendor_description = "Please fill out order acceptance form about the listing: <insert_post_id> here<insert_order_id>.\n\nYou have 24 hours to Accept AND Ship order AND provide tracking number/ID without penalty, and if over 24 hours but under 48 hours it’s with a 1%% FEE, and if accepted over 48 but under 72 hours it’s with a 2%% FEE, and if it’s over 72 hours the order is cancelled, Monero refunded to user and you are deducted a FEE on next order(s) you sell until the 3% FEE balance of the cancelled item is met." ;


		orders = cur.fetchall() ;

		#address_set = set() ;
		for order in orders:

			#if not order[4] in address_set:
			# Get post title and vendor id
			cur.execute("SELECT title, user_id FROM post WHERE id = ?", (order[1],)) ;
			post = cur.fetchone() ;

			#get_listing_info_sql = ''' SELECT title, user_id
			#					  FROM post
			#					 WHERE id = order[1] '''

			cur.execute("SELECT username FROM user WHERE id = ?", (post[1],)) ;
			vendor = cur.fetchone() ;
			
			#get_vendor_username_sql = ''' SELECT username
			#						 FROM user
			#						WHERE id = get_listing_info_sql[1] '''

			cur.execute("SELECT username FROM user WHERE id = ?", (order[2],)) ;
			buyer = cur.fetchone() ;

			#get_buyer_username_sql = ''' SELECT username
			#						FROM user
			#					   WHERE id = order[2] '''


			vendor_title = "New order request from " + buyer[0] ;
			# <Post id> <Order id>
			vendor_description = str(order[0]) + " " + str(order[1]) ;


			buyer_title = "Order #" + str(order[0]) + " request to " + str(vendor[0]) + " sent"
			buyer_description = ("Order #" + str(order[0]) + " '" + str(post[0]) + "'" + " was succesfully confirmed and has been processed, and a request has been sent" +
								" to vendor, and the vendor will have up to 72 hours to accept your request." +
								"\n\nIf the vendor accepts order before 24 hours, there will be no penalty for them." +
								"\n\nIf the vendor accepts order after 24 hours but before 48 hours, you will get a 1% bonus." + 
								"\nIf the vendor accepts order after 48 hours but before 72 hours, you will get a 3% bonus." + 
								"\nIf the vendor doesn't accept order after 72 hours, you will receive a refund with a 5% bonus." +
								"\n\nRefund address: " + str(fernet.decrypt(order[3].encode()).decode()) +
								"\nIf refund address is incorrect, please reply to message with Transaction ID and updated return address." +
								"\nPayment ID: #" + str(order[5])) ;


			vendor_title = fernet.encrypt(vendor_title.encode()).decode() ;
			vendor_description = fernet.encrypt(vendor_description.encode()).decode() ;
			buyer_title = fernet.encrypt(buyer_title.encode()).decode() ;
			buyer_description = fernet.encrypt(buyer_description.encode()).decode() ;


			create_vendor_message_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
																message_to, deleted_from_sender, deleted_from_reciever, 
																date_created, order_id)
										    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''



			create_buyer_message_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
																message_to, deleted_from_sender, deleted_from_reciever, 
																date_created, order_id)
										    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''




			cur = connection.cursor() ;
			cur.execute(create_vendor_message_sql, (vendor_title, vendor_description, message_status, 
													message_type, message_admin, post[1], False, False, datetime.utcnow(), order[0])) ;
			# connection.commit() ;

			cur = connection.cursor() ;
			cur.execute(create_buyer_message_sql, (buyer_title, buyer_description, message_status, 
												   message_type, message_admin, order[2], False, False, datetime.utcnow(), order[0])) ;
				

				#address_set.add(order[4]) ;



			# Get post id and title
			cur = connection.cursor() ;
			cur.execute("SELECT id, currently_selling FROM user WHERE id = ?", (order[7], )) ;
			vendor = cur.fetchone() ;

			cur = connection.cursor() ;
			cur.execute("SELECT id, currently_buying FROM user WHERE id = ?", (order[2], )) ;
			buyer = cur.fetchone() ;

			update_buys_sql = ''' UPDATE user
						   	   	     SET currently_buying = ?
						 	       WHERE id = ? '''

			update_sale_sql = ''' UPDATE user
						   	   	     SET currently_selling = ?
						 	       WHERE id = ? '''



			cur.execute(update_sale_sql, (int(vendor[1]) + int(fernet.decrypt(order[6].encode()).decode()), order[7], )) ; 
			cur.execute(update_buys_sql, (int(buyer[1]) + int(fernet.decrypt(order[6].encode()).decode()), order[2] )) ;





			update_order_sql = ''' UPDATE order_table
							   SET status = ?,
							   	   waiting_for_vendor = ?,
							   	   recent_update = ?
							 WHERE id = ? '''

			date_current = datetime.utcnow() ;
			cur = connection.cursor() ;
			cur.execute(update_order_sql, ("WAITING FOR VENDOR", date_current, date_current, order[0])) ;
			connection.commit() ;

			
			#update_post_supply_sql = ''' UPDATE post
			#						 SET supply = ?
			#					   WHERE id = ? '''

			#cur.execute("SELECT supply FROM post WHERE id = ?", (order[1], )) ;
			#post_supply = cur.fetchone() ;

			#cur = connection.cursor() ;
			#cur.execute(update_post_supply_sql, (post_supply[0] - 1, order[1])) ;



	except:
		print("Not connected to internet, try again later...") ;
		return False ;






def no_confirmations(connection):

	try:
		# Data needed
		key = config.get("FERNET_KEY") ;
		fernet=Fernet(key.encode())

		# Select all orders to message 
		cur = connection.cursor() ;

		# If date_ordered has passed 30 minutes
		cur.execute("SELECT id, post_id, user_id, payment_id, public_address, qr_code, buying_amount FROM order_table WHERE status = ? AND confirmations = 0 AND date_ordered < ?", ("WAITING FOR PAYMENT", datetime.utcnow() + timedelta(hours=-2, minutes=-10))) ;	



		orders = cur.fetchall() ;

		address_set = set() ;
		for order in orders:
			print(order[3]) ;

			if not order[3] in address_set:

				message_user_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
																	message_to, deleted_from_sender, deleted_from_reciever, 
																	date_created, order_id)
											    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''



				message_title = "No transaction was ever recieved for Payment ID: #" + str(order[3]) ;
				message_description = ("No payment was ever recieved for Payment ID: #" + str(order[3]) + " after 2 hours of purchase."
							  ".\n\nPlease check your payment in the payment section in the orders tab for more info.\nIf you have a transaction number, please respond to this message as your Monero might have been sent to a different address by mistake and we might have the transaction under a different address.\n\n" +
							  "Public address: " + fernet.decrypt(order[4].encode()).decode()) ;
				message_admin = 1 ;


				# Encrypt message
				message_title = fernet.encrypt(message_title.encode()).decode() ;
				message_description = fernet.encrypt(message_description.encode()).decode() ;



				cur = connection.cursor() ;
				cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
														"TRANSACTION", message_admin, order[2], False, False, datetime.utcnow(), order[0])) ;
				
				address_set.add(order[3]) ;




			cur = connection.cursor() ;
			cur.execute("SELECT id, post_id, gallery_1, gallery_2, gallery_3, gallery_4, gallery_5, gallery_6, gallery_7, gallery_8, gallery_9 FROM order_post_details WHERE payment_id = ?", (order[3], )) ;
			pend_galleries_all = cur.fetchall() ;



			# Commence deletion of pictures, and then delete from database
			for pending_galleries in pend_galleries_all:
				for index in range(2, len(pending_galleries)):

					if pending_galleries[index] == None:
						break ;

					previous_picture = os.path.join("../moneromarket/", "static/img/posts/originals", pending_galleries[index]) ;
					if os.path.exists(previous_picture):
						os.remove(previous_picture) ;


				
				cur = connection.cursor() ;
				cur.execute("DELETE FROM order_post_details WHERE id = ?", (pending_galleries[0], )) ;




			# Delete qr_code when confirmation is true
			if order[5] != None:
				#Delete old profile picture
				previous_picture = os.path.join("../moneromarket/", "static/img/qrcodes", order[5])
				if os.path.exists(previous_picture):
					os.remove(previous_picture) ;



			# Unpend listed items.
			cur.execute("SELECT pending FROM post WHERE id = ?", (order[1], )) ;
			post_sql = cur.fetchone() ;

			update_post_sql = ''' UPDATE post
							   SET pending = ?
							 WHERE id = ? '''
			cur.execute(update_post_sql, (int(post_sql[0]) - int(fernet.decrypt(order[6].encode()).decode()), order[1], )) ;


			update_order_sql = ''' UPDATE order_table
							   SET status = ?,
							   	   order_cancelled = ?,
							   	   recent_update = ?,
							   	   qr_code = ?
							 WHERE id = ? '''


			date_current = datetime.utcnow() ;
			cur = connection.cursor() ;
			cur.execute(update_order_sql, ("NO PAYMENT", date_current, date_current, "None", order[0], )) ;
			connection.commit() ;


	except:
		print("Not connected to internet, try again later..") ;
		return False ;






# 4 hours might be overkill, but done just in case the Monero network experiences delays
def confirmations_less_than_10_in_6_hours(connection, wallet, daemon):
	
	try:
		# Data needed
		key = config.get("FERNET_KEY") ;
		fernet=Fernet(key.encode())

		# Select all orders to message 
		cur = connection.cursor() ;

		# If date_ordered has passed 4 hours
		cur.execute("SELECT id, post_id, user_id, payment_id, confirmations FROM order_table WHERE status = ? AND confirmations < 10 AND date_ordered < ?", ("PENDING", datetime.utcnow() + timedelta(hours=-6))) ;


		orders = cur.fetchall() ;


		address_set = { } ;
		for order in orders:

			# Don't repeat same orders
			if not order[3] in address_set:
				# Get current network fee
				network_fee = wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee ;

				message_user_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
																	message_to, deleted_from_sender, deleted_from_reciever, 
																	date_created, order_id)
											    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''


				message_title = "Payment could not be confirmed for Payment ID: #" + str(order[3]) ;
				message_description = ("Payment could not be confirmed after 4 hours of purhcase.\nTotal confirmations: " + str(order[4]) +
									   "\nConfirmations neeeded: 10\n\nReasoning as to why we don't accept payments without 10 confirmations" +
									   " is because of risk of fraud. Please see how Monero works in our footer section." +
									   "\nWe will refund your Monero if the confirmations do reach 10." +
									   "\n\nNote: Excess amount will only be refunded however if it is more than the current slowest network transaction fee, and the network fee is subject to change over time..." +
										"\nCurrent network transaction fee: " + str(network_fee)) ;
				message_admin = 1 ;


				# Encrypt message
				message_title = fernet.encrypt(message_title.encode()).decode() ;
				message_description = fernet.encrypt(message_description.encode()).decode() ;


				cur = connection.cursor() ;
				cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
														"TRANSACTION", message_admin, order[2], False, False, datetime.utcnow(), order[0])) ;
				

				address_set[order[3]] = True ;





			# Unpend listed items.
			cur.execute("SELECT pending FROM post WHERE id = ?", (order[1], )) ;
			post_sql = cur.fetchone() ;

			update_post_sql = ''' UPDATE post
							   SET pending = ?
							 WHERE id = ? '''
			cur.execute(update_post_sql, (post_sql[0] - int(fernet.decrypt(order[6].encode()).decode()), order[1], )) ;




			update_order_sql = ''' UPDATE order_table
							   SET status = ?,
							   	   recent_update = ?
							 WHERE id = ? '''


			date_current = datetime.utcnow() ;
			cur = connection.cursor() ;
			cur.execute(update_order_sql, ("UNCONFIRMED", date_current, order[0])) ;
			connection.commit() ;


	except:
		print("Not connected to internet, try again later...") ;
		return False ;



# We use a set to prevent messages being sent multiple times to the same order, howerver...
# We want the orders to all update, so that's why we don't just continue...
# Instead, we just skip the message creation.
def check_payment_price(connection, wallet, daemon):

	try:
		# Data needed
		key = config.get("FERNET_KEY") ;
		fernet=Fernet(key.encode()) ;

		# Traffic wallet through TOR
		# daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050") ;
		# wallet = Wallet(port=28088) ;


		# Get all orders that the payment has been recieved but not checked.
		cur = connection.cursor() ;
		cur.execute("SELECT id, payment_id, public_address, post_id, user_id, account_number, return_address, total_amount_for_payment_id, buying_amount FROM order_table WHERE status = ? AND confirmations > 0 AND total_amount_received IS NULL", ("PENDING", )) ;
		orders = cur.fetchall() ;



		address_set = set() ;
		for order in orders:

			# Don't repeat same payment...
			#if order[1] in address_set:
			#	continue ;



			incoming = wallet.accounts[int(fernet.decrypt(order[5].encode()).decode())].incoming(local_address=fernet.decrypt(order[2].encode()).decode()) ;
			print(incoming) ;

			# Get total payment needed
			total_price = float(fernet.decrypt(order[7].encode()).decode()) ;



			# Deny
			if float(incoming[0].amount) < float(total_price):
				# Don't repeat same message to order
				if not order[1] in address_set:

					# Get current network fee
					network_fee = wallet.accounts[0].transfer(wallet.accounts[1].address(), 0.000000000001, priority=1, relay=False)[0].fee ;
					print(network_fee) ;

					# Prepare message template
					message_user_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
															   message_to, deleted_from_sender, deleted_from_reciever, 
															   date_created, order_id)
										   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
					message_admin = 1 ;


					# Fill in message template
					message_title = "Payment was less than what was required for Payment ID: #" + str(order[1]) ;
					message_description = ("Orders have been cancelled...\nPayment recieved was " + str(numpy.format_float_positional(float(incoming[0].amount), trim='-')) +
										   ".\nTotal amount neeeded: " + str(numpy.format_float_positional(float(total_price), trim='-')) + ".\n\nPlease check details for Payment ID: " + str(order[1]) +
										   " for more information.\nPayment will be refunded after 24 hours with a 2%% FEE to the return address: " + 
										   fernet.decrypt(order[6].encode()).decode() + "\nIf return address is incorrect, please reply to ADMIN " + 
										   "with your Transaction ID to fix address." + 
										   "\n\nNote: Amount will only be refunded however if it is more than the current slowest network transaction fee, and the network fee is subject to change within 24 hours..." +
										   "\nCurrent network transaction fee: " + str(network_fee) + " XMR") ;

					# Encrypt message
					message_title = fernet.encrypt(message_title.encode()).decode() ;
					message_description = fernet.encrypt(message_description.encode()).decode() ;
				
					cur = connection.cursor() ;
					cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
														"TRANSACTION", message_admin, order[4], False, False, datetime.utcnow(), order[0])) ;


					# Transfer 5% of incoming payment to MoneroMarket's profit account for a less than amount required fee.
					# insuffiecient_funds_fee = 0.05 ;
					# transaction = wallet.accounts[int(fernet.decrypt(order[5].encode()).decode())].transfer(wallet.accounts[0].address(), total_price * insuffiecient_funds_fee) ;
					# print(transaction) ;


				# status = "PAYMENT INSUFFICIENT FUNDS"
				update_order_sql_cancelled = ''' UPDATE order_table
							   	   SET status = ?,
							   	   	   order_cancelled = ?,
							   	   	   recent_update =?,
								   	   total_amount_received = ?
							 	   WHERE id = ? '''

				# Unpend listed items.
				cur.execute("SELECT post_id, buying_amount from order_table WHERE payment_id = ?", (order[1], )) ;
				correlated_orders_payment_id = cur.fetchall() ;

				for insufficient_post in correlated_orders_payment_id:
					cur.execute("SELECT pending FROM post WHERE id = ?", (insufficient_post[0], )) ;
					post_sql = cur.fetchone() ;

					update_post_sql = ''' UPDATE post
									   SET pending = ?
									 WHERE id = ? '''
					cur.execute(update_post_sql, (post_sql[0] - int(fernet.decrypt(insufficient_post[1].encode()).decode()), insufficient_post[0], )) ;




				date_current = datetime.utcnow() ;
				cur = connection.cursor() ;
				cur.execute(update_order_sql_cancelled, ("INSUFFICIENT FUNDS", date_current, date_current, fernet.encrypt(str(incoming[0].amount).encode()).decode(), order[0])) ;
			
				print("updated database") ;




			# Accepted
			elif float(incoming[0].amount) == float(total_price):
				update_order_sql = ''' UPDATE order_table
								          SET status = ?,
								   	          total_amount_received = ?
								        WHERE id = ? '''

				cur = connection.cursor() ;
				cur.execute(update_order_sql, ("PENDING", fernet.encrypt(str(incoming[0].amount).encode()).decode(), order[0])) ;





			# Refund
			elif float(incoming[0].amount) > float(total_price):
				# Don't repeat same message to order
				if not order[1] in address_set:

					# Get current network fee
					network_fee = wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee ;

					# Prepare message template
					message_user_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
															   message_to, deleted_from_sender, deleted_from_reciever, 
															   date_created, order_id)
										   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
					message_admin = 1 ;


					# Fill in message template
					message_title = "Payment was more than what was required for Payment ID: #" + str(order[1]) ;
					message_description = ("Payment recieved was " + str(numpy.format_float_positional(float(incoming[0].amount), trim='-')) +
										   ".\nTotal amount neeeded: " + str(numpy.format_float_positional(float(total_price), trim='-', precision=8)) + ".\n\nPlease check details for Payment ID: " + str(order[1]) +
										   " for more information.\nOrders will process like normal, and excess payment will be refunded after confirmations reach 10/10 and after 24 hours with NO FEE to the return address: " + 
										   fernet.decrypt(order[6].encode()).decode() + "\nIf return address is incorrect, please reply to us " + 
										   "with your Transaction ID to fix address." + 
										   "\n\nNote: Excess amount will only be refunded however if it is more than the current slowest network transaction fee, and the network fee is subject to change within 24 hours..." +
										   "\nCurrent network transaction fee: " + str(network_fee) + " XMR") ;


					# Encrypt message
					message_title = fernet.encrypt(message_title.encode()).decode() ;
					message_description = fernet.encrypt(message_description.encode()).decode() ;



					cur = connection.cursor() ;
					cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
														"TRANSACTION", message_admin, order[4], False, False, datetime.utcnow(), order[0])) ;


				# status = "PAYMENT LESS THAN REQUIRED"
				update_order_excess_sql = ''' UPDATE order_table
							   SET status = ?,
							   	   total_amount_received = ?,
							   	   excess_received = ?
							 WHERE id = ? '''

				cur = connection.cursor() ;
				cur.execute(update_order_excess_sql, ("PENDING", fernet.encrypt(str(incoming[0].amount).encode()).decode(), datetime.utcnow(), order[0])) ;



			

			address_set.add(order[1]) ;


			connection.commit() ;




	except:
		print("Not connected to internet, try again later (Payment price).....") ;
		return False ;

















def waiting_for_vendor_72_hours(connection):

	try:
		# Data needed
		key = config.get("FERNET_KEY") ;
		fernet=Fernet(key.encode())



		# Select all orders to message where the vendor hasn't responded in 72 hours
		cur = connection.cursor() ;
		cur.execute("SELECT id, post_id, user_id, waiting_for_vendor, return_address, buying_amount, price_per_item, vendor_id FROM order_table WHERE status = ? AND waiting_for_vendor < ?", ("WAITING FOR VENDOR",  datetime.utcnow() + timedelta(hours=-72), )) ;
		orders = cur.fetchall() ;



		for order in orders: 
			# Get vendor info
			cur = connection.cursor() ;
			cur.execute("SELECT user_id FROM post WHERE id = ?", (order[1], )) ;
			vendor = cur.fetchone() ;



			# Prepare message template
			message_user_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
																message_to, deleted_from_sender, deleted_from_reciever, 
																date_created, order_id)
								   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''


			message_vendor_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
																message_to, deleted_from_sender, deleted_from_reciever, 
																date_created, order_id)
								   	 VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
			message_admin = 1 ;









			# Unpend listed items.
			cur.execute("SELECT pending FROM post WHERE id = ?", (order[1], )) ;
			post_sql = cur.fetchone() ;

			update_post_sql = ''' UPDATE post
							   SET pending = ?
							 WHERE id = ? '''
			cur.execute(update_post_sql, (post_sql[0] - int(fernet.decrypt(order[5].encode()).decode()), order[1], )) ;


			# Get post id and title
			cur = connection.cursor() ;
			cur.execute("SELECT id, currently_selling, no_response FROM user WHERE id = ?", (order[7], )) ;
			vendor = cur.fetchone() ;

			cur = connection.cursor() ;
			cur.execute("SELECT id, currently_buying FROM user WHERE id = ?", (order[2], )) ;
			buyer = cur.fetchone() ;

			update_buys_sql = ''' UPDATE user
						   	   	     SET currently_buying = ?
						 	       WHERE id = ? '''

			update_sale_sql = ''' UPDATE user
						   	   	     SET currently_selling = ?,
						   	   	     	 no_response = ?
						 	       WHERE id = ? '''



			cur.execute(update_sale_sql, (int(vendor[1]) - int(fernet.decrypt(order[5].encode()).decode()), vendor[2] + 1, order[7], )) ; 
			cur.execute(update_buys_sql, (int(buyer[1]) - int(fernet.decrypt(order[5].encode()).decode()), order[2] )) ;


			










			user_title = "Order cancelled from vendor not responding" ;
			vendor_title = "Order cancelled from not responding within 72 hours" ;

			user_description = ("Order #" + str(order[0]) + " '" + order[6] + "'"  + " has been cancelled as the vendor has neither accepted nor declined the request within 72 hours.\n" +
							   "Monero will be refunded with no charge in 24 hours, and a 3%% FEE will be applied to the vendor to pay you back for " +
							   "wasting your time.\nWe apologize for any inconviniences." + "\n\nRefund address: " + 
							   fernet.decrypt(order[4].encode()).decode() + "\nIf address is incorrect, please message us with Transaction ID" +
							   " to resolve refund address.") ;

			vendor_description = ("Order #" + str(order[0]) + " '" + order[6] + "'" + " has been cancelled as you have not neither accepted nor declined the request within 72 hours.\n" +
								 "Monero will be refunded to user and a 5%% FEE will be added to your next order to cover for the " +
								 "inconvinience provided to the user.") ;


			# Encrypt message
			user_title = fernet.encrypt(user_title.encode()).decode() ;
			user_description = fernet.encrypt(user_description.encode()).decode() ;

			vendor_title = fernet.encrypt(vendor_title.encode()).decode() ;
			vendor_description = fernet.encrypt(vendor_description.encode()).decode() ;



			cur = connection.cursor() ;
			cur.execute(message_user_sql, (user_title, user_description, "VENDOR NO SHOW", 
												"TRANSACTION", message_admin, order[2], False, False, datetime.utcnow(), order[0])) ;

			cur = connection.cursor() ;
			cur.execute(message_vendor_sql, (vendor_title, vendor_description, "NO RESPONSE", 
												"TRANSACTION", message_admin, vendor, False, False, datetime.utcnow(), order[0])) ;



			user_fee_sql = ''' INSERT INTO user_fee(user_id, vendor_id, order_id, total_amount_owed_5_percent, total_amount_paid_off, date_reserved)
								    		 VALUES(?, ?, ?, ?, ?, ?) '''

			# Get 5 percent of total order
			total_amount = fernet.encrypt(str(0.05 * (order[5] * order[6])).encode()).decode() ;
			paid_off = fernet.encrypt(str(0.00).encode()).decode() ;

			cur = connection.cursor() ;
			cur.execute(user_fee_sql, (order[2], vendor[0], order[0], total_amount, total_amount_paid_off, datetime.utcnow())) ;



			# status = "PAYMENT INSUFFICIENT FUNDS"s
			update_order_sql = ''' UPDATE order_table
						   	   SET status = ?,
						   	   	   order_cancelled = ?,
						   	   	   recent_update = ?
						 	 WHERE id = ? '''

			date_current = datetime.utcnow() ;
			cur = connection.cursor() ;
			cur.execute(update_order_sql, ("VENDOR NO SHOW", date_current, date_current, order[0])) ;



			connection.commit() ;



	except:
		print("Not connected to internet, try again later...") ;
		return False ;









def refund_in_24_hours(connection, wallet, daemon):
	# Data needed
	message_admin = 1 ;
	key = config.get("FERNET_KEY") ;
	fernet=Fernet(key.encode()) ;

	# Traffic wallet through TOR
	# daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050") ;
	# wallet = Wallet(port=28088) ;





	# Select all orders where vendor did not accept the order
	cur = connection.cursor() ;
	cur.execute("SELECT id, public_address, return_address, account_number, user_id, vendor_id, buying_amount, price_per_item FROM order_table WHERE status = ? AND order_cancelled < ? AND escrow_released IS NULL", ("VENDOR NO SHOW",  datetime.utcnow() + timedelta(hours=-24), )) ;
	orders_not_accepted = cur.fetchall() ;


	# Select all orders where insufficient funds
	cur = connection.cursor() ;
	cur.execute("SELECT id, public_address, return_address, account_number, user_id, payment_id FROM order_table WHERE status = ? AND order_cancelled < ? AND escrow_released IS NULL", ("INSUFFICIENT FUNDS",  datetime.utcnow() + timedelta(hours=-24), )) ;
	orders_insufficient_funds = cur.fetchall() ;
	

	# Select all orders where excess funds
	cur = connection.cursor() ;
	cur.execute("SELECT id, public_address, return_address, payment_id, account_number, user_id, payment_id FROM order_table WHERE excess_received < ? AND excess_received_refunded IS NULL", (datetime.utcnow() + timedelta(hours=-24), )) ;
	orders_excess_received = cur.fetchall() ;


	# Select all orders where employess accepted refund request from buyer
	cur = connection.cursor() ;
	cur.execute("SELECT id, public_address, return_address, account_number, user_id FROM order_table WHERE status = ? AND order_refunded < ? AND escrow_released IS NULL", ("REFUNDING",  datetime.utcnow() + timedelta(hours=-24), )) ;
	orders_refunding = cur.fetchall() ;



	



	# Prepare message template
	message_user_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
														message_to, deleted_from_sender, deleted_from_reciever, 
														date_created, order_id)
						   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''






	# Dictionary to store repeated orders 
	address_dictionary = { } ;
	# Orders that never were accepted
	for order in orders_not_accepted:

		# Don't repeat same orders
		if not order[1] in address_dictionary:
			#incoming_amount = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].incoming(local_address=fernet.decrypt(order[1].encode()).decode())[0].amount ;
			transaction = None ;

			network_fee = float(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee) ;
			if wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].balance() > float(fernet.decrypt(order[6].encode()).decode()) + float(fernet.decrypt(order[7].encode()).decode()) + network_fee:
				transaction = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].transfer(fernet.decrypt(order[2].encode()).decode(), float(fernet.decrypt(order[6].encode()).decode()) + float(fernet.decrypt(order[7].encode()).decode()), 1) ;
			else:
				transaction = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].sweep_all(fernet.decrypt(order[2].encode()).decode(), 1) ;

			# Add to dictionary
			address_dictionary[order[1]] = datetime.utcnow() ;



			message_title = "Monero Refunded, Vendor Did Not Accept Order." ;
			message_description = (str(incoming_amount - transaction[0].fee) + " Monero was refunded at " + str(datetime.strftime('%H:%M:%S')) + " UTC." + 
								  "\nOrder #" + str(order[0]) +  " '" + order[6] + "'" +
								  "\nRefund address: " + (str(fernet.decrypt(order[2].encode().decode())) if order[2] else "Your account wallet.") + 
								  "\nTransaction network fee: " + str(transaction[0].fee) + "\nTransaction ID: " + str(transaction)) ;

			# Encrypt message
			message_title = fernet.encrypt(message_title.encode()).decode() ;
			message_description = fernet.encrypt(message_description.encode()).decode() ;

			cur = connection.cursor() ;
			cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
									   "REFUND", message_admin, order[4], False, False, datetime.utcnow(), order[0])) ;


			# To Vendor
			message_title = "Order Cancelled, You Did Not Accept Order From Buyer." ;
			message_description = ("Order #" + str(order[0]) +  " '" + order[6] + "'" + " funds were released back for not accepting order after 72 hours.") ;

			# Encrypt message
			message_title = fernet.encrypt(message_title.encode()).decode() ;
			message_description = fernet.encrypt(message_description.encode()).decode() ;

			cur = connection.cursor() ;
			cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
									   "REFUND", message_admin, order[5], False, False, datetime.utcnow(), order[0])) ;


		# status = "PAYMENT INSUFFICIENT FUNDS"
		update_order_sql = ''' UPDATE order_table
					   	   	      SET escrow_released = ?,
					   	   	      	  recent_update = ?
					 	        WHERE id = ? '''

		date_current = datetime.utcnow() ;
		cur = connection.cursor() ;
		cur.execute(update_order_sql, (date_current, date_current, order[0])) ;


		


		connection.commit() ;






	address_dictionary.clear() ;
	# Received less than what was required
	for order in orders_insufficient_funds:

		# Don't repeat same orders
		if not order[1] in address_dictionary:

			incoming_amount = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].incoming(local_address=fernet.decrypt(order[1].encode()).decode())[0].amount ;
			transaction = None ;
			print(incoming_amount) ;
			network_fee = float(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee) ;

			
			# If balance isn't unlocked for whatever odd reason, don't bother computing transaction
			if wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].balance(unlocked=True) == 0:
				print("Wallet unlocked for insuffiecient funds == 0") ;
				address_dictionary[order[1]] = datetime.utcnow() ;
				continue ;
			
			# Check to see if there is enough in unlocked balance. Should never happen, but check here so that server doesn't crash just in case.
			# Change to 2 --> 3 later
			insufficient_amount = False ;
			network_fee = float(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee) ;
			if wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].balance(unlocked=True) <= network_fee + network_fee + float(incoming_amount) * 0.02:
				
				# Sweep all since amount was lower than fee combined.
				try:
					transaction = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].sweep_all(wallet.accounts[0].address(), 1) ;
					insufficient_amount = True ;

				except:
					print("Cannot finish transaction, amount received is less than slowest priority ): ...") ;

					# ToDo:
					# Add a table later to keep track of all wallet accounts that have receieved an insufficient amount that is less than slowest
					# network fee, unmark said order from being repeated again in this loop, and store information to try and send out again when
					# network fee gets lowered years later.
					address_dictionary[order[1]] = datetime.utcnow() ;
					continue ;

			
			else:
				try:
					transaction = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].transfer(fernet.decrypt(order[2].encode()).decode(), float(incoming_amount) - network_fee - float(incoming_amount) * 0.02) ;
					print("insuffiecient funds refunded.")
					#print(transaction) ;

					sweep_all_sql = ''' INSERT INTO sweep_all(account_number)
								  			  VALUES(?) '''
					cur = connection.cursor() ;
					cur.execute(sweep_all_sql, (order[3], )) ;


				except:
					print("Cannot finish transaction, daemon not fully syncronized, please try again later..") ;
					return False ;

				














			# Add to dictionary
			time_now = datetime.utcnow() ;
			address_dictionary[order[1]] = time_now ;



			if insufficient_amount == True:
				message_title = "Insufficient Funds, Monero Could NOT Be Refunded" ;
				message_description = (str(incoming_amount) + " Monero could not be refunded because amount received is less than the slowest network * 2 fee plus 2%% FEE." + 
									  "\nPayment ID #" + str(order[5]) +
									  "\nNetwork fee: " + str(network_fee)) ;

			else:
				message_title = "Insufficient Funds, Monero Refunded" ;
				message_description = (str(float(incoming_amount) - network_fee - float(incoming_amount) * 0.02) + " Monero was refunded at " + str(time_now.strftime('%H:%M:%S')) + " UTC." + 
									  "\nPayment ID #" + str(order[5]) +
									  "\nRefund address: " + (str(fernet.decrypt(order[2].encode()).decode()) if order[2] else "Your account wallet.") + 
									  "\nRefund fee: " + str(incoming_amount_fee) + 
									  "\nTransaction network fee: " + transaction[0].fee + "\nTransaction ID: " + str(transaction)) ;


			# Encrypt message
			message_title = fernet.encrypt(message_title.encode()).decode() ;
			message_description = fernet.encrypt(message_description.encode()).decode() ;

			cur = connection.cursor() ;
			cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
										   "REFUND", message_admin, order[4], False, False, datetime.utcnow(), order[0])) ;




		# status = "PAYMENT INSUFFICIENT FUNDS"
		update_order_sql = ''' UPDATE order_table
					   	   	      SET escrow_released = ?,
					   	   	      	  recent_update = ?,
					   	   	      	  transaction_id =?,
					   	   	      	  amount_refunded = ?
					 	        WHERE id = ? '''

		date_current = datetime.utcnow() ;
		cur = connection.cursor() ;
		cur.execute(update_order_sql, (date_current, date_current, fernet.encrypt(str(transaction).encode()).decode(), fernet.encrypt(str(transaction[0].amount).encode()).decode(), order[0])) ;



		connection.commit() ;








	# Excess amount.
	address_dictionary.clear() ;
	for order in orders_excess_received:

		# Don't repeat same orders
		if not order[1] in address_dictionary:
		
			# Get a list of the orders that have the same payment id
			cur.execute("SELECT id, price_per_item, buying_amount, return_address FROM order_table WHERE payment_id = ?", (order[2], )) ;
			correlated_orders = cur.fetchall() ;


			# Add up price
			total_price = 0.0 ;
			for correlated in correlated_orders:
				total_price = total_price + (float(fernet.decrypt(correlated[1].encode()).decode()) * float(fernet.decrypt(correlated[2].encode()).decode())) ;


			network_fee = float(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee) ;

			# Get fee info to subtract for receiving users blah blah blah.
			# Prepare to send transaction
			incoming_amount = wallet.accounts[int(fernet.decrypt(order[4].encode()).decode())].incoming(local_address=fernet.decrypt(order[1].encode()).decode())[0].amount ;
			transaction_actual = None ;
			
			message_title = None ;
			message_description = None ;

			date_current = datetime.utcnow() ;


			# Relay equals false so that transaction doesn't go through right away, we just get the transaction network fee and then subtract that from actual amount and then resend to the actual daemon Monero TOR network! (:
			if total_price + network_fee > incoming_amount:
				transaction_prototype = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].transfer(wallet.accounts[int(fernet.decrypt(order[2].encode()).decode())].address(), Decimal(incoming_amount - total_price), relay=False) ;
				transaction_actual = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].transfer(wallet.accounts[int(fernet.decrypt(order[2].encode()).decode())].address(), Decimal(incoming_amount - total_price - transaction_prototype[0].fee), relay=True) ;
			
				message_title = "Excess Monero Refunded" ;
				message_description = (str(incoming_amount) + " Excess Monero was refunded at " + str(date_current.strftime('%H:%M:%S')) + " UTC." + 
								 "\nPayment ID #" + str(order[5]) +
								  "\nRefund address: " + (str(fernet.decrypt(order[2].encode().decode())) if order[2] else "Your account wallet.") + 
								  "\nAmount: " + str(float(incoming_amount) - float(total_price)) + 
								  "\nTransaction network fee: " + str(transaction_actual[0].fee)) ;
			

			else:
				message_title = "Excess Monero NOT Refunded" ;
				message_description = ("Excess Monero refund was attempted at " + str(date_current.strftime('%H:%M:%S')) + " UTC." + 
								 "\nPayment ID #" + str(order[5]) + 
								  "\nAmount: " + str(float(incoming_amount) - float(total_price)) + 
								  "\nTransaction network fee: " + str(network_fee) +
								  "\nExcess Monero received was less than transaction network fee, thus no Monero can be refunded... We apologize for the inconvinience..") ;

			




			# Add to dictionary
			address_dictionary[order[1]] = datetime.utcnow() ;


			# Encrypt message
			message_title = fernet.encrypt(message_title.encode()).decode() ;
			message_description = fernet.encrypt(message_description.encode()).decode() ;

			cur = connection.cursor() ;
			cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
										   "REFUND", message_admin, order[5], False, False, date_current, order[0])) ;




		# Update time or refund without releasing escrow
		update_order_excess_sql = ''' UPDATE order_table
					   	   	             SET excess_received_refunded = ?,
					   	   	             	 transaction_id = ?
					 	        	   WHERE id = ? '''



		cur = connection.cursor() ;
		if total_price + network_fee > incoming_amount:
			cur.execute(update_order_excess_sql, (datetime.utcnow(), fernet.encrypt(str(transaction_actual).encode()).decode(), order[0])) ;
		else:
			cur.execute(update_order_excess_sql, (datetime.utcnow(), None, order[0])) ;



		


		connection.commit() ;






	address_dictionary.clear() ;
	for order in orders_refunding:

		# Don't repeat same orders
		if order[1] in address_dictionary:
			continue ;


		incoming_amount = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].incoming(local_address=fernet.decrypt(order[1].encode()).decode())[0].amount ;
		transaction = None ;

		if order[2] == None:
			transaction = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].sweep_all(wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].address(), 1) ;
		else:
			transaction = wallet.accounts[int(fernet.decrypt(order[3].encode()).decode())].sweep_all(fernet.decrypt(order[2].encode()).decode(), 1) ;


		# Add to dictionary
		address_dictionary[order[1]] = datetime.utcnow() ;



		# sweep_all can't get transaction fee, which is stupid, so we have to get the fee from the database and then send that info through message
		cur = connection.cursor() ;
		cur.execute("SELECT price FROM network_fee WHERE id = ?", (1, )) ;
		network_fee = cur.fetchone() ;
		

		message_title = "Monero Refunded" ;
		message_description = (str(incoming_amount) + " Monero was refunded at " + str(datetime.strftime('%H:%M:%S')) + " UTC." + 
							  "\nOrder #" + str(order[0])  + " '" + order[6] + "'" +
							  "\nRefund address: " + (str(fernet.decrypt(order[2].encode().decode())) if order[2] else "Your account wallet.") + 
							  "\nAmount: " + incoming_amount - total_price + 
							  "\nTransaction network fee: " + str(network_fee[0])) ;



		# Encrypt message
		message_title = fernet.encrypt(message_title.encode()).decode() ;
		message_description = fernet.encrypt(message_description.encode()).decode() ;



		# Update time or refund without releasing escrow
		update_order_excess_sql = ''' UPDATE order_table
					   	   	             SET escrow_released = ?,
					   	   	             	 recent_update = ?
					 	        	   WHERE id = ? '''


		date_current = datetime.utcnow() ;
		cur = connection.cursor() ;
		cur.execute(update_order_sql, (date_current, date_current, address_dictionary[order[1]])) ;



		cur = connection.cursor() ;
		cur.execute(message_user_sql, (message_title, message_description, "ORDER REFUNDED", 
									   "REFUND", message_admin, order[4], False, False, datetime.utcnow(), order[0])) ;



		connection.commit() ;




	#except:
	#	print("Not connected to internet, try again later...") ;
	#	return False ;























































def releasing_funds(connection, wallet, daemon):
	# Data needed
	key = config.get("FERNET_KEY") ;
	fernet=Fernet(key.encode()) ;


	# Select all orders where vendor did not accept the order
	cur = connection.cursor() ;
	cur.execute("SELECT DISTINCT account_number FROM order_table WHERE escrow_released IS NULL AND (status = ? OR (auto_finalization_timer < ? AND buyer_disputed IS NULL))", ("RELEASING FUNDS",  datetime.utcnow(), )) ;
	accounts = cur.fetchall() ;


	print("Length of releasing funds: " + str(len(accounts))) ;



	# Go through each order that needs to have funds released
	for account in accounts:

		# If balance isn't unlocked for whatever odd reason, don't bother computing transaction
		if wallet.accounts[int(fernet.decrypt(account[0].encode()).decode())].balance(unlocked=True) == 0:
			print("Wallet unlocked == 0") ;
			continue ;



		# Get details for each order
		cur = connection.cursor() ;
		cur.execute("SELECT id, buying_amount, price_per_item, total_amount_of_orders_for_payment_id, user_id, vendor_id, return_address, vendor_address, auto_finalization_timer, percentage_to_buyer, percentage_to_vendor, cost_for_shipping_to_buyer, cost_for_shipping_to_vendor, cost_for_shipping_from_buyer, status, post_id FROM order_table WHERE account_number = ? AND escrow_released IS NULL AND (status = ? OR (auto_finalization_timer < ? AND buyer_disputed IS NULL))", (account[0], "RELEASING FUNDS",  datetime.utcnow(), )) ;
		orders = cur.fetchall() ;


		# Get total amount of orders in payment.
		cur = connection.cursor() ;
		cur.execute("SELECT id FROM order_table WHERE account_number = ? and escrow_released IS NULL", (account[0], )) ;
		all_correlated_orders_not_released = cur.fetchall() ;



		list_of_transactions = [ ] ;
		total_price_of_everything = 0.0 ;
		total_price_profit = 0.0 ;
		date_current = datetime.utcnow() ;

		for order in orders:
			# Keep track of total amount to subtract fees from it.
			# Buying amount * Price
			constant_total_amount = total_amount = float(fernet.decrypt(order[1].encode()).decode()) * float(fernet.decrypt(order[2].encode()).decode()) ;
			total_price_of_everything = total_price_of_everything + constant_total_amount ;
			







			# If sending to ONLY vendor, take out 10% + shipping fee
			if not order[9]:
				total_price_profit += (total_amount * 0.10)
				total_amount -= (total_amount * 0.10) ;
				total_amount -= float(fernet.decrypt(order[11].encode()).decode()) ;



				# Get late fee first and pay that one off first
				cur = connection.cursor() ;
				cur.execute("SELECT id, total_amount_owed_5_percent FROM user_fee WHERE vendor_id = ? AND order_id = ? AND date_paid_off IS NULL", (order[5], order[0], )) ;
				late_fee = cur.fetchone() ;



				# Get all UserFee's of vendor from order in descending order of date reserved IF there are any fees associated with the vendor.
				cur = connection.cursor() ;
				cur.execute("SELECT id, user_id, vendor_id, total_amount_owed_5_percent, total_amount_owed_10_percent_plus_shipping, total_amount_paid_off FROM user_fee WHERE vendor_id = ? AND date_paid_off IS NULL AND NOT order_id = ?", (order[5], order[0], )) ;
				fees = cur.fetchall() ;



				# Late fees if vendor accepted order 24 or 48 hours later.
				# Will always be paid off first, and will always have enough to pay that initial fee off IF inquired.
				# Format of late_fee if string: "five 69.69696969696969"
				if late_fee:
					if fernet.decrypt(late_fee[1].encode()).decode()[:4] == "five":
						# Take off 6% from the order, and give 5% back to user. 1% swept later for me.
						total_amount = total_amount - float(fernet.decrypt(late_fee[1].encode()).decode()[6:]) ;
						list_of_transactions.append(( fernet.decrypt(order[6].encode()).decode(), (float(fernet.decrypt(late_fee[1].encode()).decode()[6:]) / 0.06) * 0.05 )) ;

					else:
						# Take off either 1% or 3% and give it ALL to the user.
						total_amount = total_amount - float(fernet.decrypt(late_fee[1].encode()).decode()) ;
						list_of_transactions.append(( fernet.decrypt(order[6].encode()).decode(), float(fernet.decrypt(late_fee[1].encode()).decode()) )) ;




				# Go through all the rest of the fees IF inquired by the vendor, and subtract them from profit, but only until 50%.
				for fee in fees:
					# Stop if 50% has been taken.
					if total_amount <= constant_total_amount / 2:
						break ;

					amount_to_pay = None ;


					# Get User's market wallet to pay to.
					cur = connection.cursor() ;
					cur.execute("SELECT account_number FROM user WHERE id = ?", (fee[1], )) ;
					user_market_wallet = cur.fetchone() ;



					# For 5-6% Fees
					if fee[3] and fernet.decrypt(fee[3].encode()).decode()[:4] == "five":
						# If vendor had paid before but didn't get all funds out, 
						if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0:
							# Amount to pay is the remaining amount
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()[6:]) - float(fernet.decrypt(fee[5].encode()).decode()) ;
						else:
							# Amount to pay is the total amount due
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()[6:]) ;


					# 1% - 3% fee
					elif fee[3]:
						# If vendor had paid before but didn't get all funds out, 
						if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0:
							# Amount to pay is the remaining amount
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()) - float(fernet.decrypt(fee[5].encode()).decode()) ;
						else:
							# Amount to pay is the total amount due
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()) ;


					# All else
					elif fee[4]:
						# If vendor had paid before but didn't get all funds out, 
						if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0:
							# Amount to pay is the remaining amount
							amount_to_pay = float(fernet.decrypt(fee[4].encode()).decode()) - float(fernet.decrypt(fee[5].encode()).decode()) ;
						else:
							# Amount to pay is the total amount due
							amount_to_pay = float(fernet.decrypt(fee[4].encode()).decode()) ;




					# Calculate amount to take out and amount left over
					amount_to_take_out = amount_to_pay ;
					amount_left_over = 0 ;

					# If taking out would result in vendor receiveing less than 50% on item
					if total_amount - amount_to_pay < constant_total_amount / 2:
						# Only take out amount that will make the vendor get 50%
						amount_to_take_out = total_amount - constant_total_amount / 2 ;
						amount_left_over = ((amount_to_take_out - amount_to_pay) * -1) ;
					


						# Update time or refund without releasing escrow
						update_order_excess_sql = ''' UPDATE user_fee
									   	   	             SET total_amount_paid_off = ?
									 	        	   WHERE id = ? '''

						cur = connection.cursor() ;
						cur.execute(update_order_excess_sql, (fernet.encrypt(str(amount_to_pay - amount_left_over).encode()).decode(), fee[0])) ;


					else:
						# Update time or refund without releasing escrow
							update_order_excess_sql = ''' UPDATE user_fee
										   	   	             SET total_amount_paid_off = ?,
										   	   	             	 date_paid_off = ?
										 	        	   WHERE id = ? '''

							cur = connection.cursor() ;
							cur.execute(update_order_excess_sql, (fernet.encrypt(str(amount_to_pay).encode()).decode(), date_current, fee[0])) ;






					# No 1% fee imposed since it was taken out before; or give ALL 1% or 3% to User.
					if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0 or fee[4] or (fee[3] and fernet.decrypt(fee[3].encode()).decode()[0] != "f"):
						total_amount = total_amount - amount_to_take_out ;
						list_of_transactions.append(( fernet.decrypt(user_market_wallet[0].encode()).decode(), amount_to_take_out )) ;


					# If there wasn't any amount of funds taken out previously and it is a 5-6%, take 6% out, 5% for user, 1% for profit.
					elif fee[3] and fernet.decrypt(fee[3].encode()).decode()[:4] == "five":
						# Take off 6% from the order, and give 5% back to user. 1% swept later for me.
						total_amount = total_amount - amount_to_take_out ;
						list_of_transactions.append(( fernet.decrypt(user_market_wallet[0].encode()).decode(), (amount_to_take_out / 0.06) * 0.05 )) ;





				# Send to vendor and not to user
				list_of_transactions.append(( fernet.decrypt(order[7].encode()).decode(), total_amount )) ;

				





















			
			# If sending to ONLY buyer, take out shipping fee
			elif not order[10]:

				# Total price profit increases by shipping cost to not raise sending error when about to send transaction.
				# User doesn't receive shipping cost anyways, as it is minused out from their end to pay for shipping costs for me.
				total_price_profit += float(fernet.decrypt(order[11].encode()).decode()) ;
				total_amount -= float(fernet.decrypt(order[11].encode()).decode()) ;


				# Pay late fee another time when vendor sells another item....


				# Get all UserFee's of Buyer from order in descending order of date reserved IF there are any fees associated with the vendor.
				cur = connection.cursor() ;
				cur.execute("SELECT id, user_id, vendor_id, total_amount_owed_5_percent, total_amount_owed_10_percent_plus_shipping, total_amount_paid_off FROM user_fee WHERE vendor_id = ? AND date_paid_off IS NULL AND NOT order_id = ?", (order[4], order[0], )) ;
				fees = cur.fetchall() ;




				# Go through all the rest of the fees IF inquired by the vendor, and subtract them from profit, but only until 50%.
				for fee in fees:
					# Stop if 50% has been taken.
					if total_amount <= constant_total_amount / 2:
						break ;

					amount_to_pay = None ;


					# Get User's market wallet to pay to.
					cur = connection.cursor() ;
					cur.execute("SELECT account_number FROM user WHERE id = ?", (fee[1], )) ;
					user_market_wallet = cur.fetchone() ;



					# For 5-6% Fees
					if fee[3] and fernet.decrypt(fee[3].encode()).decode()[:4] == "five":
						# If vendor had paid before but didn't get all funds out, 
						if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0:
							# Amount to pay is the remaining amount
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()[6:]) - float(fernet.decrypt(fee[5].encode()).decode()) ;
						else:
							# Amount to pay is the total amount due
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()[6:]) ;


					# 1% - 3% fee
					elif fee[3]:
						# If vendor had paid before but didn't get all funds out, 
						if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0:
							# Amount to pay is the remaining amount
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()) - float(fernet.decrypt(fee[5].encode()).decode()) ;
						else:
							# Amount to pay is the total amount due
							amount_to_pay = float(fernet.decrypt(fee[3].encode()).decode()) ;


					# All else
					elif fee[4]:
						# If vendor had paid before but didn't get all funds out, 
						if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0:
							# Amount to pay is the remaining amount
							amount_to_pay = float(fernet.decrypt(fee[4].encode()).decode()) - float(fernet.decrypt(fee[5].encode()).decode()) ;
						else:
							# Amount to pay is the total amount due
							amount_to_pay = float(fernet.decrypt(fee[4].encode()).decode()) ;




					# Calculate amount to take out and amount left over
					amount_to_take_out = amount_to_pay ;
					amount_left_over = 0 ;

					# If taking out would result in Buyer receiveing less than 50% on item
					if total_amount - amount_to_pay < constant_total_amount / 2:
						# Only take out amount that will make the buyer get 50%
						amount_to_take_out = total_amount - constant_total_amount / 2 ;
						amount_left_over = ((amount_to_take_out - amount_to_pay) * -1) ;
					


						# Update time or refund without releasing escrow
						update_order_excess_sql = ''' UPDATE user_fee
									   	   	             SET total_amount_paid_off = ?
									 	        	   WHERE id = ? '''

						cur = connection.cursor() ;
						cur.execute(update_order_excess_sql, (fernet.encrypt(str(amount_to_pay - amount_left_over).encode()).decode(), fee[0])) ;


					else:
						# Update time or refund without releasing escrow
							update_order_excess_sql = ''' UPDATE user_fee
										   	   	             SET total_amount_paid_off = ?,
										   	   	             	 date_paid_off = ?
										 	        	   WHERE id = ? '''

							cur = connection.cursor() ;
							cur.execute(update_order_excess_sql, (fernet.encrypt(str(amount_to_pay).encode()).decode(), date_current, fee[0])) ;






					# No 1% fee imposed since it was taken out before; or give ALL 1% or 3% to User.
					if float(fernet.decrypt(fee[5].encode()).decode()) != 0.0 or fee[4] or (fee[3] and fernet.decrypt(fee[3].encode()).decode()[0] != "f"):
						total_amount = total_amount - amount_to_take_out ;
						list_of_transactions.append(( fernet.decrypt(user_market_wallet[0].encode()).decode(), amount_to_take_out )) ;


					# If there wasn't any amount of funds taken out previously and it is a 5-6%, take 6% out, 5% for user, 1% for profit.
					elif fee[3] and fernet.decrypt(fee[3].encode()).decode()[:4] == "five":
						# Take off 6% from the order, and give 5% back to user. 1% swept later for me.
						total_amount = total_amount - amount_to_take_out ;
						list_of_transactions.append(( fernet.decrypt(user_market_wallet[0].encode()).decode(), (amount_to_take_out / 0.06) * 0.05 )) ;




				# Send to user and not to vendor
				list_of_transactions.append(( fernet.decrypt(order[6].encode()).decode(), constant_total_amount )) ;
























			# Split between buyer and vendor
			else:


				# Take out 10% Fee and Shipping Cost
				total_price_profit += (total_amount * 0.10)
				total_amount -= (total_amount * 0.10) ;
				total_amount -= float(fernet.decrypt(order[11].encode()).decode()) ;


				# Then distribute percentage of that between the buyer and the vendor.
				# [9] == Percentage to buyer
				# [10] == Percentage to vendor
				# [6] is user address
				# [7] is vendor address


				# Buyer percentage cut
				total_amount_buyer = total_amount * (float(fernet.decrypt(order[9].encode()).decode()) / 100.00) ;

				# Vendor percentage cut
				total_amount_vendor = total_amount * (float(fernet.decrypt(order[10].encode()).decode()) / 100.00) ;



				# Send to user.
				list_of_transactions.append(( fernet.decrypt(order[6].encode()).decode(), total_amount_buyer )) ;

				# Send to vendor.
				list_of_transactions.append(( fernet.decrypt(order[7].encode()).decode(), total_amount_vendor )) ;

























		# Check to see if there is enough in unlocked balance. Should never happen, but check here so that server doesn't crash just in case.
		# Change to 2 --> 3 later
		network_fee = float(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee) ;
		if wallet.accounts[int(fernet.decrypt(account[0].encode()).decode())].balance(unlocked=True) <= total_price_of_everything + network_fee - total_price_profit:
			print("Not unlocked: " + str(wallet.accounts[int(fernet.decrypt(account[0].encode()).decode())].balance(unlocked=True))) ;
			return False ;



		print("Amount of transactions to send: " + str(len(list_of_transactions))) ;

		# Transfer funds now officialy.
		try:
			transaction = wallet.accounts[int(fernet.decrypt(account[0].encode()).decode())].transfer_multiple(list_of_transactions, priority=1) ;
			print("Transaction sent") ;

		except:
			print("Cannot finish transaction, daemon not fully syncronized, please try again later..") ;
			return False ;


		# All orders' funds (have been)/(are going to be) released, and we will have to sweep_all later to claim the profit.
		if len(orders) == len(all_correlated_orders_not_released):

			sweep_all_sql = ''' INSERT INTO sweep_all(account_number)
						  			  VALUES(?) '''
			cur = connection.cursor() ;
			cur.execute(sweep_all_sql, (account[0], )) ;








		# Prepare message template
		message_user_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
															message_to, deleted_from_sender, deleted_from_reciever, 
															date_created, order_id)
							   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''


		message_vendor_sql = ''' INSERT INTO message(title, description, status, message_type, message_from, 
															message_to, deleted_from_sender, deleted_from_reciever, 
															date_created, order_id)
							   	 VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
		message_admin = 1 ;
		message_title = message_description = None ;


		# Go through all orders and message user and vendor
		for order in orders:
			date_current = datetime.utcnow() ;
			cur = connection.cursor() ;

			
			# Released early or dispute settled
			if order[14] == "RELEASING FUNDS":
				# Update time or refund without releasing escrow
				update_order_sql = ''' UPDATE order_table
						   	   	      SET status = ?,
						   	   	      	  escrow_released =?,
						   	   	          recent_update = ?
						 	        WHERE id = ? '''
				cur.execute(update_order_sql, ("RELEASED FUNDS", date_current, date_current, order[0])) ;
				
			# If auto-finalized
			else:
				# Update time or refund without releasing escrow
				update_order_sql = ''' UPDATE order_table
						   	   	      SET status = ?,
						   	   	      	  escrow_released =?,
						   	   	          recent_update = ?,
						   	   	          percentage_to_vendor = ?
						 	        WHERE id = ? '''
				cur.execute(update_order_sql, ("AUTO-FINALIZED", date_current, date_current, order[0], fernet.encrypt("100".encode()).decode())) ;



			# Get post id and title
			cur = connection.cursor() ;
			cur.execute("SELECT title, id, pending, sales, supply FROM post WHERE id = ?", (order[15], )) ;
			post = cur.fetchone() ;



			update_post_sql = ''' UPDATE post
						   	   	     SET pending = ?,
						   	   	     	 sales = ?, 
						   	   	     	 supply = ?
						 	       WHERE id = ? '''


			cur.execute(update_post_sql, (int(post[2]) - int(fernet.decrypt(order[1].encode()).decode()), int(post[3]) + int(fernet.decrypt(order[1].encode()).decode()), int(post[4]) - int(fernet.decrypt(order[1].encode()).decode()), order[15], )) ;




			# Get post id and title
			cur = connection.cursor() ;
			cur.execute("SELECT id, sales, currently_selling FROM user WHERE id = ?", (order[5], )) ;
			vendor = cur.fetchone() ;

			cur = connection.cursor() ;
			cur.execute("SELECT id, buys, currently_buying FROM user WHERE id = ?", (order[4], )) ;
			buyer = cur.fetchone() ;

			update_buys_sql = ''' UPDATE user
						   	   	     SET buys = ?,
						   	   	         currently_buying = ?
						 	       WHERE id = ? '''

			update_sale_sql = ''' UPDATE user
						   	   	     SET sales = ?,
						   	   	         currently_selling = ?
						 	       WHERE id = ? '''



			cur.execute(update_sale_sql, (int(vendor[1]) + int(fernet.decrypt(order[1].encode()).decode()), int(vendor[2]) - int(fernet.decrypt(order[1].encode()).decode()), order[5], )) ; 
			cur.execute(update_buys_sql, (int(buyer[1]) + int(fernet.decrypt(order[1].encode()).decode()), int(buyer[2]) - int(fernet.decrypt(order[1].encode()).decode()), order[4], )) ;

			if order[14] != "RELEASING FUNDS":
				message_title = "Auto-Released funds to vendor for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were auto-released." +
									   "\n\nPlease write a review for the order if you get a chance to.") ;

			elif order[9] == None:
				message_title = "Released funds to vendor for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were released." +
									   "\n\nPlease write a review for the order if you get a chance to.") ;

			elif order[10] == None:
				message_title = "Released funds for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were released." +
									  "\nRefund address: " + (str(fernet.decrypt(order[6].encode()).decode())) + 
									  "\nTransaction ID: " + str(transaction[0]) +
									  "\n\nIf vendor accepted order late, check fees in Wallet section and compare with Transaction ID above." +
									  "\nAlso, we might have taken up to 50% of profit if you had any prior associated fee, so please check all other fees associated in there as well." +
									  "\n\nPlease write a review for the order if you get a chance to.") ;

			else:
				message_title = "Released funds for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were released." +
									  "\nRefund address: " + (str(fernet.decrypt(order[6].encode()).decode())) + 
									  "\nTransaction ID: " + str(transaction[0]) +
									  "\nPercentage to you: " + (str(fernet.decrypt(order[9].encode()).decode())) +
									  "\n\nNote that no fees other than 10% of item and shipping costs get taken out in a settlement, as you already have received less Monero than what was intended." +
									  "\nHowever, next receivement of Monero from an order that is NOT a settlement will be subjected to fee incharges, if you have any." +
									  "\n\nPlease write a review for the order if you get a chance to.") ;


			# Encrypt message
			message_title = fernet.encrypt(message_title.encode()).decode() ;
			message_description = fernet.encrypt(message_description.encode()).decode() ;


			# [4] is user, [5] is vendor
			cur = connection.cursor() ;
			cur.execute(message_user_sql, (message_title, message_description, "UNOPENED", 
										   "RELEASED FUNDS", message_admin, order[4], False, False, datetime.utcnow(), order[0])) ;





			if order[14] != "RELEASING FUNDS":
				message_title = "Auto-Released funds to you for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were released." +
									   "\nRefund address: " + (str(fernet.decrypt(order[7].encode()).decode())) + 
									   "\nTransaction ID: " + str(transaction[0]) +
									   "\n\nIf you accepted order late, check fees in Wallet section and compare with Transaction ID above." +
									   "\nAlso check all other fees associated in there as well. If amount received was lower, we took out fees that were penalized against you from other orders." +
									   "\n\nPlease write a review about the buyer if you get a chance to.") ;
			if order[10] == None:
				message_title = "Released funds to buyer for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were released." +
									   "\nFees have been added to your account to pay to user as well on top." +
									   "\n\nIf you want the item back, please message us. You will have to pay an additional 10%% fee and shipping costs." +
									   "\nYou will have 7 days to accept offer." + 
									   "\nWe also may or may not accept returning the item back depending on the severity of the scam.") ;

			elif order[9] == None:
				message_title = "Released funds for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were released." +
									  "\nRefund address: " + (str(fernet.decrypt(order[7].encode()).decode())) + 
									  "\nTransaction ID: " + str(transaction[0]) +
									  "\n\nIf you accepted order late, check fees in Wallet section and compare with Transaction ID above." +
									  "\nAlso check all other fees associated in there as well. If amount received was lower, we took out fees that were penalized against you from other orders." +
									  "\n\nPlease write a review about the buyer if you get a chance to.") ;


			else:
				message_title = "Released funds for order #" + str(order[0]) ;
				message_description = ("Order #" + str(order[0]) + " '" + post[0] + "'s" + " funds were released." +
									  "\nRefund address: " + (str(fernet.decrypt(order[6].encode()).decode())) + 
									  "\nTransaction ID: " + str(transaction[0]) +
									  "\nPercentage to you: " + (str(fernet.decrypt(order[10].encode()).decode())) +
									  "\n\nNote that no fees other than 10% of item and shipping costs get taken out in a settlement, as you already have received less Monero than what was intended." +
									  "\nHowever, next receivement of Monero from an order that is NOT a settlement will be subjected to fee incharges, if you have any." +
									  "\n\nPlease write a review for the order if you get a chance to.") ;



			# Encrypt message
			message_title = fernet.encrypt(message_title.encode()).decode() ;
			message_description = fernet.encrypt(message_description.encode()).decode() ;



			cur = connection.cursor() ;
			cur.execute(message_vendor_sql, (message_title, message_description, "UNOPENED", 
										   "RELEASED FUNDS", message_admin, order[5], False, False, datetime.utcnow(), order[0])) ;





		connection.commit() ;


















def sweep_all(connection, wallet, daemon):
	# Data needed
	key = config.get("FERNET_KEY") ;
	fernet=Fernet(key.encode()) ;



	# Select all orders where vendor did not accept the order
	cur = connection.cursor() ;
	cur.execute("SELECT id, account_number FROM sweep_all") ;
	sweeps = cur.fetchall() ;


	print("Length to sweep all for profit: " + str(len(sweeps))) ;


	for sweep in sweeps:
		if wallet.accounts[int(fernet.decrypt(sweep[1].encode()).decode())].balance(unlocked=True) != wallet.accounts[int(fernet.decrypt(sweep[1].encode()).decode())].balance(unlocked=False):
			continue ;

		if wallet.accounts[int(fernet.decrypt(sweep[1].encode()).decode())].balance(unlocked=True) == 0:
			continue ;


		cur = connection.cursor() ;
		cur.execute("SELECT excess_received, excess_received_refunded FROM order_table WHERE account_number = ?", (sweep[1], )) ;
		order = cur.fetchone() ;

		if order[0] and not order[1]:
			continue ;




		

		try:
			transaction = wallet.accounts[int(fernet.decrypt(sweep[1].encode()).decode())].sweep_all(wallet.accounts[0].address(), priority=1) ;

			delete_sweep_sql = "DELETE FROM sweep_all WHERE id = ?" ;
			cur = connection.cursor() ;
			cur.execute(delete_sweep_sql, (sweep[0], )) ;
			print("Swept all! (:") ;

			connection.commit() ;
		except:
			print("Daemon not fully syncronized, try again later (Sweepall)...") ;
			return False ;

		
		



































def update_currencies(connection):
	# Source: https://www.youtube.com/watch?v=iIGNhBcj4zs
	# Source: https://coinmarketcap.com/api/documentation/v1/#operation/getV2CryptocurrencyQuotesHistorical

	try:
		# Janoher@tuta.io
		apikey_tuta = "986674f3-e338-4b75-8239-437f5eb90d40" ;

		# janoher@protonmail.com
		apikey = "48871def-b149-4933-b528-49f4ac8eeb0b" ;
		headers = { "X-CMC_PRO_API_KEY": apikey, "Accepts" : "application/json"} ;
		url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest" ;



		print("Starting to process currencies. Time: " + str(time.ctime())) ;

		# Get USA & Bitcoin & Ethrium price
		params = { "start" : 1, "limit" : 4000, "convert": "USD"} ;
		json = requests.get(url, params=params, headers=headers).json() ;


		# Get list data
		coins = json["data"] ;
		monero_index = 0 ;
		bitcoin = 0.0 ;
		ethereum = 0.0 ;
		litecoin = 0.0 ;
		dogecoin = 0.0 ;
		bitcoin_cash = 0.0 ;
		usd = 0.0 ;
		tether_gold = 0.0 ;

		index = 0 ;
		count = 0 ;
		for coin in coins:
			# Record BTC <-> USD
			if coin["symbol"] == "BTC":
				bitcoin = coin["quote"]["USD"]["price"] ;
				count += 1 ;

			# Record ETH <-> USD
			if coin["symbol"] == "ETH":
				ethereum = coin["quote"]["USD"]["price"] ;
				count += 1 ;

			if coin["symbol"] == "LTC":
				litecoin = coin["quote"]["USD"]["price"] ;
				count += 1 ;

			if coin["symbol"] == "DOGE":
				dogecoin = coin["quote"]["USD"]["price"] ;
				count += 1 ;

			if coin["symbol"] == "BCH":
				bitcoin_cash = coin["quote"]["USD"]["price"] ;
				count += 1 ;


			#if coin["symbol"] == "XMR":
				#monero_index = index ;
			#	count += 1 ;


			if coin["symbol"] == "XAUT":
				tether_gold = coin["quote"]["USD"]["price"] ;
				count += 1 ;


			if count == 7:
				break ;


			#index += 1 ;





		for coin in coins:
			if coin["symbol"] == "XMR":
				usd = coin["quote"]["USD"]["price"] ;

				# Get cryptocurrecy prices against Monero
				bitcoin = coin["quote"]["USD"]["price"] / bitcoin ;
				ethereum = coin["quote"]["USD"]["price"] / ethereum ;
				litecoin = coin["quote"]["USD"]["price"] / litecoin ;
				dogecoin = coin["quote"]["USD"]["price"] / dogecoin ;
				bitcoin_cash = coin["quote"]["USD"]["price"] / bitcoin_cash ;
				tether_gold = coin["quote"]["USD"]["price"] / tether_gold ;


			#monero_index += 1 ;

		# Save entries into database
		with connection:
			update_currency_database(connection, (usd, "USDT")) ;
			update_currency_database(connection, (bitcoin, "BTC")) ;
			update_currency_database(connection, (bitcoin_cash, "BCH")) ;
			update_currency_database(connection, (litecoin, "LTC")) ;
			update_currency_database(connection, (dogecoin, "DOGE")) ;
			update_currency_database(connection, (ethereum, "ETH")) ;
			update_currency_database(connection, (tether_gold, "XAUT")) ;


	except:
		print("Couldn't process currencies, try again later...") ;
		return False ;



	'''
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
		update_currency_database(connection, (usd, "USD")) ;
		update_currency_database(connection, (eur, "EUR")) ;
		update_currency_database(connection, (gbp, "GBP")) ;
		update_currency_database(connection, (cad, "CAD")) ;
		update_currency_database(connection, (aud, "AUD")) ;
		update_currency_database(connection, (chf, "CHF")) ;
		update_currency_database(connection, (cny, "CNY")) ;
		update_currency_database(connection, (jpy, "JPY")) ;
		update_currency_database(connection, (krw, "KRW")) ;
		update_currency_database(connection, (inr, "INR")) ;
		update_currency_database(connection, (rub, "RUB")) ;
		update_currency_database(connection, (bitcoin, "BTC")) ;
		update_currency_database(connection, (ethrium, "ETH")) ;
	'''
	

	# Print message
	print("\n\nFinished processing currencies. Time: " + str(time.ctime())) ;




# Update the currency price within the database
def update_currency_database(connection, task):
	sql = ''' UPDATE currency
			  SET price = ?
			  WHERE country = ?'''


	cur = connection.cursor() ;
	cur.execute(sql, task) ;
	connection.commit() ;











def pending_orders_15_minutes(connection):
	cur = connection.cursor() ;
	cur.execute("SELECT id, list_of_list_of_items FROM pending_order_screen WHERE date_reserved < ?", (datetime.utcnow() + timedelta(minutes=-18), )) ;
	pending_details = cur.fetchall() ;

	for pend in pending_details:
		cur = connection.cursor() ;
		cur.execute("SELECT id, post_id, buying_amount, gallery_1, gallery_2, gallery_3, gallery_4, gallery_5, gallery_6, gallery_7, gallery_8, gallery_9 FROM order_post_details WHERE pending_order_screen_id = ?", (pend[0], )) ;
		pend_galleries_all = cur.fetchall() ;




		# Commence deletion of pictures, and then delete from database
		for pend_galleries in pend_galleries_all:
			key = config.get("FERNET_KEY") ;
			fernet=Fernet(key.encode()) ;

			# Unpend each item first
			cur.execute("SELECT pending FROM post WHERE id = ?", (int(pend_galleries[1]), )) ;
			pending_post = cur.fetchone() ;

			update_pending_sql = ''' UPDATE post
						   	   	     SET pending = ?
						 	       WHERE id = ? '''

			cur.execute(update_pending_sql, (pending_post[0] - int(fernet.decrypt(pend_galleries[2].encode()).decode()), int(pend_galleries[1]), )) ;





			for index in range(3, len(pend_galleries)):

				if pend_galleries[index] == None:
					break ;

				previous_picture = os.path.join("../moneromarket/", "static/img/posts/originals", pend_galleries[index]) ;
				if os.path.exists(previous_picture):
					os.remove(previous_picture) ;
			
			cur = connection.cursor() ;
			cur.execute("DELETE FROM order_post_details WHERE id = ?", (pend[0], )) ;




	cur = connection.cursor() ;
	for pend in pending_details:
		cur.execute("DELETE FROM pending_order_screen WHERE id = ?", (pend[0], )) ;

	connection.commit() ;









def buyer_return_48_hours(connection):
	cur = connection.cursor() ;
	cur.execute("SELECT id FROM pending_order_screen WHERE date_reserved < ?", (datetime.utcnow() + timedelta(minutes=-18), )) ;
	pending_details = cur.fetchall() ;









def buyer_return_expired(connection):
	cur = connection.cursor() ;
	cur.execute("SELECT id, post_id, status, percentage_to_vendor, user_id, vendor_id FROM order_table WHERE status = ? AND request_buyer_return < ? AND recent_update = request_buyer_return", ("DISPUTING", datetime.utcnow() + timedelta(hours=48, minutes=-7), )) ;
	orders = cur.fetchall() ;

	key = config.get("FERNET_KEY") ;
	fernet=Fernet(key.encode()) ;


	print("Length of expired buyer returns: " + str(len(orders))) ;

	for order in orders:


		# Update the dispute won for post
		cur.execute("SELECT disputes_won FROM post WHERE id = ?", (order[1], )) ;
		post = cur.fetchone() ;

		update_post_sql = ''' UPDATE post
						   	  SET disputes_won = ?
						 	  WHERE id = ? '''

		cur.execute(update_post_sql, (int(post[0]) + 1, order[1])) ;
			



		cur.execute("SELECT disputes_won FROM user WHERE id = ?", (order[5], )) ;
		vendor = cur.fetchone() ;
		cur.execute("SELECT disputes_lost FROM user WHERE id = ?", (order[4], )) ;
		buyer = cur.fetchone() ;




		update_buyer_sql = ''' UPDATE user
						   	   SET disputes_lost = ?
						 	   WHERE id = ? '''

		cur.execute(update_buyer_sql, (int(buyer[0]) + 1, order[4])) ;

		update_vendor_sql = ''' UPDATE user
						   	    SET disputes_won = ?
						 	    WHERE id = ? '''

		cur.execute(update_vendor_sql, (int(vendor[0]) + 1, order[5])) ;



		update_order_sql = ''' UPDATE order_table
						   	   SET status = ?,
						   	   	   percentage_to_vendor = ?,
						   	   	   recent_update = ?
						 	   WHERE id = ? '''

		cur.execute(update_order_sql, ("RELEASING FUNDS", fernet.encrypt("100".encode()).decode(), datetime.utcnow(), order[0])) ;



		print("Started changes") ;

	print("commited changes") ;
	connection.commit() ;


































# int main()

# Initialize connection to the database...
connection = create_connection("../moneromarket/database/site.db") ;

# Print out whether database connected or not
if connection:
	print("Sucessfully connected to the database! (:") ;

else:
	print("Failed to connect to the database... ):") ;





# Instantiate wallet and route it through TOR
# Do it here to not have to constantly run a new instance of a wallet everytime, we will pass it by reference through the functions
# This makes the program not run slow, only in the intial bootup, IF the wallet size is already large to begin with
# i.e, most likely will not run slow in the beginning at all.
print("\n\nStarting to instantiate wallet. Time: " + str(time.ctime())) ;
daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050") ;
wallet = Wallet(port=28088) ;
print("\n\nFinished instantiating wallet. Time: " + str(time.ctime())) ;




while True:
	# Print message
	print("\n\nStarting to process orders. Time: " + str(time.ctime())) ;

	# wallet.refresh() ;
	update_currencies(connection) ;
	update_confirmations(connection, wallet, daemon) ;
	check_payment_price(connection, wallet, daemon) ;
	check_if_confirmations_are_10(connection) ;
	no_confirmations(connection) ;
	confirmations_less_than_10_in_6_hours(connection, wallet, daemon) ;
	waiting_for_vendor_72_hours(connection) ;
	releasing_funds(connection, wallet, daemon) ;
	sweep_all(connection, wallet, daemon) ;
	buyer_return_expired(connection) ;



	refund_in_24_hours(connection, wallet, daemon) ;

	pending_orders_15_minutes(connection) ;


	#update_currencies(connection) ;

	# Print message
	print("\n\nFinished processing orders. Time: " + str(time.ctime())) ;
	print("Will refresh in 10 minute.\n\n") ;

	time.sleep(600) ;



















# Errors:
'''
Traceback (most recent call last):
  File "orders.py", line 1085, in <module>
    update_network_transaction_fees(connection, wallet, daemon) ;
  File "orders.py", line 955, in update_network_transaction_fees
    slow_priority = wallet.accounts[0].transfer(wallet.accounts[1].address(), 0.000000000001, priority=1, relay=False) ;
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/monero/account.py", line 92, in transfer
    return self._backend.transfer(
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/monero/backends/jsonrpc/wallet.py", line 247, in transfer
    _transfers = self.raw_request('transfer_split', data)
  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/monero/backends/jsonrpc/wallet.py", line 314, in raw_request
    raise _err2exc[err['code']](err['message'])
monero.exceptions.NotEnoughUnlockedMoney: not enough unlocked money









'''



















