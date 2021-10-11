from flask import Blueprint, render_template, flash, redirect, url_for, request, abort  
from flask_login import login_required, current_user  

from moneromarket import db  

from moneromarket.database.models import User, Post, Category, SubCategory, CartItem, Order, Currency, Message, SavedForLaterItem, PendingOrderScreen, OrderPostDetails, AdminEditing, UserFee, OrderPictures, Dispute  
from moneromarket.orders.forms import CheckoutForm, UpdateCartForm, AddToCartForm, OrderAcceptancePhysicalForm, OrderAcceptanceDigitalForm, UpdateSavedForLaterForm, RequestBuyerReturnForm  
from moneromarket.main.forms import SearchForm, AdvancedSearchForm  
from moneromarket.main.utils import get_category_info  

from moneromarket.orders.utils import save_picture_qrcode, delete_picture_qrcode  
from moneromarket.orders.utils import save_picture_copied_post, delete_post_picture_path  
from moneromarket.employees.utils import delete_picture_of_item, delete_picture_of_receipt 

from datetime import datetime, timedelta  
import re  
import math  

import os  
import json  
from moneromarket.config import config  

# Encryption and decryption
from cryptography.fernet import Fernet  


# Monero
from monero.wallet import Wallet  
from monero.backends.jsonrpc import JSONRPCWallet  
from monero.daemon import Daemon  
from monero.address import address  
from monero.numbers import PaymentID  
import random  

from decimal import Decimal  
import numpy  
# Source: https://stackoverflow.com/questions/658763/how-to-suppress-scientific-notation-when-printing-float-values





# Initialize Blueprint
orders = Blueprint("orders", __name__)  




@orders.route("/orders", methods=["GET", "POST"])
@login_required
def list():
	# Object used to decrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  

	page = request.args.get("page", 1, type=int)  
	filter_by = request.args.get("filter_by", "buying", type=str)  
	type_of_table = request.args.get("type_of_table", "individual", type=str)  

	
	


	orders = None  
	if filter_by == "buying":
		if type_of_table == "individual":
			orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  

		elif type_of_table == "all":
			# source: https://stackoverflow.com/questions/22275412/sqlalchemy-return-all-distinct-column-values
			orders = Order.query.filter_by(user_id=current_user.id).with_entities(Order.total_amount_for_payment_id, Order.total_amount_of_orders_for_payment_id, Order.date_ordered, Order.payment_id, Order.confirmations, Order.excess_received, Order.status).distinct().order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  


	elif filter_by == "selling":
		if type_of_table == "all":
			type_of_table = "individual"  

		orders = Order.query.filter(Order.vendor_id == current_user.id, Order.confirmations >= 10, Order.vendor_deleted == False).order_by(Order.recent_update.desc()).paginate(page=page, per_page=10)  






	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	
	return render_template("order/list.html", title="Orders", current_page="account", datetime=datetime.utcnow(), orders=orders, numpy=numpy,
						   search_form=search_form, filter_by=filter_by, User=User, page=page, type_of_table=type_of_table, fernet=fernet, float=float)  








@orders.route("/checkout", methods=["GET", "POST"])
@login_required
# Post_item and post_buying is used if buying straight from item page, no carts registered
def checkout():

	# Check to make sure pending order is valid and correct
	pending_order = PendingOrderScreen.query.filter_by(user_id=current_user.id).first_or_404()  

	cart_list = CartItem.query.filter_by(user_id=current_user.id).order_by(CartItem.date_edited.desc())  
	if not cart_list:
		abort(404)  

	post_details_list = OrderPostDetails.query.filter_by(payment_id=pending_order.payment_id)  
	if not post_details_list:
		return redirect(url_for("orders.pend_order"))  


	# Generate new checkout if cart was edited
	if pending_order.latest_time != cart_list.first().date_edited:
		return redirect(url_for("orders.pend_order"))  






	# Split the time pieces into a string, create a datetime object from it, and compare current time to 2 hours ahead to see if time expired.
	# Source: https://codingpointer.com/python-tutorial/split-string-by-multiple-separators
	# Sorce: https://stackoverflow.com/questions/66218128/convert-string-of-datetime-to-datetime-object
	time_split = re.split("[-:. /s]+", str(pending_order.date_reserved))  
	time_passed = datetime(int(time_split[0]), int(time_split[1]), int(time_split[2]), int(time_split[3]), int(time_split[4]), int(time_split[5]), int(time_split[6]))  
	if datetime.utcnow() > (time_passed + timedelta(minutes=16)):
		print("Order expired, directing to pend_order function...")  
		return redirect(url_for('orders.pend_order'))  






	# Encryption
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  


	form = CheckoutForm()  
	if form.validate_on_submit():
		

		# Process data now from the HTML Form
		name_and_address_encrypted = fernet.encrypt(form.name_and_address.data.encode()).decode()  

		return_address_encrypted = None  
		if form.return_address.data:
			return_address_encrypted = fernet.encrypt(form.return_address.data.encode()).decode()  
		else:
			return_address_encrypted = current_user.public_address  




		# Create a seperate order for each item in the cart
		index = 0  
		date_ordered = datetime.utcnow()  
		payment_id = pending_order.payment_id  
		cart_info_txt = pending_order.list_of_list_of_items.strip("][").split(", ")  
		total_amount_of_cart_items = fernet.encrypt(str(len(cart_info_txt)).encode()).decode()  
		for item in cart_list:

			# If for whatever reason data doesn't match up, abort (SHOULDN'T HAPPEN, but here just in case for error handling)
			splitted_cart_info = cart_info_txt[index].strip(")(").split("_")  
			if item.id != int(splitted_cart_info[0]):
				abort(404)  

			post_detail = OrderPostDetails.query.filter_by(post_id=CartItem.query.filter_by(id=int(splitted_cart_info[0])).first().cart_post.id, payment_id=payment_id).first_or_404()  
			post_detail.pending_order_screen_id = None  
			post_detail.cart_id = None  

			# highest int possible: 9223372036854775807
			random_num = random.randint(1, 9999999999999999)  
			while Order.query.filter_by(id=random_num).first():
				random_num = random.randint(1, 9999999999999999)  

			# source: https://www.youtube.com/watch?v=l4ugfcj7qrI
			# source: https://monero.fandom.com/wiki/URI_formatting
			qrcode = str(save_picture_qrcode(str("monero:" + fernet.decrypt(pending_order.public_address.encode()).decode() + "?tx_amount=" + str(numpy.format_float_positional(float(fernet.decrypt(pending_order.payment_total.encode()).decode()), trim='-', precision=8)) + "&tx_payment_id=" + payment_id)))  

			order = Order(id=random_num, post_id=item.cart_post.id, user_id=current_user.id, vendor_id=item.cart_post.vendor.id,
						  buying_amount=fernet.encrypt(str(int(splitted_cart_info[2])).encode()).decode(), 
						  price_per_item=fernet.encrypt(str(float(splitted_cart_info[1])).encode()).decode(),
						  return_address=return_address_encrypted,
						  name_and_address=name_and_address_encrypted,
						  public_address=pending_order.public_address,
						  account_number=pending_order.account_number, total_amount_of_orders_for_payment_id=total_amount_of_cart_items,
						  payment_id=payment_id, total_amount_for_payment_id=pending_order.payment_total,
						  status="WAITING FOR PAYMENT", date_ordered=date_ordered, recent_update=date_ordered, 
						  qr_code=fernet.encrypt(qrcode.encode()).decode())  

			index += 1  
			db.session.add(order)  
			db.session.delete(item)  



		db.session.delete(pending_order)  
		db.session.commit()  
		flash("Order processed!", "alert-green")  
		return redirect(url_for("orders.checkout_complete", payment_id=payment_id))  







	# Get the variable to print until what time user has to submit order to the database in the top yellow banner.
	# Get hour of datetime string
	hour = str(pending_order.date_reserved)[11:13]  

	# Change 11:00pm to 1:00am && 10:00pm to Midnight
	if hour == "22":
		hour = "00"  

	elif hour == "23":
		hour = "01"  


	# Add 2 to the hour if < 22
	else:
		int_hour = int(hour) + 2  

		# Add leading zero to single digits
		if int_hour < 10:
			hour = "0" + str(int_hour)  
		else:
			hour = str(int_hour)  


	# Get updated hour along with minutes and seconds
	expiration = hour + str(pending_order.date_reserved)[13:19]  





	page = request.args.get("page", 1, type=int)  
	cart_items = cart_list.paginate(page=page, per_page=10)  
	cart_info_txt = pending_order.list_of_list_of_items.strip("][").split(", ")  



	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  




	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  

	return render_template("order/checkout.html", title="Checkout", time_for_order=datetime, datetime=datetime.utcnow(), form=form,
						   total_price=float(fernet.decrypt(pending_order.payment_total.encode()).decode()), numpy=numpy, search_form=search_form,
						   wallet_address=fernet.decrypt(pending_order.public_address.encode()).decode(), timedelta=timedelta, Post=Post,
						   qrcode="None", pending_order=pending_order, fernet=fernet,
						   payment_id=pending_order.payment_id, expiration=expiration, time=pending_order.date_reserved,
						   OrderPostDetails=OrderPostDetails, cart_items=cart_items, cart_info_txt=cart_info_txt, page=page,
						   SubCategory=SubCategory, float=float,
						   usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, post_details_list=post_details_list, xaut=xaut)  








@orders.route("/checkout-complete/<string:payment_id>", methods=["GET", "POST"])
@login_required
def checkout_complete(payment_id):
	return redirect(url_for('orders.view_payment_id', payment_id=payment_id))  







@orders.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
	# Set page for pagination
	page = request.args.get("page", 1, type=int)  

	# Get user information to get cart information specific to the user
	items = CartItem.query.filter_by(user_id=current_user.id).order_by(CartItem.date_saved.desc())  





	# Update the amount on the top right side button filed form shit.
	update_cart_amount_form = UpdateCartForm()  
	update_saved_amount_form = UpdateSavedForLaterForm()  

	if update_cart_amount_form.submit_update_cart.data and update_cart_amount_form.validate_on_submit():
		amount = request.form.get("cart-view-amount")  

		if not amount:
			# flash("Please enter a valid amount to update the amount of items.", "alert-red")  
			do = "nothing"  

		elif amount:
			cart_id = request.form.get("hidden_cart_id")  

			cart = CartItem.query.filter_by(id=int(cart_id)).first()  

			if int(amount) > int(cart.cart_post.supply):
				flash("Error, there are only " + str(cart.cart_post.supply) + " item(s) left in stock.", "alert-red")  
			else:
				cart.buying = int(amount)  
				cart.date_edited = datetime.utcnow()  
				db.session.commit()  
				# flash("Successfully changed", "alert-blue")  

		return redirect(url_for("orders.cart", page=page))  


	elif request.method == "GET":
		update_cart_amount_form.cart_id.data = request.form.get("hidden_cart_id")  



	if update_saved_amount_form.submit_update_saved.data and update_saved_amount_form.validate_on_submit():
		amount = request.form.get("saved-view-amount")  

		if not amount:
			# flash("Please enter a valid amount to update the amount of items.", "alert-red")  
			do = "nothing"  

		elif amount:
			saved_id = request.form.get("hidden_saved_id")  

			saved = SavedForLaterItem.query.filter_by(id=int(saved_id)).first()  

			if int(amount) > int(saved.saved_for_later_post.supply):
				flash("Error, there are only " + str(saved.saved_for_later_post.supply) + " item(s) left in stock.", "alert-red")  
			else:
				saved.buying = int(amount)  
				db.session.commit()  
				# flash("Successfully changed", "alert-blue")  

		return redirect(url_for("orders.cart", page=page))  


	elif request.method == "GET":
		update_saved_amount_form.saved_id.data = request.form.get("hidden_saved_id")  



	if update_saved_amount_form.submit_add_to_cart.data and update_saved_amount_form.validate_on_submit():
		amount = request.form.get("saved-view-amount")  

		saved_id = request.form.get("hidden_saved_id")  

		saved = SavedForLaterItem.query.filter_by(id=int(saved_id)).first()  

		if not amount:
			amount = saved.buying  

		else:
			amount = int(amount)  


		is_in_cart = CartItem.query.filter_by(post_id=saved.post_id, user_id=saved.user_id).first()  

		if is_in_cart:
			if is_in_cart.buying + amount > Post.query.filter_by(id=is_in_cart.post_id).first().supply:
				is_in_cart.buying = Post.query.filter_by(id=is_in_cart.post_id).first().supply  
				is_in_cart.date_edited = datetime.utcnow()  
			else:
				is_in_cart.buying = is_in_cart.buying + amount  
				is_in_cart.date_edited = datetime.utcnow()  
		
		else:
			if saved.buying > Post.query.filter_by(id=saved.post_id).first().supply:
				saved.buying = Post.query.filter_by(id=saved.post_id).first().supply  
			else:
				saved.buying = amount  

			current_date = datetime.utcnow()  
			cart_item = CartItem(user_id=saved.user_id, post_id=saved.post_id, buying=saved.buying, date_saved=current_date, date_edited=current_date)  
			db.session.add(cart_item)  


		db.session.delete(saved)  
		db.session.commit()  
		
		flash("Added to Cart", "alert-blue")  
		return redirect(url_for("orders.cart", page=page))  
















	


	# Get user information to get saved_for_later information specific to the user
	saved_for_later = SavedForLaterItem.query.filter_by(user_id=current_user.id).order_by(SavedForLaterItem.date_saved.desc())  

	# Get total price of all things in cart
	total_price = 0.0  
	for item in items:
		if item.cart_post:

			if item.cart_post.fixed_to_fiat == False:
				total_price = total_price + (item.cart_post.price * item.buying)  

			elif item.cart_post.fixed_to_fiat == True:
				total_price = total_price + ((item.cart_post.price / Currency.query.filter_by(country="USDT").first().price) * item.buying)  


	# Paginate the cart items & saved for later items
	items = items.paginate(page=page, per_page=10)  
	saved_for_later = saved_for_later.paginate(page=page, per_page=10)  




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


	advanced_search_form = AdvancedSearchForm()  
	if advanced_search_form.submit_advanced_search.data and advanced_search_form.validate_on_submit():
		item = request.form.get("item", "", type=str)  
		if not item:
			item = "{NULL}"  

		vendor = request.form.get("vendor", "", type=str)  
		if not vendor:
			vendor = "{NULL}"

		shipping_from = request.form.get("shipping_from", "Any", type=str)  
		shipping_to = request.form.get("shipping_to", "Any", type=str)  



		# Get currency
		currency = request.form.get("currency").upper()  


		price_from = request.form.get("price_from", 0.0, type=float)  
		price_to = request.form.get("price_to", 0.0, type=float)  

		rating_1 = request.form.get("search_rating_1", 0, type=int)  
		rating_2 = request.form.get("search_rating_2", 0, type=int)  
		rating_3 = request.form.get("search_rating_3", 0, type=int)  
		rating_4 = request.form.get("search_rating_4", 0, type=int)  
		rating_5 = request.form.get("search_rating_5", 0, type=int)  


		return redirect(url_for("listings.advanced_search", item=item, vendor=vendor, shipping_from=shipping_from, shipping_to=shipping_to, currency=currency,
								price_from=price_from, price_to=price_to, rating_5=rating_5, rating_4=rating_4, rating_3=rating_3, rating_2=rating_2,
								rating_1=rating_1))  



	return render_template("order/cart.html", title="Cart", items=items, total_price=total_price, time_for_order=datetime, math=math, page=page,
						   SubCategory=SubCategory, datetime=datetime.utcnow(), random=random, update_cart_amount_form=update_cart_amount_form, Currency=Currency,
						   update_saved_amount_form=update_saved_amount_form, usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, numpy=numpy, search_form=search_form, saved_for_later=saved_for_later,
						   xaut=xaut, advanced_search_form=advanced_search_form, categories=get_category_info())  



@orders.route("/cart/delete/<int:cart_id>")
@login_required
def cart_delete(cart_id):
	item = CartItem.query.filter_by(id=cart_id).first_or_404()  


	db.session.delete(item)  
	db.session.commit()  


	flash("Item removed from cart.", "alert-blue")  
	return redirect(url_for('orders.cart'))  

@orders.route("/saved/delete/<int:saved_id>")
@login_required
def saved_delete(saved_id):
	item = SavedForLaterItem.query.filter_by(id=saved_id).first()  


	db.session.delete(item)  
	db.session.commit()  


	flash("Item no longer saved for later.", "alert-blue")  
	return redirect(url_for('orders.cart', username=current_user.username))  


@orders.route("/listings/cart/add/<int:post_id>/buying_<int:buying>", methods=["GET", "POST"])
@login_required
def add_to_cart(post_id, buying =2):
	current_date = datetime.utcnow()  

	post = Post.query.filter_by(id=post_id).first_or_404()  
	cart = CartItem(post_id=post_id, buying=buying, cart_vendor=current_user, date_saved=current_date, date_edited=current_date)  

	saved = SavedForLaterItem.query.filter_by(post_id=post_id, user_id=current_user.id).first()  

	db.session.add(cart)  
	db.session.delete(saved)  
	db.session.commit()  


	flash("Added to cart.", "alert-blue")  
	return redirect(url_for('orders.cart'))  








@orders.route("/refresh/checkout/")
@login_required
def pend_order():
	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  


	# Check to see if user already has a pending order
	pending_order = PendingOrderScreen.query.filter_by(user_id=current_user.id).order_by().first()  
	cart_items = CartItem.query.filter_by(user_id=current_user.id).order_by(CartItem.date_edited.desc())  



	if not cart_items:
		abort(404)  


	if pending_order:

		# If user has not modified cart at all
		if pending_order.latest_time == cart_items.first().date_edited:

			# If 17 minutes have not passed
			time_split = re.split("[-:. /s]+", str(pending_order.date_reserved))  
			time_passed = datetime(int(time_split[0]), int(time_split[1]), int(time_split[2]), int(time_split[3]), int(time_split[4]), int(time_split[5]), int(time_split[6]))  
			if datetime.utcnow() < (time_passed + timedelta(minutes=16)):
				print("HELP")  



				return redirect(url_for('orders.checkout'))  


				# Proceed like normal and skip everything else
				#return redirect(url_for('orders.cart', pending_order_id=pending_order.id))  

			else:
				cart_info_txt = pending_order.list_of_list_of_items.strip("][").split(", ")  
				# Unpend every single item from the pended order
				for unpending_item in cart_info_txt:
					splitted_cart_info = unpending_item.strip(")(").split("_")  


					if Post.query.filter_by(id=int(splitted_cart_info[3])).first() == None:
						continue  


					Post.query.filter_by(id=int(splitted_cart_info[3])).first().pending -= int(splitted_cart_info[2])  


					post_detail = OrderPostDetails.query.filter_by(post_id=int(splitted_cart_info[3]), payment_id=pending_order.payment_id).first()  
					delete_post_picture_path(post_detail.gallery_1)  
					delete_post_picture_path(post_detail.gallery_2)  
					delete_post_picture_path(post_detail.gallery_3)  

					if post_detail.gallery_4:
						delete_post_picture_path(post_detail.gallery_4)  
					if post_detail.gallery_5:
						delete_post_picture_path(post_detail.gallery_5)  
					if post_detail.gallery_6:
						delete_post_picture_path(post_detail.gallery_6)  
					if post_detail.gallery_7:
						delete_post_picture_path(post_detail.gallery_7)  
					if post_detail.gallery_8:
						delete_post_picture_path(post_detail.gallery_8)  
					if post_detail.gallery_9:
						delete_post_picture_path(post_detail.gallery_9)  

					db.session.delete(post_detail)  





				db.session.delete(pending_order)  
				db.session.commit()  
				flash("Time to place order has expired, please try checking out again.", "alert-red")  
				return redirect(url_for("orders.cart"))  


		# If user has modified cart in any way
		else:
			cart_info_txt = pending_order.list_of_list_of_items.strip("][").split(", ")  
			# Unpend every single item from the pended order
			for unpending_item in cart_info_txt:
				splitted_cart_info = unpending_item.strip(")(").split("_")  


				if Post.query.filter_by(id=int(splitted_cart_info[3])).first() == None:
					continue  


				Post.query.filter_by(id=int(splitted_cart_info[3])).first().pending -= int(splitted_cart_info[2])  


				post_detail = OrderPostDetails.query.filter_by(post_id=int(splitted_cart_info[3]), payment_id=pending_order.payment_id).first()  
				delete_post_picture_path(post_detail.gallery_1)  
				delete_post_picture_path(post_detail.gallery_2)  
				delete_post_picture_path(post_detail.gallery_3)  

				if post_detail.gallery_4:
					delete_post_picture_path(post_detail.gallery_4)  
				if post_detail.gallery_5:
					delete_post_picture_path(post_detail.gallery_5)  
				if post_detail.gallery_6:
					delete_post_picture_path(post_detail.gallery_6)  
				if post_detail.gallery_7:
					delete_post_picture_path(post_detail.gallery_7)  
				if post_detail.gallery_8:
					delete_post_picture_path(post_detail.gallery_8)  
				if post_detail.gallery_9:
					delete_post_picture_path(post_detail.gallery_9)  

				db.session.delete(post_detail)  





			db.session.delete(pending_order)  
			db.session.commit()  
			flash("Cart has been modified. Please try checking out again.", "alert-red")  
			return redirect(url_for("orders.cart"))  

	



	# Check supply before wallet instantiation to make it faster for user to know if an item is taken up, or if they are ordering more than
	# what is available. If their is a way to pass by reference the wallet, remove this section from the route
	for item in cart_items:

		if item.cart_post == None:
			flash(f"Post was deleted...", "alert-red")  
			return redirect(url_for("orders.cart"))  


		# Check to see if no one else has pended the order from the time that you checked out until now... UNLIKEY to happen, but still possible...
		elif item.cart_post.supply - item.cart_post.pending == 0:
			flash(f"Post #{ item.cart_post.id } is out of stock, please update cart, or try again later.", "alert-red")  
			return redirect(url_for("orders.cart"))  

		elif item.buying + item.cart_post.pending > item.cart_post.supply:
			flash(f"Amount you want to buy is more than what is available for Post #{ item.cart_post.id }, please update cart, or try again later.", "alert-red")  
			return redirect(url_for("orders.cart"))  
	# End removal right here if found.



	# Traffic wallet through TOR
	daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050")  
	wallet = Wallet(port=28088)  
	# source: https://monero.fandom.com/wiki/URI_formatting
	payment_id = random.randint(111111111111111111, 999999999999999999)  
	payment_id_done = str(PaymentID(payment_id))  

	

	# Get the length of accounts before creating a new one
	number_of_reserved_wallets = len(wallet.accounts)  
	new_address = wallet.new_account().address()  

	# The index of the order's wallet, which by default is the reserved variable. However, verify if it's correct before moving on.
	order_account_number = number_of_reserved_wallets  
	# If somebody else also created a wallet at the same time (highly unlikely, but still possible)
	if wallet.accounts[number_of_reserved_wallets].address() != new_address:

		# Get the current number of reserved wallets now.
		number_of_current_wallets = len(wallet.accounts)  

		# Go through from the index saved before to the amount of wallets available now and find the order's wallet
		for i in range(number_of_reserved_wallets, number_of_current_wallets):
			if wallet.accounts[i].address() == new_address:
				order_account_number = i  



	


	pending_order = PendingOrderScreen(user_id=current_user.id, date_reserved=datetime.utcnow(), payment_id=payment_id_done, 
									   latest_time=cart_items.first().date_edited, qr_code="None", payment_total="0",
									   list_of_list_of_items="[]",
									   account_number=fernet.encrypt(str(order_account_number).encode()).decode(),
									   public_address=fernet.encrypt(str(new_address).encode()).decode())  
	db.session.add(pending_order)  
	db.session.commit()  

	# Now convert list_of_list into big string representation
	# Pass in cart info to get fixed total price, so price change doesnt' affect user when sending Monero
	string_repr = "["  
	total_price = 0.0  
	post_details_list = [ ]  
	for item in cart_items:

		if item == None or item.cart_post == None:
			index = 0  
			for unpending_item in cart_items:
				if unpending_item == item:
					break  

				else:
					# Unpend each item that was pended now....
					unpending_item.cart_post.pending -= unpending_item.buying  

					delete_post_picture_path(post_details_list[index].gallery_1)  
					delete_post_picture_path(post_details_list[index].gallery_2)  
					delete_post_picture_path(post_details_list[index].gallery_3)  

					if post_details_list[index].gallery_4:
						delete_post_picture_path(post_details_list[index].gallery_4)  
					if post_details_list[index].gallery_5:
						delete_post_picture_path(post_details_list[index].gallery_5)  
					if post_details_list[index].gallery_6:
						delete_post_picture_path(post_details_list[index].gallery_6)  
					if post_details_list[index].gallery_7:
						delete_post_picture_path(post_details_list[index].gallery_7)  
					if post_details_list[index].gallery_8:
						delete_post_picture_path(post_details_list[index].gallery_8)  
					if post_details_list[index].gallery_9:
						delete_post_picture_path(post_details_list[index].gallery_9)  

					db.session.delete(post_details_list[index])  
					index += 1  



			db.session.commit()  
			flash(f"A post was deleted, please update cart.", "alert-red")  
			return redirect(url_for("orders.cart"))  

		# Check to see if no one else has pended the order from the time that you checked out until now... UNLIKEY to happen, but still possible...
		elif item.cart_post.supply - item.cart_post.pending <= 0:

			index = 0  
			for unpending_item in cart_items:
				if unpending_item == item:
					break  

				else:
					# Unpend each item that was pended now....
					unpending_item.cart_post.pending -= unpending_item.buying  

					delete_post_picture_path(post_details_list[index].gallery_1)  
					delete_post_picture_path(post_details_list[index].gallery_2)  
					delete_post_picture_path(post_details_list[index].gallery_3)  

					if post_details_list[index].gallery_4:
						delete_post_picture_path(post_details_list[index].gallery_4)  
					if post_details_list[index].gallery_5:
						delete_post_picture_path(post_details_list[index].gallery_5)  
					if post_details_list[index].gallery_6:
						delete_post_picture_path(post_details_list[index].gallery_6)  
					if post_details_list[index].gallery_7:
						delete_post_picture_path(post_details_list[index].gallery_7)  
					if post_details_list[index].gallery_8:
						delete_post_picture_path(post_details_list[index].gallery_8)  
					if post_details_list[index].gallery_9:
						delete_post_picture_path(post_details_list[index].gallery_9)  

					db.session.delete(post_details_list[index])  
					index += 1  



			db.session.commit()  
			flash(f"Another user has reserved the last available spot for Post #{ item.cart_post.id }, please update cart, or try again later.", "alert-red")  
			return redirect(url_for("orders.cart"))  

		elif item.buying + item.cart_post.pending > item.cart_post.supply:

			index = 0  
			for unpending_item in cart_items:
				if unpending_item == item:
					break  

				else:
					# Unpend each item that was pended now....
					unpending_item.cart_post.pending -= unpending_item.buying  

					delete_post_picture_path(post_details_list[index].gallery_1)  
					delete_post_picture_path(post_details_list[index].gallery_2)  
					delete_post_picture_path(post_details_list[index].gallery_3)  

					if post_details_list[index].gallery_4:
						delete_post_picture_path(post_details_list[index].gallery_4)  
					if post_details_list[index].gallery_5:
						delete_post_picture_path(post_details_list[index].gallery_5)  
					if post_details_list[index].gallery_6:
						delete_post_picture_path(post_details_list[index].gallery_6)  
					if post_details_list[index].gallery_7:
						delete_post_picture_path(post_details_list[index].gallery_7)  
					if post_details_list[index].gallery_8:
						delete_post_picture_path(post_details_list[index].gallery_8)  
					if post_details_list[index].gallery_9:
						delete_post_picture_path(post_details_list[index].gallery_9)  

					db.session.delete(post_details_list[index])  
					index += 1  


			db.session.commit()  
			flash(f"Amount you want to buy is more than what is available for Post #{ item.cart_post.id }, please update cart, or try again later.", "alert-red")  
			return redirect(url_for("orders.cart"))  





		# Save all photos into order
		g1=g2=g3=g4=g5=g6=g7=g8=g9=None  


		# Add saving copies later with PIL
		g1 = save_picture_copied_post(item.cart_post.gallery_1)  

		g2 = save_picture_copied_post(item.cart_post.gallery_2)  

		g3 = save_picture_copied_post(item.cart_post.gallery_3)  

		if item.cart_post.gallery_4:
			g4 = save_picture_copied_post(item.cart_post.gallery_4)  

		if item.cart_post.gallery_5:
			g5 = save_picture_copied_post(item.cart_post.gallery_5)  

		if item.cart_post.gallery_6:
			g6 = save_picture_copied_post(item.cart_post.gallery_6)  

		if item.cart_post.gallery_7:
			g7 = save_picture_copied_post(item.cart_post.gallery_7)  

		if item.cart_post.gallery_8:
			g8 = save_picture_copied_post(item.cart_post.gallery_8)  

		if item.cart_post.gallery_9:
			g9 = save_picture_copied_post(item.cart_post.gallery_9)  



		price_per_item = None  
		if item.cart_post.fixed_to_fiat == True:
			price_per_item = float(item.cart_post.price) / float(Currency.query.filter_by(country="USDT").first().price)  
		elif item.cart_post.fixed_to_fiat == False:
			price_per_item = item.cart_post.price  

		post_detail = OrderPostDetails(shipping_from=fernet.encrypt(item.cart_post.shipping_from.encode()).decode(), 
									   shipping_to=fernet.encrypt(item.cart_post.shipping_to.encode()).decode(),
									   post_title=fernet.encrypt(item.cart_post.title.encode()).decode(), 
									   post_description=fernet.encrypt(item.cart_post.description.encode()).decode(),
									   post_refund_policy=fernet.encrypt(item.cart_post.refund_policy.encode()).decode(),
									   gallery_1=g1, gallery_2=g2, gallery_3=g3,
									   gallery_4=g4, gallery_5=g5, gallery_6=g6, gallery_7=g7, gallery_8=g8, gallery_9=g9,
									   post_id=item.cart_post.id, payment_id=payment_id_done,
									   buying_amount=fernet.encrypt(str(item.buying).encode()).decode(),
									   price_per_item=fernet.encrypt(str(price_per_item).encode()).decode(),
									   cart_id=item.id, pending_order_screen_id=pending_order.id)  

		post_details_list.append(post_detail)  







		# Capture price to prevent price difference from total.. UNLIKELY to happen, but still possible....
		captured_price = price_per_item  
		total_price += item.buying * captured_price  
		item.cart_post.pending += item.buying  


		# Commit so that there is less of a chance of 2 people buying the same product and running out of stock at the same time.
		db.session.add(post_detail)  
		db.session.commit()  



		
		# Now append to string
		if len(string_repr) != 1:
			string_repr += ", "  

		# FORMAT: [0] = cart_id, [1] = price, [2] = buying, [3] = post_id    |    REPRESENTATION example: (1_1.56_1) 
		string_repr += '(' + str(item.id) + '_' + numpy.format_float_positional(captured_price, trim='-', precision=8) + '_' + str(item.buying) + '_' + str(item.post_id) + ')'  
	# End representation example: [(1_1.56_1), (2_2.56_3), (3_0.000005_7), (4_1.00000069_1), (5_5_2)]
	string_repr += ']'  




	# source: https://www.youtube.com/watch?v=l4ugfcj7qrI
	qrcode = str(save_picture_qrcode(str("monero:" + str(new_address) + "?tx_amount=" + numpy.format_float_positional(total_price, trim='-', precision=8) + "&tx_payment_id=" + payment_id_done)))  

	pending_order.qr_code = qrcode  
	pending_order.list_of_list_of_items = string_repr  
	pending_order.payment_total = fernet.encrypt(str(total_price).encode()).decode()  
	db.session.commit()  


	return redirect(url_for('orders.checkout'))  























































@orders.route("/accept/order/<int:order_id>", methods=["GET", "POST"])
@login_required
def accept(order_id):
	message_id = request.args.get("message_id", 0, type=int)  
	form_physical = OrderAcceptancePhysicalForm()  
	form_digital = OrderAcceptanceDigitalForm()  

	order = Order.query.filter_by(id=order_id).first_or_404()  

	# If user is not allowed access
	if current_user.id != order.vendor_id:
		abort(403)  


	# Print 404 if user already accepted offer.
	if order.vendor_accepted:
		flash(f"Order has already been provided a Tracking Number/ID. If wanting to change, please message ADMIN", "alert-faded-yellow")  

		if message_id:
			return redirect(url_for("messages.view", message_id=message_id, direction="received"))  
		else:
			return redirect(url_for("orders.list", filter_by="selling"))  
		# abort(404)  


	if order.date_ordered < datetime.utcnow() + timedelta(hours=-72):
		flash("Order was cancelled, and a 6%% FEE was incharged for waiting over 72 hours", "alert-faded-yellow")  
		
		fee_incharge = "five " + str(0.06 * (float(fernet.decrypt(order.buying_amount.encode()).decode()) * float(fernet.decrypt(order.price_per_item.encode()).decode())))  
		zero_zero = str(0.0)  
		total_amount_owed_5_percent = fernet.encrypt(str(fee_incharge).encode()).decode()  
		total_amount_paid_off = fernet.encrypt(zero_zero.encode()).decode()  


		user_fee = UserFee(user_id=current_user.id, vendor_id=order.vendor_id, order_id=order.id, 
							   total_amount_owed_5_percent=total_amount_owed_5_percent,
							   total_amount_paid_off=total_amount_paid_off, date_reserved=datetime.utcnow())  

		db.session.add(user_fee)  
		db.session.commit()  

		return redirect(url_for('orders.list'))  
		return redirect(url_for('orders.list'))  


	
	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  



	if form_physical.validate_on_submit():
		

		# Fee incharges fron buyer.
		# If 24 hours passes
		if order.date_ordered < datetime.utcnow() + timedelta(hours=-24):
			fee_incharge =  0.01 * (float(fernet.decrypt(order.buying_amount.encode()).decode()) * float(fernet.decrypt(order.price_per_item.encode()).decode()))  
			flash("1%% FEE was incharged for waiting over 24 hours", "alert-faded-yellow")  

			zero_zero = str(0.0)  
			total_amount_owed_5_percent = fernet.encrypt(str(fee_incharge).encode()).decode()  
			total_amount_paid_off = fernet.encrypt(zero_zero.encode()).decode()  


			user_fee = UserFee(user_id=current_user.id, vendor_id=order.vendor_id, order_id=order.id, 
								   total_amount_owed_5_percent=total_amount_owed_5_percent,
								   total_amount_paid_off=total_amount_paid_off, date_reserved=datetime.utcnow())  

			db.session.add(user_fee)  

		elif order.date_ordered < datetime.utcnow() + timedelta(hours=-48):
			fee_incharge =  0.03 * (float(fernet.decrypt(order.buying_amount.encode()).decode()) * float(fernet.decrypt(order.price_per_item.encode()).decode()))  
			flash("3%% FEE was incharged for waiting over 48 hours", "alert-faded-yellow")  

			zero_zero = str(0.0)  
			total_amount_owed_5_percent = fernet.encrypt(str(fee_incharge).encode()).decode()  
			total_amount_paid_off = fernet.encrypt(zero_zero.encode()).decode()  


			user_fee = UserFee(user_id=current_user.id, vendor_id=order.vendor_id, order_id=order.id, 
								   total_amount_owed_5_percent=total_amount_owed_5_percent,
								   total_amount_paid_off=total_amount_paid_off, date_reserved=datetime.utcnow())  

			db.session.add(user_fee)  




		# Add tracking number and time form was filled out onto order.
		order.tracking_number = fernet.encrypt(form_physical.tracking_number.data.encode()).decode()  
		order.vendor_accepted = order.vendor_shipped = order.recent_update = datetime.utcnow()  
		order.status = "VENDOR SHIPPED"  

		# Size of 95 is the standard size for Monero wallet addresses.
		if form_physical.wallet_address.data == None or len(form_physical.wallet_address.data) != 95:
			order.vendor_address = current_user.public_address  
		else:
			order.vendor_address = fernet.encrypt(form_physical.wallet_address.data.encode()).decode()  

		if form_physical.description.data == None or form_physical.description.data == "":
			string_text = "User did not fill anything out."  
			order.description_vendor = fernet.encrypt(string_text.encode()).decode()  
		else:
			order.description_vendor = fernet.encrypt(form_physical.description.data.encode()).decode()  


		# Edit message status from OPENED to ACCEPTED
		#message_self = Message.query.filter_by(id=message_id).first()  
		#message_self.status = "ACCEPTED"  



		# Encrypt message data to create a new message
		subject = ("Order #" + str(order_id) + " has been shipped by " + str(order.orders_post.vendor.username))  
		description = ("Order #" + str(order_id) + " '" + order.orders_post.title + "'" + "\nTracking number has been provided to us, and your package is on it's way to our office." +
					   "\nWe will notify you when we receive the package and will immediatly ship it to you, and provide the tracking number " +
					   "for you to track the package after it has shipped from our office.")  

		subject_vendor = ("Order #" + str(order_id) + " has been successfully processed to " + User.query.filter_by(id=order.user_id).first().username)  
		vendor_description = ("Order #" + str(order_id) + " '" + order.orders_post.title + "'" + "\nTracking Number/ID that you provided is: " + form_physical.tracking_number.data +
							  "\nIf the information is incorrect, please reply to this message with corrected Tracking Number/ID." + 
							  "\n\nPlease note that incorrect or fake Tracking Number/ID not fixed soon will result in a LOSS.")  

		subject_encrypted = fernet.encrypt(subject.encode()).decode()  
		description_encrypted = fernet.encrypt(description.encode()).decode()  

		subject_vendor_encrypted = fernet.encrypt(subject_vendor.encode()).decode()  
		description_vendor_encrypted = fernet.encrypt(vendor_description.encode()).decode()  
		ADMIN = 1  


		# Add new message to the database
		message_to_user = Message(title=subject_encrypted, description=description_encrypted, message_from=ADMIN, 
						  message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type="TRANSACTION", order_id=order.id)  
		db.session.add(message_to_user)  

		# Add new message to the database
		message_to_vendor = Message(title=subject_vendor_encrypted, description=description_vendor_encrypted, message_from=ADMIN, 
						  message_to=current_user.id, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type="TRANSACTION", order_id=order.id)  
		db.session.add(message_to_vendor)  



		# Save all changes
		db.session.commit()  


		flash("Transaction Number/ID successfully processed!", "alert-green")  
		return redirect(url_for('orders.list'))  



	elif form_digital.validate_on_submit():
		# If digital.
		tracking_number_null = "No tracking number needed, order is digital."
		order.tracking_number = fernet.encrypt(tracking_number_null.encode()).decode()  
		order.vendor_accepted = order.vendor_shipped = order.recent_update = datetime.utcnow()  
		order.status = "VENDOR SHIPPED"  

		# Size of 95 is the standard size for Monero wallet addresses.
		if form_digital.wallet_address.data == None or len(form_digital.wallet_address.data) != 95:
			order.vendor_address = current_user.public_address  
		else:
			order.vendor_address = fernet.encrypt(form_digital.wallet_address.data.encode()).decode()  

		if form_digital.description.data == None or form_digital.description.data == "":
			string_text = "User did not fill anything out."  
			order.description_vendor = fernet.encrypt(string_text.encode()).decode()  
		else:
			order.description_vendor = fernet.encrypt(form_digital.description.data.encode()).decode()  


		# Edit message status from OPENED to ACCEPTED
		#message_self = Message.query.filter_by(id=message_id).first()  
		#message_self.status = "ACCEPTED"  



		# Encrypt message data to create a new message
		subject = ("Order #" + str(order_id) + " has been digitally sent to us by " + str(order.orders_post.vendor.username))  
		description = ("Order #" + str(order_id) + " '" + order.orders_post.title + "'" + 
					   "\nDigital good details/file(s) have been sent to us to verify content is real." +
					   "\nWe will notify you when the digital is done being reviewed, and will send to you after for you to verify content(s).")  

		subject_vendor = ("Order #" + str(order_id) + " has been successfully processed to " + User.query.filter_by(id=order.user_id).first().username)  
		vendor_description = ("Order #" + str(order_id) + " '" + order.orders_post.title + "'" +
							  "\nDigital good details/file(s) have been sent to us to verify content is real." +
					   		  "\nWe will notify you when the digital is done being reviewed, and will send to buyer after for them to verify content(s).")  

		subject_encrypted = fernet.encrypt(subject.encode()).decode()  
		description_encrypted = fernet.encrypt(description.encode()).decode()  

		subject_vendor_encrypted = fernet.encrypt(subject_vendor.encode()).decode()  
		description_vendor_encrypted = fernet.encrypt(vendor_description.encode()).decode()  
		ADMIN = 1  


		# Add new message to the database
		message_to_user = Message(title=subject_encrypted, description=description_encrypted, message_from=ADMIN, 
						  message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type="TRANSACTION", order_id=order.id)  
		db.session.add(message_to_user)  

		# Add new message to the database
		message_to_vendor = Message(title=subject_vendor_encrypted, description=description_vendor_encrypted, message_from=ADMIN, 
						  message_to=current_user.id, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type="TRANSACTION", order_id=order.id)  
		db.session.add(message_to_vendor)  



		# Save all changes
		db.session.commit()  


		flash("Digital item(s) successfully processed!", "alert-green")  
		return redirect(url_for('orders.list'))  



	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("order/info/accept.html", datetime=datetime.utcnow(), form_physical=form_physical, order=order, 
						   SubCategory=SubCategory, numpy=numpy, search_form=search_form, User=User, AdminEditing=AdminEditing, 
						   fernet=fernet, OrderPostDetails=OrderPostDetails, float=float, form_digital=form_digital)  






@orders.route("/cart/saveforlater/<int:cart_id>")
@login_required
def cart_save_for_later(cart_id):

	cart_item = CartItem.query.filter_by(id=cart_id).first()  

	if not cart_item:
		abort(404)  

	if cart_item.user_id != current_user.id:
		abort(403)  

	


	is_already_saved = SavedForLaterItem.query.filter_by(user_id=current_user.id, post_id=cart_item.post_id).first()  

	if is_already_saved:
		if is_already_saved.buying + cart_item.buying <= cart_item.cart_post.supply :
			is_already_saved.buying = is_already_saved.buying + cart_item.buying  
		else:
			is_already_saved.buying = cart_item.cart_post.supply  

	else:
		saved_for_later = SavedForLaterItem(post_id=cart_item.post_id, user_id=current_user.id, buying=cart_item.buying,
										date_saved=datetime.utcnow())  

		db.session.add(saved_for_later)  


	edit_time = CartItem.query.filter_by(user_id=current_user.id).order_by(CartItem.date_edited.desc()).first()  
	edit_time.date_edited = datetime.utcnow()  

	db.session.delete(cart_item)  
	db.session.commit()  


	flash("Saved for Later", "alert-blue")  
	return redirect(url_for("orders.cart"))  










@orders.route("/orders/payment-id/<string:payment_id>", methods=["GET", "POST"])
@login_required
def view_payment_id(payment_id):
	page = request.args.get("page", 1, type=int)  
	orders = Order.query.filter_by(payment_id=payment_id).paginate(page=page, per_page=10)  

	if orders.total == 0:
		abort(404)  
	elif orders.items[0].user_id != current_user.id:
		abort(403)  
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

	return render_template("order/info/payment.html", title="Checked-Out", datetime=datetime.utcnow(), orders=orders,
						   SubCategory=SubCategory, public_address=public_address, fernet=fernet, float=float,
						   payment_id=payment_id, refund_address=refund_address, confirmations=confirmations, total_price=total_price,
						   numpy=numpy, search_form=search_form, page=page, timedelta=timedelta, User=User,
						   usdt=usdt, btc=btc, bch=bch, ltc=ltc, doge=doge, eth=eth, xaut=xaut)  





@orders.route("/order/id/<int:order_id>", methods=["GET", "POST"])
@login_required
def view_order(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  


	transaction_id = request.args.get("transaction_id", "", type=str)  
	account_number = request.args.get("account_number", 0, type=int)  

	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  

	if order.user_id != current_user.id:
		# Edit this later to include all instances where vendor is not allowed to see
		if order.vendor_id == current_user.id and (order.status != "PENDING" or order.status == "REFUNDING"):

			# Make the search bar on the top right work
			search_form = SearchForm()  
			if search_form.validate_on_submit():
				return redirect(url_for("listings.search", text=search_form.text.data))  

			if order.status == "WAITING FOR VENDOR":
				return redirect(url_for('orders.accept', order_id=order_id))  


			# Get currency rate
			usdt = Currency.query.filter_by(country="USDT").first().price  
			btc = Currency.query.filter_by(country="BTC").first().price  
			eth = Currency.query.filter_by(country="ETH").first().price  
			bch = Currency.query.filter_by(country="BCH").first().price  
			ltc = Currency.query.filter_by(country="LTC").first().price  
			doge = Currency.query.filter_by(country="DOGE").first().price  
			xaut = Currency.query.filter_by(country="XAUT").first().price  

			return render_template("order/info/vendor.html", title="Checked-Out", datetime=datetime.utcnow(), order=order,
						   SubCategory=SubCategory, fernet=fernet, float=float, OrderPostDetails=OrderPostDetails,
						   numpy=numpy, search_form=search_form, timedelta=timedelta, User=User,
						   usdt=usdt, btc=btc, eth=eth, bch=bch, doge=doge, ltc=ltc, xaut=xaut)  
		elif current_user.is_admin or current_user.is_employee:
			return redirect(url_for('employees.view_order', order_id=order_id))  


		else:
			abort(403)  




	if order.vendor_id == current_user.id:
		if not order.waiting_for_vendor:
			abort(404)  

		elif not order.vendor_accepted:
			return redirect(url_for("orders.accept", order_id=order_id))  

		else:
			# Make the search bar on the top right work
			search_form = SearchForm()  
			if search_form.validate_on_submit():
				return redirect(url_for("listings.search", text=search_form.text.data))  


			return render_template("order/info/vendor.html", title="Checked-Out", datetime=datetime.utcnow(), order=order,
								   SubCategory=SubCategory, fernet=fernet, float=float,
								   numpy=numpy, search_form=search_form, timedelta=timedelta, OrderPostDetails=OrderPostDetails, User=User)  






	# For user
	public_address = fernet.decrypt(order.public_address.encode()).decode()  


	confirmations = order.confirmations  
	if confirmations > 10:
		confirmations = 10  


	total_price = float(fernet.decrypt(order.buying_amount.encode()).decode()) * float(fernet.decrypt(order.price_per_item.encode()).decode())  

	
	refund_address = fernet.decrypt(order.return_address.encode()).decode()  







	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  






	# Request Buyer Return Form
	request_buyer_return_form = RequestBuyerReturnForm()  
	if request_buyer_return_form.validate_on_submit():

		# Check to see if time didn't expire
		if datetime.utcnow() > order.request_buyer_return + timedelta(hours=48, minutes=10):
			abort(404)  


		if order.buyer_shipped:
			abort(404)  

		order.tracking_number = fernet.encrypt(request_buyer_return_form.tracking_number.data.encode()).decode()  


		description = "User didn't fill out anything in description."  
		if request_buyer_return_form.description.data:
			description = request_buyer_return_form.description.data  

		order.description_buyer = fernet.encrypt(description.encode()).decode()  
		order.recent_update = order.buyer_shipped = datetime.utcnow()  




		subject = "Buyer SUBMITTED return requested for Order #" + str(order.id)  
		description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s buyer return request has been submitted.\n\n" +
					   "We are now waiting for package to arrive, and we will determine who is in the right.")  

		subject_encrypted = fernet.encrypt(subject.encode()).decode()  
		description_encrypted = fernet.encrypt(description.encode()).decode()  

		message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					      message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
					      message_type="DISPUTE", order_id=order.id)  

		db.session.add(message)  


		subject = "Successfully SUBMITTED return requested for Order #" + str(order.id)  
		description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s buyer return request has been submitted.\n\n" +
					   "We are now waiting for package to arrive, and we will determine who is in the right.")  

		subject_encrypted = fernet.encrypt(subject.encode()).decode()  
		description_encrypted = fernet.encrypt(description.encode()).decode()  

		message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					      message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
					      message_type="DISPUTE", order_id=order.id)  

		db.session.add(message)  





		db.session.commit()  
		flash("Submitted Request Buyer Return Form Successfully!", "alert-green")  


		request_buyer_return_form.tracking_number.data = None  
		return redirect(url_for('orders.view_order', order_id=order_id))  






	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("order/info/individual.html", title="Checked-Out", datetime=datetime.utcnow(), order=order,
						   SubCategory=SubCategory, public_address=public_address, fernet=fernet, float=float,
						   refund_address=refund_address, confirmations=confirmations, total_price=total_price,
						   numpy=numpy, search_form=search_form, timedelta=timedelta, User=User, OrderPictures=OrderPictures,
						   btc=btc, bch=bch, ltc=ltc, usdt=usdt, doge=doge, eth=eth, xaut=xaut,
						   request_buyer_return_form=request_buyer_return_form, AdminEditing=AdminEditing)  

































@orders.route("/order/extend/id/<int:order_id>", methods=["GET", "POST"])
@login_required
def extend_finalization(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  

	if order.user_id != current_user.id:
		abort(403)  


	# Time expired.
	if datetime.utcnow() >= order.auto_finalization_timer:
		do_somthing = "ok"  

	# Can only extend once....
	if order.recent_update != order.shipped_from_office:
		flash("Can only extend auto-finalization once.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	if datetime.utcnow() < order.auto_finalization_timer - timedelta(hours=72):
		flash("Needs to be 3 days or less for extending auto-finalization to take place.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  




	# 7 days
	order.auto_finalization_timer = order.auto_finalization_timer + timedelta(hours=168)  
	order.recent_update = datetime.utcnow()  

	db.session.commit()  

	flash("Successfully extended auto-finalization!", "alert-blue")  
	return redirect(url_for('orders.view_order', order_id=order_id))  



@orders.route("/order/release/id/<int:order_id>", methods=["GET", "POST"])
@login_required
def release_funds(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  

	if order.user_id != current_user.id:
		abort(403)  

	# Can only extend once....
	if order.status == "RELEASING FUNDS":
		flash("Funds are already being sent to the vendor.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  

	elif order.escrow_released:
		flash("Funds have already been sent to the vendor.", "alert-red")  
		return redirect(url_for('orders.view_order', order_id=order_id))  





	order.recent_update = datetime.utcnow()  
	order.status = "RELEASING FUNDS"  



	key = config.get("FERNET_KEY")  
	fernet=Fernet(key.encode())  
	order.percentage_to_vendor = fernet.encrypt("100".encode()).decode()  

	subject = "Order #" + str(order.id) + "'s funds are being released to you"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to you.\n" +
				   "This may take up to 72 hours to complete, but usually should take less than 24 hours.\n\n" + 
				   "Wallet address: " + fernet.decrypt(order.vendor_address.encode()).decode() +
				   "\nShipping cost from our office to buyer: " + str(fernet.decrypt(order.cost_for_shipping_to_buyer.ecndoe()).decode()) + " XMR" +
				   "\n\nWe will update you when funds get sent to you.")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
					  message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
					  message_type="TRANSACTION", order_id=order_id)  


	subject = "Order #" + str(order.id) + "'s funds are being released to vendor"  
	description = ("Order #" + str(order.id) + " '" + order.orders_post.title + "'s funds are being released to vendor.\n")  

	subject_encrypted = fernet.encrypt(subject.encode()).decode()  
	description_encrypted = fernet.encrypt(description.encode()).decode()  

	message_to_buyer = Message(title=subject_encrypted, description=description_encrypted, message_from=1, 
							   message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
							   message_type="TRANSACTION", order_id=order_id)  


	db.session.add(message)  
	db.session.add(message_to_buyer)  





	# Update post pending and sales.
	post = Post.query.filter_by(id=order.post_id).first_or_404()  
	post.sales = post.sales + int(fernet.decrypt(order.buying_amount.encode()).decode())  
	post.pending = post.pending - int(fernet.decrypt(order.buying_amount.encode()).decode())  
	post.supply = post.supply - int(fernet.decrypt(order.buying_amount.encode()).decode())  


	db.session.commit()  

	flash("Successfully released funds to vendor!", "alert-green")  
	return redirect(url_for('orders.view_order', order_id=order_id))  




















@orders.route("/order/cancel/<int:order_id>", methods=["GET", "POST"])
@login_required
def cancel_order(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  

	if order.user_id != current_user.id:
		abort(403)  





	if order.status == "PENDING":
		order.status = "CANCELLING AND REFUNDING"  

		flash("Order successfully cancelled and will be sent to you shortly.", "alert-blue")  








@orders.route("/order/delete/<int:order_id>")
@login_required
def delete_order(order_id):
	order = Order.query.filter_by(id=order_id).first_or_404()  
	previous_page = request.args.get("previous_page", "orders.list", type=str)  
	page = request.args.get("page", 1, type=int)  
	filter_by = request.args.get("filter_by", "buying", type=str)  

	if order.user_id != current_user.id:
		if order.vendor_id != current_user.id:
			abort(403)  



	if order.escrow_released == None and order.status != "NO PAYMENT" and order.status != "UNCONFIRMED" and order.status != "CANCELLED":
		if previous_page == "orders.list":
			flash("Order in TRANSACTION cannot be deleted.", "alert-red")  
			return redirect(url_for('orders.list', page=page, filter_by=filter_by))  


		else:
			flash("Order in TRANSACTION cannot be deleted.", "alert-red")  
			return redirect(url_for('orders.view_payment_id', page=page))  



	if order.status == "NO PAYMENT" or order.status == "UNCONFIRMED":
		if order.vendor_id == current_user.id: 
			abort(403)  



		if order.order_post_details:
			post_details = OrderPostDetails.query.filter_by(id=order.order_post_details).first()  


			if post_details.gallery_1:
				delete_post_picture_path(post_details.gallery_1)  

			if post_details.gallery_2:
				delete_post_picture_path(post_details.gallery_2)  

			if post_details.gallery_3:
				delete_post_picture_path(post_details.gallery_3)  

			if post_details.gallery_4:
				delete_post_picture_path(post_details.gallery_4)  

			if post_details.gallery_5:
				delete_post_picture_path(post_details.gallery_5)  

			if post_details.gallery_6:
				delete_post_picture_path(post_details.gallery_6)  

			if post_details.gallery_7:
				delete_post_picture_path(post_details.gallery_7)  

			if post_details.gallery_8:
				delete_post_picture_path(post_details.gallery_8)  

			if post_details.gallery_9:
				delete_post_picture_path(post_details.gallery_9)  


			db.session.delete(post_details)  
			order.order_post_details = None  


		db.session.delete(order)  
		db.session.commit()  


		flash("Order deleted.", "alert-blue")  
		return redirect(url_for('orders.list'))  




	if (order.vendor_deleted and current_user.id == order.vendor_id) or (order.buyer_deleted and current_user.id == order.user_id):
		abort(403)  




	if (not order.vendor_deleted and current_user.id == order.vendor_id and not order.buyer_deleted):
		order.vendor_deleted = True  
		db.session.commit()  
		flash("Successfully deleted order", "alert-blue")  
		
		if previous_page == "orders.view_payment_id":
			return redirect(url_for(previous_page, payment_id=order.payment_id, page=page))  
		else:
			return redirect(url_for(previous_page, filter_by=filter_by))  

	if (not order.buyer_deleted and current_user.id == order.user_id and not order.vendor_deleted):
		order.buyer_deleted = True  
		db.session.commit()  
		flash("Successfully deleted order", "alert-blue")  

		if previous_page == "orders.view_payment_id":
			return redirect(url_for('orders.view_payment_id', payment_id=order.payment_id, page=page))  
		else:
			return redirect(url_for(previous_page,filter_by=filter_by))  



	if (order.vendor_deleted and current_user.id == order.user_id) or (order.buyer_deleted and current_user.id == order.vendor_id):
		if order.order_pictures_id:
			pictures = OrderPictures.query.filter_by(id=order.order_pictures_id).first()  

			# Delete receipt
			if pictures.receipt_picture:
				delete_picture_of_receipt(pictures.receipt_picture)  


			if pictures.gallery_1:
				delete_picture_of_item(pictures.gallery_1)  

			if pictures.gallery_2:
				delete_picture_of_item(pictures.gallery_2)  

			if pictures.gallery_3:
				delete_picture_of_item(pictures.gallery_3)  

			if pictures.gallery_4:
				delete_picture_of_item(pictures.gallery_4)  

			if pictures.gallery_5:
				delete_picture_of_item(pictures.gallery_5)  

			if pictures.gallery_6:
				delete_picture_of_item(pictures.gallery_6)  

			if pictures.gallery_7:
				delete_picture_of_item(pictures.gallery_7)  

			if pictures.gallery_8:
				delete_picture_of_item(pictures.gallery_8)  

			if pictures.gallery_9:
				delete_picture_of_item(pictures.gallery_9)  

			if pictures.gallery_10:
				delete_picture_of_item(pictures.gallery_10)  

			if pictures.gallery_11:
				delete_picture_of_item(pictures.gallery_11)  

			if pictures.gallery_12:
				delete_picture_of_item(pictures.gallery_12)  

			if pictures.gallery_13:
				delete_picture_of_item(pictures.gallery_13)  

			if pictures.gallery_14:
				delete_picture_of_item(pictures.gallery_14)  

			if pictures.gallery_15:
				delete_picture_of_item(pictures.gallery_15)  

			if pictures.gallery_16:
				delete_picture_of_item(pictures.gallery_16)  

			if pictures.gallery_17:
				delete_picture_of_item(pictures.gallery_17)  

			if pictures.gallery_18:
				delete_picture_of_item(pictures.gallery_18)  

			if pictures.gallery_19:
				delete_picture_of_item(pictures.gallery_19)  

			if pictures.gallery_20:
				delete_picture_of_item(pictures.gallery_20)  

			if pictures.gallery_21:
				delete_picture_of_item(pictures.gallery_21)  


			db.session.delete(pictures)  


		db.session.delete(order)  
		db.session.commit()  


		flash("Order deleted.", "alert-blue")  
		return redirect(url_for('orders.list'))  













@orders.route("/checkout/original/<int:post_id>/<string:payment_id>", methods=["GET", "POST"])
@login_required
def checkout_original_item(post_id, payment_id):

	order = PendingOrderScreen.query.filter_by(payment_id=payment_id).first_or_404()  

	# Only employees, admins, buyer, and seller can view the original item.
	if order.user_id != current_user.id:
		abort(403)  



	previous_page = request.args.get("previous_page", "main.home", type=str)  
	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  


	original = OrderPostDetails.query.filter_by(post_id=post_id, payment_id=payment_id).first_or_404()  







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

	return render_template("order/info/original.html", datetime=datetime.utcnow(), title="Original item", search_form=search_form, original=original,
						   previous_page=previous_page, Post=Post, User=User, order=order, numpy=numpy, fernet=fernet, float=float,
						   usdt=usdt, btc=btc, bch=bch, ltc=ltc, eth=eth, doge=doge, xaut=xaut)  
