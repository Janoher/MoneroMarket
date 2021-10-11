from flask import Blueprint, render_template, flash, redirect, url_for, request, abort  
from flask_login import login_user, current_user, logout_user, login_required  

from moneromarket.users.forms import RegistrationForm, LoginForm  
from moneromarket.users.forms import (ChangePasswordForm, AddEmailForm, UpdateEmailForm, 
									  DeleteEmailForm, OneTimePasswordForm, DeleteAccountForm, UpdateProfileForm)  

from moneromarket import db, bcrypt  
from moneromarket.database.models import User, Post, CartItem, FavoriteUser, FavoriteItem, Message, SubCategory, Order, Currency, OrderPostDetails, OrderPictures, AdminEditing, Review, Dispute  

from moneromarket.users.utils import save_picture, delete_profile_picture, delete_post  
from moneromarket.employees.utils import save_picture_of_item, save_picture_of_receipt  
from moneromarket.reviews.utils import delete_review_picture_path  
from moneromarket.main.forms import SearchForm  
from moneromarket.employees.forms import CreateOutgoingShipmentForm, SearchOrderForm, AdminEditingForm, CreateOutgoingDigitalShipmentForm, SplitFundsForm, ReleaseBuyerForm,ReleaseVendorForm, SearchTransactionIDForm, SearchPublicAddressForm, SearchPaymentIDForm, ChangeBuyerAddressForm, ChangeVendorAddressForm, ChangeBuyerShippingAddressForm, AddFeaturedPost  
from moneromarket.reviews.forms import EditReviewForm  
from moneromarket.wallets.utils import MergeIncomingAndOutgoing  
from moneromarket.wallets.forms import SendMoneroForm  

from datetime import datetime, timedelta  
import os  
import json  
import random  
import numpy  
from moneromarket.config import config  

# Encryption and decryption
from cryptography.fernet import Fernet  


from monero.wallet import Wallet  
from monero.daemon import Daemon  
from monero.address import address  
from monero.numbers import PaymentID  


# http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
from sqlalchemy import or_, and_  




employees = Blueprint("employees", __name__)  











# Logout user
@employees.route("/employee", methods=["GET", "POST"])
@login_required
def home():

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  


	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	search_order_form = SearchOrderForm()  
	if search_order_form.submit.data and search_order_form.validate_on_submit():
		# source: https://stackoverflow.com/questions/8075877/converting-string-to-int-using-try-except-in-python
		try:
			search_order_form.order_number.data = int(search_order_form.order_number.data)  
		except ValueError:
			flash("Order does not exist.", "alert-red")  
			return redirect(url_for('employees.home'))  



		if not Order.query.filter_by(id=int(search_order_form.order_number.data)).first():
			flash("Order does not exist.", "alert-red")  
			return redirect(url_for('employees.home'))  

		else:
			return redirect(url_for("orders.view_order", order_id=int(search_order_form.order_number.data)))  



	search_payment_form = SearchPaymentIDForm()  
	if search_payment_form.submit_payment_id.data and search_payment_form.validate_on_submit():
		# source: https://stackoverflow.com/questions/8075877/converting-string-to-int-using-try-except-in-python
		try:
			search_payment_form.payment_id.data = search_payment_form.payment_id.data  
		except ValueError:
			flash("Order does not exist.", "alert-red")  
			return redirect(url_for('employees.home'))  



		if not Order.query.filter_by(payment_id=search_payment_form.payment_id.data).first():
			flash("Payment does not exist.", "alert-red")  
			return redirect(url_for('employees.home'))  

		else:
			return redirect(url_for("employees.view_payment_id", payment_id=search_payment_form.payment_id.data))  



	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  






	# Transaction ID
	transaction_id_form = SearchTransactionIDForm()  
	if transaction_id_form.submit_transaction_id.data and transaction_id_form.validate_on_submit():
		# source: https://stackoverflow.com/questions/8075877/converting-string-to-int-using-try-except-in-python
		if len(transaction_id_form.transaction_id.data) != 64:
			flash("Transaction ID entered incorrectly.", "alert-red")  
			return redirect(url_for('employees.home'))  


		daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050")  
		wallet = Wallet(port=28088)  

		# Public address
		for i in range(len(wallet.accounts)):
			if not wallet.accounts[i].incoming():
				continue  

			# Check through all transactions just in case a user double sends by mistake....
			for j in range(len(wallet.accounts[i].incoming())):
				if wallet.accounts[i].incoming()[j].transaction.hash == transaction_id_form.transaction_id.data:

					# Get public address to get order details from SQL database
					local_address = wallet.accounts[i].address()  
					account_number = i  

					orders = Order.query.all()  
					for order in orders:
						if fernet.decrypt(order.public_address.encode()).decode() == local_address:
							# order = Order.query.filter((fernet.decrypt(Order.public_address.encode()).decode()) == local_address).first_or_404()  

							return redirect(url_for("employees.view_order", order_id=order.id, 
													transaction_id=fernet.encrypt(transaction_id_form.transaction_id.data.encode()).decode(), 
													account_number=fernet.encrypt(str(account_number).encode()).decode()))  


		flash("Transaction does not exist.", "alert-red")  
		return redirect(url_for('employees.home'))  







	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/home.html", datetime=datetime.utcnow(), title="Employee", search_form=search_form,
						   search_order_form=search_order_form, transaction_id_form=transaction_id_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes,
						   search_payment_form=search_payment_form)  




# Logout user
@employees.route("/employee/shipments/incoming/<filter_by>", methods=["GET", "POST"])
@login_required
def incoming_shipments(filter_by ="all"):

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  


	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  



	page = request.args.get("page", 1, type=int)  


	# Source: http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
	incoming_shipments = None  
	if filter_by == "all":
		incoming_shipments = Order.query.filter(or_(Order.status == "VENDOR SHIPPED", and_(Order.buyer_shipped != None, Order.status == "DISPUTING"))).order_by(Order.recent_update.asc()).paginate(page=page, per_page=10)  
	elif filter_by == "buyer":
		incoming_shipments = Order.query.filter(Order.buyer_shipped != None, Order.status == "DISPUTING").order_by(Order.buyer_shipped).order_by(Order.vendor_shipped.asc()).paginate(page=page, per_page=10)  
	elif filter_by == "vendor":
		incoming_shipments = Order.query.filter_by(status="VENDOR SHIPPED").order_by(Order.vendor_shipped).order_by(Order.vendor_shipped.asc()).paginate(page=page, per_page=10)  



	

	





	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/incoming_shipments.html", datetime=datetime.utcnow(), title="Employee - Incoming", incoming_shipments=incoming_shipments,
						   search_form=search_form, filter_by=filter_by, fernet=fernet, page=page, User=User)  




@employees.route("/employee/shipments/incoming/view/order<int:order_id>", methods=["GET", "POST"])
@login_required
def view_incoming_shipment(order_id):

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  


	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  


	order = Order.query.filter_by(id=order_id).first()  
	if order.shipped_from_office:
		flash("Order has already been shipped.", "alert-faded-yellow")  
		return redirect(url_for('employees.incoming_shipments', filter_by="all"))  


	# OrderAcceptanceForm just for testing out, but make own specific form because more data will be added.
	# Such as description of the item, photos of the item, picutre of receipt, and text entry for the receipt.
	form = CreateOutgoingShipmentForm()  
	form_digital = CreateOutgoingDigitalShipmentForm()  
	if form.validate_on_submit():
		
		# Save picture variables for end to save into database
		gallery_1 = ""   
		gallery_2 = ""   
		gallery_3 = ""  
		gallery_4 = ""   
		gallery_5 = ""   
		gallery_6 = ""   
		gallery_7 = ""   
		gallery_8 = ""   
		gallery_9 = ""  
		gallery_10 = ""  
		gallery_11 = ""  
		gallery_12 = ""  
		gallery_13 = ""  
		gallery_14 = ""  
		gallery_15 = ""  
		gallery_16 = ""  
		gallery_17 = ""  
		gallery_18 = ""  
		gallery_19 = ""  
		gallery_20 = ""  
		gallery_21 = ""  
		receipt_picture = ""  

		accepted_extensions = { "jpg", "png", "jpeg", "pneg" }  



		# Source: https://stackoverflow.com/questions/53021662/multiplefilefield-wtforms
		# If there were any pictures submitted
		if form.pictures.data:

			if len(form.pictures.data) < 6:
				flash("6 files minimum are required for blue button.", "alert-red")  
				return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  

			elif len(form.pictures.data) > 21:
				flash("21 files maximum are allowed for blue button.", "alert-red")  
				return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  

			# Go through each picture to make sure they are the right format
			for picture in form.pictures.data:
				# Format for form.picture.data has nonsense filler in the last three characters
				if str(picture).lower()[-7:-3] in accepted_extensions or str(picture).lower()[-6:-3] in accepted_extensions:
					print("Accepted")  

				else:
					flash("Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
					return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  



			# Now do receipt
			if form.receipt_picture.data:
				if str(form.receipt_picture.data).lower()[-7:-3] in accepted_extensions or str(form.receipt_picture.data).lower()[-6:-3] in accepted_extensions:
					receipt_picture = save_picture_of_receipt(form.receipt_picture.data)  


				elif form.receipt_picture.data:
					flash("Only .jpg, .png, .jpeg, and .pneg files are allowed, please try again.", "alert-red")  
					return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  

			else:
				flash("No receipt picture submitted or registered, please try again.", "alert-red")  
				return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  





			# Save each photo now in the database
			for index in range(len(form.pictures.data)):
				saved_picture = save_picture_of_item(form.pictures.data[index])  

				if index == 0:
					gallery_1 = saved_picture  

				elif index == 1:
					gallery_2 = saved_picture  

				elif index == 2:
					gallery_3 = saved_picture  

				elif index == 3:
					gallery_4 = saved_picture  

				elif index == 4:
					gallery_5 = saved_picture  

				elif index == 5:
					gallery_6 = saved_picture  

				elif index == 6:
					gallery_7 = saved_picture  

				elif index == 7:
					gallery_8 = saved_picture  

				elif index == 8:
					gallery_9 = saved_picture  
				
				elif index == 9:
					gallery_10 = saved_picture  

				elif index == 10:
					gallery_11 = saved_picture  

				elif index == 11:
					gallery_12 = saved_picture  

				elif index == 12:
					gallery_13 = saved_picture  

				elif index == 13:
					gallery_14 = saved_picture  

				elif index == 14:
					gallery_15 = saved_picture  

				elif index == 15:
					gallery_16 = saved_picture  

				elif index == 16:
					gallery_17 = saved_picture  

				elif index == 17:
					gallery_18 = saved_picture  

				elif index == 18:
					gallery_19 = saved_picture  

				elif index == 19:
					gallery_20 = saved_picture  

				elif index == 20:
					gallery_21 = saved_picture  






		# If no images were passed through the form
		else:
			flash("No pictures submitted or registered, please try again.", "alert-red")  
			return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  






		description = fernet.encrypt(form.description.data.encode()).decode()  

		date_arrival = form.expected_arrival_date.data  
		auto_finalization = date_arrival + timedelta(hours=168)	# 7 days
		order.auto_finalization_timer = auto_finalization + timedelta(minutes=-1, seconds=-1)  
		order.tracking_number = fernet.encrypt(form.tracking_number.data.encode()).decode()  
		order.shipped_from_office = order.recent_update = current_time = datetime.utcnow()  

		# New table attached to order containing order info.
		order_pictures = OrderPictures(notes_about_item=description, receipt_picture=receipt_picture, date_arrival=date_arrival,
									   gallery_1=gallery_1, gallery_2=gallery_2, gallery_3=gallery_3, gallery_4=gallery_4, gallery_5=gallery_5,
									   gallery_6=gallery_6, gallery_7=gallery_7, gallery_8=gallery_8, gallery_9=gallery_9, gallery_10=gallery_10,
									   gallery_11=gallery_11, gallery_12=gallery_12, gallery_13=gallery_13, gallery_14=gallery_14,
									   gallery_15=gallery_15, gallery_16=gallery_16, gallery_17=gallery_17, gallery_18=gallery_18,
									   gallery_19=gallery_19, gallery_20=gallery_20, gallery_21=gallery_21)  


		user_title = "Order #" + str(order.id) + " was successfully verified and shipped"  
		user_body = ("Order #" + str(order.id) + " '" + order.orders_post.title + "' " + 
					 "arrived to our office and was shipped on " + current_time.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nOrder should be arriving on or a little after " + date_arrival.strftime("%b %-d") + 
					 "\nAuto-finalization will occur on " + auto_finalization.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nIf order has not come a few days before auto-finalization, you can extend auto-finalization and wait for delays." +
					 "\nIf item received was not like what it was described, or order never arrived after extending auto-finalization, " + 
					 "you can file a dispute to us in the order page." + "\nElse if all goes well, you can release the funds early to '" + 
					 order.orders_post.vendor.username + "', or you can just wait and auto-finalization will take care of the rest.")


		vendor_title = "Order #" + str(order.id) + " was successfully verified and shipped to buyer"  
		vendor_body = ("Order #" + str(order.id) + " '" + order.orders_post.title + "' " + 
					 "arrived to our office from you and was shipped on " + current_time.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nAuto-finalization will occur on " + auto_finalization.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nIf order has not received order a few days before auto-finalization, " +
					 "they can extend auto-finalization and wait for delays." +
					 "\nIf item received was not like what it was described, or order never arrived after extending auto-finalization, " + 
					 "the user can file a dispute against you." + "\nWe will accept dispute responses from you, and will consider what to do." +
					 "\nElse if all goes well, '" + User.query.filter_by(id=order.user_id).first().username + "' can release the funds early to " +
					 "you, or auto-finalization will take care of the rest if they don't do an early release.")

		v_title_e = fernet.encrypt(vendor_title.encode()).decode()  
		v_body_e = fernet.encrypt(vendor_body.encode()).decode()  
		u_title_e = fernet.encrypt(user_title.encode()).decode()  
		u_body_e = fernet.encrypt(user_body.encode()).decode()  

		message_user = Message(title=u_title_e, description=u_body_e, message_type="TRANSACTION", message_from=1, message_to=order.user_id,
							   date_created=datetime.utcnow(), order_id=order.id)  
		message_vendor = Message(title=v_title_e, description=v_body_e, message_type="TRANSACTION", message_from=1, message_to=order.vendor_id,
							     date_created=datetime.utcnow(), order_id=order.id)  

		# Update order pictures
		order.shipped_from_office = order.recent_update = datetime.utcnow()  
		db.session.add(order_pictures)  
		order.order_pictures_id = order_pictures.id  
		order.status = "SHIPPED TO BUYER"  




		fixed_to_fiat = None  
		currency = request.form.get("currency").upper()  

		# Will always be true as of now, but in the future will allow for static Monero prices.
		# Commented out original and replaced with "if True:"
		# Just uncomment and delete "if True:" whenever ready to allow for static Monero prices, as everything is already all set up.

		# if request.form.get("fiat") == "Fiat":
		if False:
			fixed_to_fiat = True  
		else:
			fixed_to_fiat = False  

		# Least amount possible is 1 x 10^-8
		# Scratch that, that's what I wanted haha, but unfortanately the price can't be less than the transaction fees
		# Starting officialy at 0.0001 on 04-15/2021, and subject to change.
		# For Monero.....



		# Convert to fiat to adjust the price....
		if fixed_to_fiat == True:
			if currency == "XMR":
				form.shipping_cost.data = float(form.shipping_cost.data) * float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "USDT":
				form.shipping_cost.data = float(form.shipping_cost.data) * float(Currency.query.filter_by(country=currency).first().price)  

			'''
			# Never less than $1 USD
			if float(form.shipping_cost.data) < float(1.00):
				form.shipping_cost.data = float(1.00)  '''


		# Convert to Monero to keep it static.
		elif fixed_to_fiat == False:
			if currency == "USDT":
				form.shipping_cost.data = float(form.shipping_cost.data) / float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "XMR":
				form.shipping_cost.data = float(form.shipping_cost.data) * float(Currency.query.filter_by(country=currency).first().price) / float(Currency.query.filter_by(country="USDT").first().price)  

			'''
			# Never less than $1 USD
			if float(form.shipping_cost.data) < float(1) / float(Currency.query.filter_by(country="USDT").first().price):
				form.shipping_cost.data = float(1) / float(Currency.query.filter_by(country="USDT").first().price)  '''





		# Add messages to database
		db.session.add(message_user)  
		db.session.add(message_vendor)  


		order.order_pictures_id = order_pictures.id  
		order.cost_for_shipping_to_buyer = fernet.encrypt(str(form.shipping_cost.data).encode()).decode()
		db.session.commit()  

		flash("Successfully sent out order!", "alert-green")
		return redirect(url_for("employees.incoming_shipments", filter_by='all'))  






	elif form_digital.validate_on_submit():
		
		# Save picture variables for end to save into database
		gallery_1 = ""   
		gallery_2 = ""   
		gallery_3 = ""  
		gallery_4 = ""   
		gallery_5 = ""   
		gallery_6 = ""   
		gallery_7 = ""   
		gallery_8 = ""   
		gallery_9 = ""  
		gallery_10 = ""  
		gallery_11 = ""  
		gallery_12 = ""  
		gallery_13 = ""  
		gallery_14 = ""  
		gallery_15 = ""  
		gallery_16 = ""  
		gallery_17 = ""  
		gallery_18 = ""  
		gallery_19 = ""  
		gallery_20 = ""  
		gallery_21 = ""  
		receipt_picture = ""  

		accepted_extensions = { "jpg", "png", "jpeg", "pneg" }  



		# Source: https://stackoverflow.com/questions/53021662/multiplefilefield-wtforms
		# If there were any pictures submitted
		if form_digital.pictures.data:

			if len(form_digital.pictures.data) < 6:
				flash("6 files minimum are required for blue button.", "alert-red")  
				return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  

			elif len(form_digital.pictures.data) > 21:
				flash("21 files maximum are allowed for blue button.", "alert-red")  
				return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  

			# Go through each picture to make sure they are the right format
			for picture in form_digital.pictures.data:
				# Format for form_digital.picture.data has nonsense filler in the last three characters
				if str(picture).lower()[-7:-3] in accepted_extensions or str(picture).lower()[-6:-3] in accepted_extensions:
					print("Accepted")  

				else:
					flash("Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
					return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  






			# Save each photo now in the database
			for index in range(len(form_digital.pictures.data)):
				saved_picture = save_picture_of_item(form_digital.pictures.data[index])  

				if index == 0:
					gallery_1 = saved_picture  

				elif index == 1:
					gallery_2 = saved_picture  

				elif index == 2:
					gallery_3 = saved_picture  

				elif index == 3:
					gallery_4 = saved_picture  

				elif index == 4:
					gallery_5 = saved_picture  

				elif index == 5:
					gallery_6 = saved_picture  

				elif index == 6:
					gallery_7 = saved_picture  

				elif index == 7:
					gallery_8 = saved_picture  

				elif index == 8:
					gallery_9 = saved_picture  
				
				elif index == 9:
					gallery_10 = saved_picture  

				elif index == 10:
					gallery_11 = saved_picture  

				elif index == 11:
					gallery_12 = saved_picture  

				elif index == 12:
					gallery_13 = saved_picture  

				elif index == 13:
					gallery_14 = saved_picture  

				elif index == 14:
					gallery_15 = saved_picture  

				elif index == 15:
					gallery_16 = saved_picture  

				elif index == 16:
					gallery_17 = saved_picture  

				elif index == 17:
					gallery_18 = saved_picture  

				elif index == 18:
					gallery_19 = saved_picture  

				elif index == 19:
					gallery_20 = saved_picture  

				elif index == 20:
					gallery_21 = saved_picture  






		# If no images were passed through the form_digital
		else:
			flash("No pictures submitted or registered, please try again.", "alert-red")  
			return redirect(url_for('employees.view_incoming_shipment', order_id=order_id))  






		description = fernet.encrypt(form_digital.description.data.encode()).decode()  

		date_arrival = datetime.utcnow()  
		auto_finalization = (date_arrival + timedelta(hours=168)) + timedelta(minutes=-1, seconds=-1)  	# 7 days
		order.auto_finalization_timer = auto_finalization  
		order.shipped_from_office = order.recent_update = current_time = date_arrival  

		# New table attached to order containing order info.
		order_pictures = OrderPictures(notes_about_item=description, receipt_picture="None", date_arrival=date_arrival,
									   gallery_1=gallery_1, gallery_2=gallery_2, gallery_3=gallery_3, gallery_4=gallery_4, gallery_5=gallery_5,
									   gallery_6=gallery_6, gallery_7=gallery_7, gallery_8=gallery_8, gallery_9=gallery_9, gallery_10=gallery_10,
									   gallery_11=gallery_11, gallery_12=gallery_12, gallery_13=gallery_13, gallery_14=gallery_14,
									   gallery_15=gallery_15, gallery_16=gallery_16, gallery_17=gallery_17, gallery_18=gallery_18,
									   gallery_19=gallery_19, gallery_20=gallery_20, gallery_21=gallery_21)  


		user_title = "Order #" + str(order.id) + " was successfully verified and digitally sent"  
		user_body = ("Order #" + str(order.id) + " '" + order.orders_post.title + "' " + 
					 "arrived to our office and was shipped on " + current_time.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nAuto-finalization will occur on " + auto_finalization.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nIf item received was not like what it was described, or order never arrived after extending auto-finalization, " + 
					 "you can file a dispute to us in the order page." + "\nElse if all goes well, you can release the funds early to '" + 
					 order.orders_post.vendor.username + "', or you can just wait and auto-finalization will take care of the rest.")


		vendor_title = "Order #" + str(order.id) + " was successfully verified and digitally sent to buyer"  
		vendor_body = ("Order #" + str(order.id) + " '" + order.orders_post.title + "' " + 
					 "arrived to our office from you and was digitally on " + current_time.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nAuto-finalization will occur on " + auto_finalization.strftime("%b %-d, %H:%M:%S") + " UTC time." + 
					 "\nIf buyer has not received order a few days before auto-finalization, " +
					 "they can extend auto-finalization and wait for delays." +
					 "\nIf item received was not like what it was described, or order never arrived after extending auto-finalization, " + 
					 "the user can file a dispute against you." + "\nWe will accept dispute responses from you, and will consider what to do." +
					 "\nElse if all goes well, '" + User.query.filter_by(id=order.user_id).first().username + "' can release the funds early to " +
					 "you, or auto-finalization will take care of the rest if they don't do an early release.")

		v_title_e = fernet.encrypt(vendor_title.encode()).decode()  
		v_body_e = fernet.encrypt(vendor_body.encode()).decode()  
		u_title_e = fernet.encrypt(user_title.encode()).decode()  
		u_body_e = fernet.encrypt(user_body.encode()).decode()  

		message_user = Message(title=u_title_e, description=u_body_e, message_type="TRANSACTION", message_from=1, message_to=order.user_id,
							   date_created=datetime.utcnow(), order_id=order.id)  
		message_vendor = Message(title=v_title_e, description=v_body_e, message_type="TRANSACTION", message_from=1, message_to=order.vendor_id,
							     date_created=datetime.utcnow(), order_id=order.id)  

		# Update order pictures
		order.shipped_from_office = order.recent_update = datetime.utcnow()  
		db.session.add(order_pictures)  
		order.order_pictures_id = order_pictures.id  
		order.status = "SHIPPED TO BUYER"  

		order.description_digital = fernet.encrypt(form_digital.description_digital.data.encode()).decode()  



		





		# Add messages to database
		db.session.add(message_user)  
		db.session.add(message_vendor)  


		order.cost_for_shipping_to_buyer = fernet.encrypt("0".encode()).decode()  
		db.session.commit()  

		flash("Successfully digitally sent out order!", "alert-green")
		return redirect(url_for("employees.incoming_shipments", filter_by='all'))  


















	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  




	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("employee/view_incoming_shipment.html", datetime=datetime.utcnow(), title="Employee - View Incoming", fernet=fernet,
						   order=order, search_form=search_form, SubCategory=SubCategory, numpy=numpy, form=form, float=float,
						   usdt=usdt, btc=btc, bch=bch, doge=doge, ltc=ltc, eth=eth,
						   OrderPostDetails=OrderPostDetails, form_digital=form_digital, xaut=xaut, User=User,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  























# Logout user
@employees.route("/employee/shipments/outgoing/<filter_by>", methods=["GET", "POST"])
@login_required
def outgoing_shipments(filter_by ="all"):

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  


	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  



	page = request.args.get("page", 1, type=int)  


	# Source: http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
	outgoing_shipments = None  
	if filter_by == "all":
		outgoing_shipments = Order.query.filter(or_(Order.status == "SHIPPED TO BUYER", Order.status == "SHIPPED TO VENDOR")).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "buyer":
		outgoing_shipments = Order.query.filter_by(status="SHIPPED TO BUYER").order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "vendor":
		outgoing_shipments = Order.query.filter_by(status="SHIPPED TO VENDOR").order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	else:
		abort(403)  

	





	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/outgoing_shipments.html", datetime=datetime.utcnow(), title="Employee",
						   outgoing_shipments=outgoing_shipments,
						   search_form=search_form, filter_by=filter_by, fernet=fernet, page=page, User=User,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  





@employees.route("/employee/shipments/outgoing/view/order<int:order_id>", methods=["GET", "POST"])
@login_required
def view_outgoing_shipment(order_id):

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  


	order = Order.query.filter_by(id=order_id).first_or_404()  
	order_info = OrderPictures.query.filter_by(id=order.order_pictures_id).first_or_404()  



	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  




	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("employee/view_outgoing_shipment.html", datetime=datetime.utcnow(), title="Employee - View Outgoing", fernet=fernet,
						   order=order, search_form=search_form, SubCategory=SubCategory, numpy=numpy, order_info=order_info, float=float,
						   User=User,
						   usdt=usdt, btc=btc, bch=bch, eth=eth, doge=doge, ltc=ltc, xaut=xaut,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  
































@employees.route("/employee/original/<int:order_id>", methods=["GET", "POST"])
@login_required
def original_item(order_id):

	order = Order.query.filter_by(id=order_id).first_or_404()  

	# Only employees, admins, buyer, and seller can view the original item.
	if not current_user.is_employee:
		if not current_user.is_admin:
			if order.user_id != current_user.id:
				if order.vendor_id != current_user.id:
					abort(403)  


	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	previous_page = request.args.get("previous_page", "main.home", type=str)  
	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  


	original = OrderPostDetails.query.filter_by(post_id=order.post_id, payment_id=order.payment_id).first_or_404()  







	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  




	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("employee/original.html", datetime=datetime.utcnow(), title="Original item", search_form=search_form, original=original,
						   previous_page=previous_page, Post=Post, User=User, order=order, numpy=numpy, fernet=fernet, float=float,
						   usdt=usdt, btc=btc, bch=bch, ltc=ltc, eth=eth, doge=doge, xaut=xaut,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  











@employees.route("/employee/disputes/outgoing/<filter_by>", methods=["GET", "POST"])
@login_required
def disputes(filter_by ="buyer"):

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  



	page = request.args.get("page", 1, type=int)  


	# Source: http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
	disputes = None  
	'''
	if filter_by == "all":
		disputes = Order.query.filter(and_(Order.status == "DISPUTING", or_(Order.buyer_disputed != None, Order.vendor_disputed != None))).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	'''

	if filter_by == "buyer":
		disputes = Order.query.filter(Order.status == "DISPUTING", Order.buyer_disputed != None).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "vendor":
		disputes = Review.query.filter(Review.dispute_date != None, Review.dispute_resolved == None).order_by(Review.dispute_date.desc()).paginate(page=page, per_page=10)  
	else:
		abort(404)  










	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/order_disputes.html", datetime=datetime.utcnow(), title="Disputes", search_form=search_form,
						   filter_by=filter_by, disputes=disputes, User=User, page=page, fernet=fernet, OrderPostDetails=OrderPostDetails,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  












@employees.route("/employee/view/order/<int:order_id>", methods=["GET", "POST"])
@login_required
def view_order(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  

	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  


	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  










	transaction_id = request.args.get("transaction_id", "0", type=str)  
	account_number = request.args.get("account_number", "-1", type=str)  


	total_balance = None  
	unlocked_balance = None  
	transactions = None  
	wallet = None  
	network_fees = [ ]  
	if transaction_id != "0":
		daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050")  
		wallet = Wallet(port=28088)  


		total_balance = wallet.accounts[int(fernet.decrypt(account_number.encode()).decode())].balance(unlocked=False)  
		unlocked_balance = wallet.accounts[int(fernet.decrypt(account_number.encode()).decode())].balance(unlocked=True)  


		transactions = MergeIncomingAndOutgoing(wallet.accounts[int(fernet.decrypt(account_number.encode()).decode())].incoming(),
											    wallet.accounts[int(fernet.decrypt(account_number.encode()).decode())].outgoing())  


		network_fees.append(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee)  
		network_fees.append(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=2, relay=False)[0].fee)  
		network_fees.append(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=3, relay=False)[0].fee)  







	change_buyer_address_form = ChangeBuyerAddressForm()  
	if change_buyer_address_form.submit_buyer.data and change_buyer_address_form.validate_on_submit():
		if change_buyer_address_form.return_address.data == None or len(change_buyer_address_form.return_address.data) != 95:
			flash("Please insert a valid Monero address...", "alert-red")  

			return redirect(url_for('employees.view_order', order_id=order_id))  
		else:
			order.return_address = fernet.encrypt(change_buyer_address_form.return_address.data.encode()).decode()  
			flash("Buyer return wallet address changed...", "alert-green")  

			db.session.commit()  




	change_vendor_address_form = ChangeVendorAddressForm()  
	if change_vendor_address_form.submit_vendor.data and change_vendor_address_form.validate_on_submit():
		if change_vendor_address_form.return_address.data == None or len(change_vendor_address_form.return_address.data) != 95:
			flash("Please insert a valid Monero address...", "alert-red")  

			return redirect(url_for('employees.view_order', order_id=order_id))  
		else:
			order.vendor_address = fernet.encrypt(change_vendor_address_form.return_address.data.encode()).decode()  
			flash("Vendor return wallet address changed...", "alert-green")  

			db.session.commit()  




	change_buyer_shipping_address_form = ChangeBuyerShippingAddressForm()  
	if change_buyer_shipping_address_form.submit_shipping_buyer.data and change_buyer_shipping_address_form.validate_on_submit():
		order.name_and_address = fernet.encrypt(change_buyer_shipping_address_form.shipping_address.data.encode()).decode()  

		db.session.commit()  





	send_monero_form = SendMoneroForm()  
	if send_monero_form.validate_on_submit():


		fixed_to_fiat = None  
		currency = request.form.get("currency").upper()  

		# Will always be true as of now, but in the future will allow for static Monero prices.
		# Commented out original and replaced with "if True:"
		# Just uncomment and delete "if True:" whenever ready to allow for static Monero prices, as everything is already all set up.

		# if request.send_monero_form.get("fiat") == "Fiat":
		if False:
			fixed_to_fiat = True  
		else:
			fixed_to_fiat = False  

		# Least amount possible is 1 x 10^-8
		# Scratch that, that's what I wanted haha, but unfortanately the price can't be less than the transaction fees
		# Starting officialy at 0.0001 on 04-15/2021, and subject to change.
		# For Monero.....



		# Convert to fiat to adjust the price....
		if fixed_to_fiat == True:
			if currency == "XMR":
				send_monero_form.amount.data = float(send_monero_form.amount.data) * float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "USDT":
				send_monero_form.amount.data = float(send_monero_form.amount.data) * (float(Currency.query.filter_by(country="USDT").first().price) / float(Currency.query.filter_by(country=currency).first().price))  


			# Never less than $1 USD
			if float(send_monero_form.amount.data) < float(1.00):
				send_monero_form.amount.data = float(1.00)  


		# Convert to Monero to keep it static.
		elif fixed_to_fiat == False:
			if currency == "USDT":
				send_monero_form.amount.data = float(send_monero_form.amount.data) / float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "XMR":
				send_monero_form.amount.data = float(send_monero_form.amount.data) * float(Currency.query.filter_by(country=currency).first().price) / float(Currency.query.filter_by(country="USDT").first().price)  


			'''
			# Never less than $1 USD
			if float(send_monero_form.amount.data) < float(1) / float(Currency.query.filter_by(country="USDT").first().price):
				send_monero_form.amount.data = float(1) / float(Currency.query.filter_by(country="USDT").first().price)  
			'''






		# Get important and frequently used variables to not have to copy & paste throughout the function...
		fee_priority = request.form.get("fee-priority")  
		unlocked_balance = wallet.accounts[int(fernet.decrypt(account_number.encode()).decode())].balance(unlocked=True)  


		# Don't attempt to send any money if user tries to send more money than what they have unlocked.
		if float(send_monero_form.amount.data) > float(unlocked_balance):
			flash(f"{ send_monero_form.amount.data } XMR is more than your unlocked balance, please send a different amount, or wait until balance is fully unlocked.", "alert-red")  


		# Send ALL available money, without worrying about the transaction fee interfering, only if transaction is not zero of course
		elif float(send_monero_form.amount.data) == float(unlocked_balance) and float(unlocked_balance) != 0.0:
			if float(network_fees[int(fee_priority)]) >= float(unlocked_balance):
				flash(f"Fee is higher than unlocked balanced, please try with a different fee, or wait until balance is fully unlocked.", "alert-red")  
			else:
				try:
					sweep_all = wallet.accounts[int(fernet.decrypt(account_number.encode()).decode())].sweep_all(send_monero_form.address.data, int(fee_priority) + 1)  
					flash("Successfully sent ALL available UNLOCKED balance to address. Check below in Transaction History for info! Transaction ID: " + str(sweep_all[0][0]), "alert-blue")  
				except ValueError:
					flash("Address is not valid, please try sending to a different address.", "alert-red")  


		# If the price of the fee makes the amount higher than what is unlocked, give the user options on what to do.
		elif float(send_monero_form.amount.data) + float(network_fees[int(fee_priority)]) > float(unlocked_balance):
			flash("Amount + Network Fee is more than unlocked balance, please retry with a smaller fee size, or retry but send ALL available Monero in unlocked balance, or wait until balance is fully unlocked.", "alert-red")  


		# Prevent sending zero Monero, as this will cause an exception and crash the server.... ):
		elif float(send_monero_form.amount.data) == 0.0:
			flash("Error, cannot send 0 XMR, it is not allowed. Please send an actual amount.", "alert-red")  


		# Negative amounts of monero trying to send
		elif float(send_monero_form.amount.data) < 0.0:
			flash("Error, cannot send negative amounts of XMR, it is not allowed. Please send an actual amount.", "alert-red")  


		# Send normal transaction with fee specified if both combined is less than or equal to the unlocked balance (:
		elif float(send_monero_form.amount.data) + float(network_fees[int(fee_priority)]) <= float(unlocked_balance):
			try:
				transaction = wallet.accounts[int(fernet.decrypt(account_number.encode()).decode())].transfer(send_monero_form.address.data, Decimal(send_monero_form.amount.data), int(fee_priority) + 1)  
				flash(f"Successfully sent { send_monero_form.amount.data } XMR to address. Check below in Transaction History for info! Transaction ID: " + str(transaction[0]), "alert-blue")  
			except ValueError:
				flash("Address is not valid, please try sending to a different address.", "alert-red")  
			except monero.exceptions.NotEnoughMoney:
				flash("Not enough Monero to send, please try with a smaller priority network fee, or add more Monero.", "alert-red")  

		# Uknown errors
		else:
			flash("Unknown error occured... ):", "alert-red")  


		return redirect(url_for('employees.view_order', order_id=order_id, transaction_id=transaction_id, account_number=account_number))  
















	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  





	split_form = SplitFundsForm()  
	buyer_release_form = ReleaseBuyerForm()  
	vendor_release_form = ReleaseVendorForm()  

	if split_form.submit_split.data and split_form.validate_on_submit():
		if split_form.to_buyer.data > 100.00 or split_form.to_buyer.data < 0.00:
			flash("Cannot give more than 100% or less than 0%..", "alert-red")  
			return redirect(url_for('employees.view_order', order_id=order_id))  

		if split_form.to_vendor.data > 100.00 or split_form.to_vendor.data < 0.00:
			flash("Cannot give more than 100% or less than 0%..", "alert-red")  
			return redirect(url_for('employees.view_order', order_id=order_id))  


		if split_form.to_buyer.data + split_form.to_vendor.data != 100.00:
			flash("Buyer and vendor combined must be 100%", "alert-red")  
			return redirect(url_for('employees.view_order', order_id=order_id))  


		if len(split_form.description.data) > 500:
			flash("Maximum description of 500 characters allowed", "alert-red")  
			return redirect(url_for('employees.view_order', order_id=order_id))  



		# If all is correct, redirect to submit form
		return redirect(url_for('employees.release_disputed_funds_to_settled', order_id=order_id, to_buyer=str(split_form.to_buyer.data), 
								to_seller=str(split_form.to_vendor.data), description_dispute=split_form.description.data))  





	elif buyer_release_form.submit_buyer.data and buyer_release_form.validate_on_submit():

		if len(buyer_release_form.description.data) > 500:
			flash("Maximum description of 500 characters allowed", "alert-red")  
			return redirect(url_for('employees.view_order', order_id=order_id))  


		return redirect(url_for('employees.release_disputed_funds_to_buyer', order_id=order_id, description_dispute=buyer_release_form.description.data))  


	elif vendor_release_form.submit_vendor.data and vendor_release_form.validate_on_submit():

		if len(vendor_release_form.description.data) > 500:
			flash("Maximum description of 500 characters allowed", "alert-red")  
			return redirect(url_for('employees.view_order', order_id=order_id))  


		return redirect(url_for('employees.release_disputed_funds_to_vendor', order_id=order_id, description_dispute=vendor_release_form.description.data))  
		





	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():
		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/view_order.html", title="Checked-Out", datetime=datetime.utcnow(), order=order,
						   SubCategory=SubCategory, fernet=fernet, float=float, OrderPictures=OrderPictures,
						   numpy=numpy, search_form=search_form, timedelta=timedelta, OrderPostDetails=OrderPostDetails, User=User,
						   usdt=usdt, btc=btc, ltc=ltc, bch=bch, doge=doge, eth=eth, xaut=xaut, split_form=split_form,
						   buyer_release_form=buyer_release_form, vendor_release_form=vendor_release_form, transaction_id=transaction_id,
						   account_number=account_number, total_balance=total_balance, unlocked_balance=unlocked_balance, transactions=transactions,
						   wallet=wallet, send_monero_form=send_monero_form, network_fees=network_fees,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes,
						   change_buyer_address_form=change_buyer_address_form, change_vendor_address_form=change_vendor_address_form,
						   change_buyer_shipping_address_form=change_buyer_shipping_address_form)  










@employees.route("/employee/orders/view/payment-id/<string:payment_id>", methods=["GET", "POST"])
@login_required
def view_payment_id(payment_id):
	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  


	page = request.args.get("page", 1, type=int)  
	orders = Order.query.filter_by(payment_id=payment_id).paginate(page=page, per_page=10)  

	if orders.total == 0:
		abort(404)  
	#http://127.0.0.1:5000/order/payment-id/07b7cb238f84c8ca

	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  


	public_address = fernet.decrypt(orders.items[0].public_address.encode()).decode()  


	confirmations = orders.items[0].confirmations  
	if confirmations > 10:
		confirmations = 10  


	total_price = orders.items[0].total_amount_for_payment_id  

	
	refund_address = fernet.decrypt(orders.items[0].return_address.encode()).decode()  







	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  







	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("employee/view_payment.html", title="Checked-Out", datetime=datetime.utcnow(), orders=orders,
						   SubCategory=SubCategory, public_address=public_address, fernet=fernet, float=float,
						   payment_id=payment_id, refund_address=refund_address, confirmations=confirmations, total_price=total_price,
						   numpy=numpy, search_form=search_form, page=page, timedelta=timedelta, User=User,
						   usdt=usdt, btc=btc, bch=bch, ltc=ltc, doge=doge, eth=eth, xaut=xaut,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  










'''
@employees.route("/employee/release/funds/to/vendor", methods=["GET", "POST"])
@login_required
def release_funds_to_vendor():
	order_id = request.args.get("order_id", 0, type=int)  
	order = Order.query.filter_by(id=order_id).first_or_404()  

	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	if order.escrow_released:
		flash("Funds already have been released.", "alert-faded-yellow")  
		return redirect(url_for("employees.view_order", order_id=order.id))  
	elif order.status == "RELEASING FUNDS":
		flash("Funds already are being released.", "alert-faded-yellow")  
		return redirect(url_for("employees.view_order", order_id=order.id))  

		
	
	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  



	# Send to both user and profit later in orders.py sql automation....
	order.status = "RELEASING FUNDS"  
	order.percentage_to_vendor = fernet.encrypt("100".encode()).decode()  
	order.recent_update = datetime.utcnow()  

	subject = "Order #" + str(order.id) + "'s funds are being released to you"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to you.\n" +
				   "This may take up to 72 hours to complete, but usually should take less than 24 hours.\n\n" + 
				   "Wallet address: " + order.fernet.decrypt(order.vendor_address.encode()).decode() +
				   "\nShipping cost from our office to buyer: " + str(order.cost_for_shipping_to_buyer) + " XMR" +
				   "\n\nWe will update you when funds get sent to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					  message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
					  message_type="TRANSACTION")  


	subject = "Order #" + str(order.id) + "'s funds are being released to vendor"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to vendor.\n")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message_to_buyer = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
							   message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
							   message_type="TRANSACTION")  


	db.session.add(message)  
	db.session.add(message_to_buyer)  




	db.session.commit()  
	flash("Successfully released funds to vendor.", "alert-green")  
	return redirect(url_for("employees.view_order", order_id=order.id))  













@employees.route("/employee/release/funds/to/buyer", methods=["GET", "POST"])
@login_required
def release_funds_to_buyer():
	order_id = request.args.get("order_id", 0, type=int)  
	order = Order.query.filter_by(id=order_id).first_or_404()  

	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	if order.escrow_released:
		flash("Funds already have been released.", "alert-faded-yellow")  
		return redirect(url_for("employees.view_order", order_id=order.id))  
	elif order.status == "RELEASING FUNDS":
		flash("Funds already are being released.", "alert-faded-yellow")  
		return redirect(url_for("employees.view_order", order_id=order.id))  

		
	
	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  



	# Send to both user and profit later in orders.py sql automation....
	order.status = "RELEASING FUNDS"  
	order.percentage_to_buyer = fernet.encrypt("100".encode()).decode()  

	subject = "Order #" + str(order.id) + "'s funds are being released to you"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to you.\n" +
				   "This may take up to 72 hours to complete, but usually should take less than 24 hours.\n\n" + 
				   "Wallet address: " + order.fernet.decrypt(order.vendor_address.encode()).decode() +
				   "\n\nWe will update you when funds get sent to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					  message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
					  message_type="TRANSACTION")  


	subject = "Order #" + str(order.id) + "'s funds are being released to buyer"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to buyer.\n")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message_to_vendor = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
							   message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
							   message_type="TRANSACTION")  


	db.session.add(message)  
	db.session.add(message_to_vendor)  




	db.session.commit()  
	flash("Successfully released funds to buyer.", "alert-green")  
	return redirect(url_for("employees.view_order", order_id=order.id))  

'''











@employees.route("/admin/info", methods=["GET", "POST"])
@login_required
def info_edit():

	if not current_user.is_admin:
		abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  


	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  

	admin = AdminEditing.query.filter_by(id=1).first_or_404()  
	form = AdminEditingForm()  

	if form.validate_on_submit():
		admin.lowest_price_possible_for_listing = form.lowest_price.data  

		admin.shipping_address = fernet.encrypt(form.shipping_address.data.encode()).decode()  


		admin.admin_who_edited = current_user.username  
		admin.last_time_edited = datetime.utcnow()  

		db.session.commit()  






	elif request.method == "GET":
		form.lowest_price.data = admin.lowest_price_possible_for_listing  

		form.shipping_address.data = fernet.decrypt(admin.shipping_address.encode()).decode()  





	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():
		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/edit_info.html", title="Info", datetime=datetime.utcnow(), form=form, search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  






























@employees.route("/employees/release/buyer/id/<int:order_id>", methods=["GET", "POST"])
@login_required
def release_disputed_funds_to_buyer(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  
	buyer = User.query.filter_by(id=order.user_id).first_or_404()  
	vendor = User.query.filter_by(id=order.vendor_id).first_or_404()  


	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	# Can only extend once....
	if order.status == "RELEASING FUNDS":
		flash("Funds are already being sent to the buyer.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	elif order.escrow_released:
		flash("Funds have already been sent to the buyer.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	elif order.status != "DISPUTING":
		flash("Can only release funds on a dispute, error.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  





	order.recent_update = datetime.utcnow()  
	order.status = "RELEASING FUNDS"  
	buyer.disputes_won = buyer.disputes_won + 1  
	vendor.disputes_lost = vendor.disputes_lost + 1  



	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  

	description_dispute = request.args.get("description_dispute", "No description.", type=str)  
	order.description_dispute = fernet.encrypt(description_dispute.encode()).decode()  
	order.percentage_to_buyer = fernet.encrypt("100".encode()).decode()  

	subject = "Order #" + str(order.id) + "'s dispute has been resolved with you WINNING the dispute."  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to you.\n" +
				   "This may take up to 72 hours to complete, but usually should take less than 24 hours.\n\n" + 
				   "Wallet address: " + fernet.decrypt(order.return_address.encode()).decode() +
				   "\nShipping cost from our office to you: " + str(fernet.decrypt(order.cost_for_shipping_to_buyer.encode()).decode()) + " XMR" +
				   "\nWe will take off shipping cost from your refund, and will incharge fees to the vendor to pay back " +
				   "the shipping costs." + 
				   "\n\nWe will update you when funds get sent to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					  message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
					  message_type="DISPUTE", order_id=order.id)  


	subject = "Order #" + str(order.id) + "'s dispute has been resolved with you LOSING the dispute"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to buyer.\n" + 
				   "You will incur a " + str(fernet.decrypt(order.cost_for_shipping_to_buyer.encode()).decode()) + " XMR fee for shipping costs from our office to the buyer, " +
				   "plus an additional 10%% fee associated with selling of the item." + 
				   "\nYou will have 7 days to claim return of item, else we will proceed to sell the item." +
				   "\nIf claiming return of item, be prepared to pay shipping cost from office to buyer PLUS 10%% fee associated with selling" +
				   " of the item, plus shipping costs from us back to you." )  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message_to_buyer = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
							   message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
							   message_type="DISPUTE", order_id=order.id)  


	db.session.add(message)  
	db.session.add(message_to_buyer)  

	db.session.commit()  

	flash("Successfully released funds to buyer!", "alert-green")  
	return redirect(url_for('employees.view_order', order_id=order_id))  








@employees.route("/employe/release/vendor/id/<int:order_id>", methods=["GET", "POST"])
@login_required
def release_disputed_funds_to_vendor(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  
	buyer = User.query.filter_by(id=order.user_id).first_or_404()  
	vendor = User.query.filter_by(id=order.vendor_id).first_or_404()  

	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  

	# Can only extend once....
	if order.status == "RELEASING FUNDS":
		flash("Funds are already being sent to the vendor.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	elif order.escrow_released:
		flash("Funds have already been sent to the vendor.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	elif order.status != "DISPUTING":
		flash("Can only release funds on a dispute, error.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  





	order.recent_update = datetime.utcnow()  
	order.status = "RELEASING FUNDS"  
	vendor.disputes_won = vendor.disputes_won + 1  
	buyer.disputes_lost = buyer.disputes_lost + 1  



	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  

	description_dispute = request.args.get("description_dispute", "No description.", type=str)  
	order.description_dispute = fernet.encrypt(description_dispute.encode()).decode()  
	order.percentage_to_vendor = fernet.encrypt("100".encode()).decode()  

	subject = "Order #" + str(order.id) + "'s dispute has been resolved with you WINNING the dispute."  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to you.\n" +
				   "This may take up to 72 hours to complete, but usually should take less than 24 hours.\n\n" + 
				   "Wallet address: " + fernet.decrypt(order.vendor_address.encode()).decode() +
				   "\nShipping cost from our office to you: " + str(fernet.decrypt(order.cost_for_shipping_to_buyer.encode()).decode()) + " XMR" +
				   "\nWe will take off shipping cost PLUS 10%% fee off your profit, and any additional fees that you may have." +
				   "\n\nWe will update you when funds get sent to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					  message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
					  message_type="DISPUTE", order_id=order.id)  


	subject = "Order #" + str(order.id) + "'s dispute has been resolved with you LOSING the dispute"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to vendor.\n" + 
				   "You will incur a 10%% fee for deception of wrong-doing, which will be added onto your account.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message_to_buyer = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
							   message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
							   message_type="DISPUTE", order_id=order.id)  


	db.session.add(message)  
	db.session.add(message_to_buyer)  

	db.session.commit()  

	flash("Successfully released funds to vendor!", "alert-green")  
	return redirect(url_for('employees.view_order', order_id=order_id))  





























@employees.route("/employe/release/settled/id/<int:order_id>", methods=["GET", "POST"])
@login_required
def release_disputed_funds_to_settled(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  
	buyer = User.query.filter_by(id=order.user_id).first_or_404()  
	vendor = User.query.filter_by(id=order.vendor_id).first_or_404()  

	to_buyer = request.args.get("to_buyer", "0", type=str)  
	to_seller = request.args.get("to_seller", "0", type=str)  
	description_dispute = request.args.get("description_dispute", "No description.", type=str)  

	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	if to_buyer == "0":
		abort(404)  
	if to_seller == "0":
		abort(404)  

	# Can only extend once....
	if order.status == "RELEASING FUNDS":
		flash("Funds are already being sent to the vendor.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	elif order.escrow_released:
		flash("Funds have already been sent to the vendor.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	elif order.status != "DISPUTING":
		flash("Can only release funds on a dispute, error.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  



	order.recent_update = datetime.utcnow()  
	order.status = "RELEASING FUNDS"  

	buyer.disputes_neutral = buyer.disputes_neutral + 1  
	vendor.disputes_neutral = vendor.disputes_neutral + 1  


	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  

	order.description_dispute = fernet.encrypt(description_dispute.encode()).decode()  
	order.percentage_to_buyer = fernet.encrypt(to_buyer.encode()).decode()  
	order.percentage_to_vendor = fernet.encrypt(to_seller.encode()).decode()  




	subject = "Order #" + str(order.id) + "'s dispute has been resolved with a SETTLEMENT."  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to both you and the vendor.\n" +
				   "This may take up to 72 hours to complete, but usually should take less than 24 hours.\n\n" + 
				   "Wallet address: " + fernet.decrypt(order.return_address.encode()).decode() +
				   "\nPercentage agreed to be given onto you: " + to_buyer +
				   "\nShipping cost from our office to you: " + str(fernet.decrypt(order.cost_for_shipping_to_buyer.encode()).decode()) + " XMR" +
				   "\nWe will take off " + to_buyer + "%% of the (shipping cost PLUS 10%% fee of the item), and any additional fees that you may have." +
				   "\n\nWe will update you when funds get sent to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					  message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
					  message_type="DISPUTE", order_id=order.id)  


	subject = "Order #" + str(order.id) + "'s dispute has been resolved with a SETTLEMENT."  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to both you and the buyer.\n" +
				   "This may take up to 72 hours to complete, but usually should take less than 24 hours.\n\n" + 
				   "Wallet address: " + fernet.decrypt(order.vendor_address.encode()).decode() +
				   "\nPercentage agreed to be given onto you: " + to_seller +
				   "\nShipping cost from our office to the buyer: " + str(fernet.decrypt(order.cost_for_shipping_to_buyer.encode()).decode()) + " XMR" +
				   "\nWe will take off " + to_seller + "%% of the (shipping cost PLUS 10%% fee of the item), and any additional fees that you may have." +
				   "\n\nWe will update you when funds get sent to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message_to_buyer = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
							   message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
							   message_type="DISPUTE", order_id=order.id)  


	db.session.add(message)  
	db.session.add(message_to_buyer)  

	db.session.commit()  

	flash("Successfully settled funds between buyer and vendor!", "alert-green")  
	return redirect(url_for('employees.view_order', order_id=order_id))  

















@employees.route("/employe/request/buyer/return/id/<int:order_id>", methods=["GET", "POST"])
@login_required
def request_buyer_return(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  

	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	if order.request_buyer_return:
		abort(404)  



	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  

	# Create messages ahora
	subject = "Buyer return requested for Order #" + str(order.id)  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s buyer return request has been initiated.\n\n" +
				   "You have up to 48 hours to submit return request form and ship the item back to us, or the funds will be RELEASED to" +
				   " the vendor.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					  message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
					  message_type="DISPUTE", order_id=order.id)  


	subject = "Buyer return requested for Order #" + str(order.id)  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s buyer return request has been initiated.\n\n" +
				   "The buyer will have up to 48 hours to submit return request form and ship the item back to us, or the funds will be RELEASED" +
				   " back to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message_to_buyer = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
							   message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
							   message_type="DISPUTE", order_id=order.id)  

	db.session.add(message)  
	db.session.add(message_to_buyer)  






	order.request_buyer_return = order.recent_update = datetime.utcnow()  
	db.session.commit()  


	flash("Successfully requested buyer return!", "alert-green")  
	return redirect(url_for('employees.view_order', order_id=order_id))  











@employees.route("/employees/review/view", methods=["GET", "POST"])
@login_required
def view_review():
	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	review_id = request.args.get("review_id", 0, type=int)  
	filter_by = request.args.get("filter_by", "vendor", type=str)  
	page = request.args.get("page", 1, type=int)  


	review = Review.query.filter_by(id=review_id).first_or_404()  

	if review.dispute_resolved:
		flash("Dispute for review has been resolved.", "alert-faded-yellow")  
		return redirect(url_for("employees.disputes", filter_by=filter_by, page=page))  





	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  


	form = EditReviewForm()  
	if form.validate_on_submit():
		if request.form.get("review_photos") == "Review_Photos":
			if review.gallery_1:
				delete_review_picture_path(review.gallery_1)  
				review.gallery_1 = None  
			if review.gallery_2:
				delete_review_picture_path(review.gallery_2)  
				review.gallery_2 = None  
			if review.gallery_3:
				delete_review_picture_path(review.gallery_3)  
				review.gallery_3 = None  


		rating = None  
		if request.form.get("star") == "star1":
			rating = 5  
		elif request.form.get("star") == "star2":
			rating = 4  
		elif request.form.get("star") == "star3":
			rating = 3  
		elif request.form.get("star") == "star4":
			rating = 2  
		elif request.form.get("star") == "star5":
			rating = 1  
		else:
			rating = review.rating  
			#flash(f"Please select a star rating.", "alert-red")  
			#return redirect(url_for('employees.view_review', review_id=review_id, filter_by=filter_by, page=page))  



		review.title = form.title.data  
		review.description = form.description.data  	
		review.dispute_resolved = datetime.utcnow()  
		db.session.commit()  

		flash("Successfully edited review", "alert-blue")  
		return redirect(url_for('employees.disputes', filter_by=filter_by, page=page))  



	form.title.data = review.title  
	form.description.data = review.description  


	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():
		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/review.html", title="View Review", datetime=datetime.utcnow(), form=form, search_form=search_form,
						   review=review, fernet=fernet, filter_by=filter_by, page=page, Order=Order, review_id=review_id)  





@employees.route("/employees/review/view/no/change", methods=["GET", "POST"])
@login_required
def no_change_review():
	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	review_id = request.args.get("review_id", 0, type=int)  
	filter_by = request.args.get("filter_by", "vendor", type=str)  
	page = request.args.get("page", 1, type=int)  


	review = Review.query.filter_by(id=review_id).first_or_404()  
	user = User.query.filter_by(id=review.user_id).first()  

	# Change dispute amounts on user profile
	#if user:


	if review.dispute_resolved:
		flash("Dispute for review has been resolved.", "alert-faded-yellow")  
		return redirect(url_for("employees.disputes", filter_by=filter_by, page=page))  



	review.dispute_resolved = datetime.utcnow()  
	db.session.commit()  


	flash("No change was taken place for review dispute.", "alert-blue")  
	return redirect(url_for("employees.disputes", filter_by=filter_by, page=page))  





@employees.route("/employees/review/view/delete/change", methods=["GET", "POST"])
@login_required
def delete_change_review():
	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  


	review_id = request.args.get("review_id", 0, type=int)  
	filter_by = request.args.get("filter_by", "vendor", type=str)  
	page = request.args.get("page", 1, type=int)  


	review = Review.query.filter_by(id=review_id).first_or_404()  

	if review.dispute_resolved:
		flash("Dispute for review has been resolved.", "alert-faded-yellow")  
		return redirect(url_for("employees.disputes", filter_by=filter_by, page=page))  

	review.dispute_resolved = datetime.utcnow()  


	if review.gallery_1:
		delete_review_picture_path(review.gallery_1)  
	if review.gallery_2:
		delete_review_picture_path(review.gallery_2)  
	if review.gallery_3:
		delete_review_picture_path(review.gallery_3)  



	db.session.delete(review)  
	db.session.commit()  


	flash("Review successfully deleted.", "alert-blue")  
	return redirect(url_for("employees.disputes", filter_by=filter_by, page=page))  













@employees.route("/admin/suspend/<string:username>", methods=["GET", "POST"])
@login_required
def suspend_user(username):
	if not current_user.is_admin:
		abort(403)  


	user = User.query.filter_by(username=username).first_or_404()  
	user.suspended = datetime.utcnow()  
	db.session.commit()  

	flash("User suspended", "alert-blue")  


	return redirect(url_for("users.profile", username=username))  



@employees.route("/admin/unsuspend/<string:username>", methods=["GET", "POST"])
@login_required
def unsuspend_user(username):
	if not current_user.is_admin:
		abort(403)  


	user = User.query.filter_by(username=username).first_or_404()  
	user.suspended = None  
	db.session.commit()  

	flash("User unsuspended", "alert-blue")  


	return redirect(url_for("users.profile", username=username))  















@employees.route("/employee/reports", methods=["GET", "POST"])
@login_required
def reports():

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  



	page = request.args.get("page", 1, type=int)  
	filter_by = request.args.get("filter_by", "received", type=str)  


	# Source: http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
	messages = None  
	'''
	if filter_by == "all":
		disputes = Order.query.filter(and_(Order.status == "DISPUTING", or_(Order.buyer_disputed != None, Order.vendor_disputed != None))).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	'''

	if filter_by == "received":
		messages = Message.query.filter(Message.message_type == "REPORT", Message.message_to == 1).order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "sent":
		messages = Message.query.filter(Message.message_type == "REPORT", Message.message_from == 1).order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "all":
		messages = Message.query.filter(Message.message_type == "REPORT").order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	else:
		abort(404)  










	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/reports.html", datetime=datetime.utcnow(), title="Reports", search_form=search_form,
						   filter_by=filter_by, messages=messages, User=User, page=page, fernet=fernet,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  



















@employees.route("/employee/messages", methods=["GET", "POST"])
@login_required
def messages():

	if not current_user.is_employee:
		if not current_user.is_admin:
			abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  



	page = request.args.get("page", 1, type=int)  
	filter_by = request.args.get("filter_by", "received", type=str)  


	# Source: http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
	messages = None  
	'''
	if filter_by == "all":
		disputes = Order.query.filter(and_(Order.status == "DISPUTING", or_(Order.buyer_disputed != None, Order.vendor_disputed != None))).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	'''

	if filter_by == "received":
		messages = Message.query.filter(Message.message_type == "MESSAGE", Message.message_to == 1).order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "sent":
		messages = Message.query.filter(Message.message_type == "MESSAGE", Message.message_from == 1).order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "all":
		messages = Message.query.filter(Message.message_type == "MESSAGE").order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	else:
		abort(404)  










	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/messages.html", datetime=datetime.utcnow(), title="Messages", search_form=search_form,
						   filter_by=filter_by, messages=messages, User=User, page=page, fernet=fernet,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  




@employees.route("/employee/total/messages", methods=["GET", "POST"])
@login_required
def total_messages():

	if not current_user.is_admin:
		abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  



	page = request.args.get("page", 1, type=int)  
	filter_by = request.args.get("filter_by", "received", type=str)  


	# Source: http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
	messages = None  
	'''
	if filter_by == "all":
		disputes = Order.query.filter(and_(Order.status == "DISPUTING", or_(Order.buyer_disputed != None, Order.vendor_disputed != None))).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  
	'''

	if filter_by == "received":
		messages = Message.query.filter(Message.message_to == 1).order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "sent":
		messages = Message.query.filter(Message.message_from == 1).order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "all":
		messages = Message.query.filter(Message.message_from == 1, Message.message_to == 1).order_by(Message.date_created.desc()).paginate(page=page, per_page=10)  
	else:
		abort(404)  










	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/messages_all.html", datetime=datetime.utcnow(), title="Messages", search_form=search_form,
						   filter_by=filter_by, messages=messages, User=User, page=page, fernet=fernet,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  








@employees.route("/employee/total/featured/posts", methods=["GET", "POST"])
@login_required
def featured_posts():

	if not current_user.is_admin:
		abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  


	add_featured_post = AddFeaturedPost()  
	if add_featured_post.data and add_featured_post.submit_featured:

		# Add the featured post into the database
		featured_post = FeaturedPost(post_id=subject_encrypted, date=datetime.utcnow())  

		db.session.add(featured_post)  
		db.session.commit()  





	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("employee/featured.html", datetime=datetime.utcnow(), title="Featured Posts", search_form=search_form, User=User,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  




'''
@employees.route("/employees/review/view/edit/change", methods=["GET", "POST"])
@login_required
def edit_change_review():
	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403)  

			
	review_id = request.args.get("review_id", 0, type=int)  
	filter_by = request.args.get("filter_by", "vendor", type=str)  
	page = request.args.get("page", 1, type=int)  


	review = Review.query.filter_by(id=review_id).first_or_404()  


	review.dispute_resolved = datetime.utcnow()  






	if request.form.get("review_photos") == "Review_Photos":
		if review.gallery_1:
			delete_review_picture_path(review.gallery_1)  
		if review.gallery_2:
			delete_review_picture_path(review.gallery_2)  
		if review.gallery_3:
			delete_review_picture_path(review.gallery_3)  





	
	db.session.commit()  


	flash("Review successfully edited.", "alert-blue")  
	return redirect(url_for("employees.disputes", filter_by=filter_by, page=page))  
'''

