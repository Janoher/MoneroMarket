from flask import Blueprint, render_template, flash, redirect, url_for, request ;
from flask_login import login_user, current_user, logout_user, login_required ;

from moneromarket.users.forms import RegistrationForm, LoginForm ;
from moneromarket.users.forms import (ChangePasswordForm, AddEmailForm, UpdateEmailForm, 
									  DeleteEmailForm, OneTimePasswordForm, DeleteAccountForm, UpdateProfileForm) ;

from moneromarket import db, bcrypt ;
from moneromarket.database.models import User, Post, CartItem, FavoriteUser, FavoriteItem, Message, SubCategory, Order, Currency, Review ;

from moneromarket.users.utils import save_picture, delete_profile_picture, delete_post ;
from moneromarket.orders.utils import save_picture_qrcode, delete_picture_qrcode ;
from moneromarket.main.forms import SearchForm ;
from moneromarket.reviews.forms import DisputeReviewForm ;

from datetime import datetime, timedelta ;
import os ;
import json ;
import random ;
import numpy ;
from moneromarket.config import config ;

# Encryption and decryption
from cryptography.fernet import Fernet ;


from monero.wallet import Wallet ;
from monero.backends.jsonrpc import JSONRPCWallet ;
from monero.daemon import Daemon ;
from monero.address import address ;
from monero.numbers import PaymentID ;


# http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
from sqlalchemy import or_ ;




users = Blueprint("users", __name__) ;



@users.route("/register", methods=["GET", "POST"])
def register():

	# If user is already logged in, redirect back to home page to not allow user to register again
	if current_user.is_authenticated:
		return redirect(url_for("main.home")) ;




	form = RegistrationForm() ;

	if form.validate_on_submit():
		# Hash password and transform into a string
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8") ;

		if form.email.data:
			form.email.data = form.email.data.lower() ;







		# Traffic wallet through TOR
		daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050") ;
		# Instantiate the wallet
		wallet = Wallet(port=28088) ;
		
		key = config.get("FERNET_KEY") ;

		# Object used to encrypt items
		fernet = Fernet(key.encode()) ;


		# Get the length of accounts before creating a new one
		number_of_reserved_wallets = len(wallet.accounts) ;
		new_address = wallet.new_account().address() ;

		# The index of the user's wallet, which by default is the reserved variable. However, verify if it's correct before moving on.
		user_account_number = number_of_reserved_wallets ;
		# If somebody else also created a wallet at the same time (highly unlikely, but still possible)
		if wallet.accounts[number_of_reserved_wallets].address() != new_address:

			# Get the current number of reserved wallets now.
			number_of_current_wallets = len(wallet.accounts) ;

			# Go through from the index saved before to the amount of wallets available now and find the user's wallet
			for i in range(number_of_reserved_wallets, number_of_current_wallets):
				if wallet.accounts[i].address() == new_address:
					user_account_number = i ;


		qrcode = str(save_picture_qrcode(str("monero:" + str(new_address)))) ;


		# highest in: 9223372036854775807
		random_num = random.randint(1, 9223372036854775807) ;
		while User.query.filter_by(id=random_num).first():
			random_num = random.randint(1, 9223372036854775807) ;

		# Create a new user and pass in the info from the front-end, and also the hashed password, and user's wallet account number encrypted
		user = User(id=random_num, username=form.username.data, email=form.email.data, password=hashed_password,
				    account_number=fernet.encrypt(str(user_account_number).encode()).decode(), 
				    public_address=fernet.encrypt(str(new_address).encode()).decode(),
				    qr_code=fernet.encrypt(qrcode.encode()).decode()) ;

		# Add and commit user to the database
		db.session.add(user) ;
		db.session.commit() ;


		# Return to login screen
		flash(f"Account created for { form.username.data }, you are now able to log in!", "alert-green") ;
		return redirect(url_for("users.login")) ;


	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("login/register.html", title="Register", form=form, current_page="register", datetime=datetime.utcnow(),
						   search_form=search_form) ;



@users.route("/login", methods=["GET", "POST"])
def login():

	# If user is already logged in, redirect back to home page to not allow user to login again
	if current_user.is_authenticated:
		return redirect(url_for("main.home")) ;


	form = LoginForm() ;


	# Jump here when submit button is pressed
	if form.validate_on_submit():

		# Check database if username and/or email exists, and save results into their corresponding variables
		username = User.query.filter(User.username.like('%' + form.username_or_email.data + '%')).first() ;
		# username = User.query.filter_by(username=form.username_or_email.data).first() ;
		email = User.query.filter_by(email=form.username_or_email.data).first() ;

		# If username exists and the password entered matches
		if username and bcrypt.check_password_hash(username.password, form.password.data):
			login_user(username) ;

			# Print flashed message on the top of the screen after successful login
			flash("Successfully logged in!", "alert-green") ;


			# Log login date and time
			current_user.last_login = datetime.utcnow() ;
			current_user.last_seen = datetime.utcnow() ;
			db.session.commit() ;


			# Redirect to page user tried to access after being required to login
			next_page = request.args.get("next") ;
			if next_page:
				return redirect(next_page) ;

			# Return to home if no redirect
			return redirect(url_for("main.home")) ;

		# If email exists and the password entered matches
		elif email and bcrypt.check_password_hash(email.password, form.password.data):
			login_user(email) ;

			# Print flashed message on the top of the screen after successful login
			flash("Successfully logged in!", "alert-green") ;

			# Log login date and time
			current_user.last_login = datetime.utcnow() ;
			current_user.last_seen = datetime.utcnow() ;
			db.session.commit() ;

			# Redirect to page user tried to access after being required to login
			next_page = request.args.get("next") ;
			if next_page:
				return redirect(next_page) ;

			# Return to home if no redirect
			return redirect(url_for("main.home")) ;



		# Login credentials don't exist in database
		else:
			# If no instance of '@' in data, then it means it was an invalid username
			if form.username_or_email.data.rfind('@') == -1:
				flash("Login unsuccessful, please check username and password.", "alert-red") ;

			# Invalid email
			else:
				flash("Login unsuccessful, please check email and password.", "alert-red") ;



	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;


	return render_template("login/login.html", title="Login", form=form, current_page="login", datetime=datetime.utcnow(),
						   search_form=search_form) ;






@users.route("/profile/<string:username>", methods=["GET", "POST"])
def profile(username):
	user = User.query.filter_by(username=username).first_or_404() ;

	page = request.args.get("page", 1, type=int) ;
	filter_by = request.args.get("filter_by", "buyer", type=str) ;




	# Reviews
	reviews_buyer = Review.query.filter_by(to_buyer=user.id).order_by(Review.date_posted.desc()) ;
	#reviews = total_reviews.paginate(page=page, per_page=10) ;




	
	key = config.get("FERNET_KEY") ;
	# Object used to encrypt items
	fernet = Fernet(key.encode()) ;


	dispute_form = DisputeReviewForm() ;
	if dispute_form.submit.data and dispute_form.validate_on_submit():


		review_id = request.form.get("hidden_review_id") ;
		post_id = request.form.get("hidden_post_id") ;
		review = Review.query.filter_by(id=int(review_id), post_id=int(post_id)).first_or_404() ;


		if filter_by == "seller" and (review.vendor_id != current_user.id or review.to_buyer):
			abort(403) ;
		elif filter_by == "buyer" and review.to_buyer != current_user.id:
			abort(403) ;


		if review.dispute_date:
			flash("Dispute for review already submitted", "alert-faded-yellow") ;
			return redirect(url_for('users.profile', username=username, page=page, filter_by=filter_by)) ;


		if datetime.utcnow() > review.date_posted + timedelta(hours=24*7, minutes=5):
			flash("Time for being able to dispute a review has expired (7 days)", "alert-red") ;
			return redirect(url_for('users.profile', username=username, page=page, filter_by=filter_by)) ;


		# Don't allow more than 500 words
		if len(dispute_form.description.data) > 500:
			flash("Reasoning for dispute must be less than 500 characters.", "alert-red") ;
			return redirect(url_for('users.profile', username=username, page=page, filter_by=filter_by)) ;




		review.dispute_text = fernet.encrypt(dispute_form.description.data.encode()).decode() ;
		review.dispute_date = datetime.utcnow() ;

		db.session.commit() ;
		return redirect(url_for('users.profile', username=username, page=page, filter_by=filter_by)) ;











	# Variable to keep track of review counting stuff
	# for the list, it's [ 'negative' 'nuetrual' 'positive' ]
	buyer_points = 0.0 ;
	buyer_one_month = [ 0, 0, 0 ] ;
	buyer_six_months = [ 0, 0, 0 ] ;
	buyer_twelve_months = [ 0, 0, 0 ] ;
	buyer_all_time = [ 0, 0, 0 ] ;
	

	for review in reviews_buyer:
		buyer_points += review.rating ;

		# Neutral rating
		if review.rating > 2.4 and review.rating < 3.6:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				buyer_one_month[1] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				buyer_six_months[1] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				buyer_twelve_months[1] += 1 ;
			else:
				buyer_all_time[1] += 1 ;

		# Negative rating
		elif review.rating < 2.5:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				buyer_one_month[0] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				buyer_six_months[0] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				buyer_twelve_months[0] += 1 ;
			else:
				buyer_all_time[0] += 1 ;


		# positive rating
		elif review.rating > 3.5:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				buyer_one_month[2] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				buyer_six_months[2] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				buyer_twelve_months[2] += 1 ;
			else:
				buyer_all_time[2] += 1 ;



	# Get average star rating for entire post of all the reviews associated with post
	reviews_buyer_count = 0 ;

	if reviews_buyer:
		reviews_buyer_count = reviews_buyer.count() ;


	if reviews_buyer_count == 0:
		buyer_points = 0.0 ;
	else:
		buyer_points /= reviews_buyer_count ;



	reviews_buyer = reviews_buyer.paginate(page=page, per_page=10) ;










	# Seller reviews
	# Reviews
	reviews_seller = Review.query.filter_by(vendor_id=user.id, to_buyer=None).order_by(Review.date_posted.desc()) ;
	#reviews = total_reviews.paginate(page=page, per_page=10) ;



	# Variable to keep track of review counting stuff
	# for the list, it's [ 'negative' 'nuetrual' 'positive' ]
	seller_points = 0.0 ;
	seller_one_month = [ 0, 0, 0 ] ;
	seller_six_months = [ 0, 0, 0 ] ;
	seller_twelve_months = [ 0, 0, 0 ] ;
	seller_all_time = [ 0, 0, 0 ] ;
	

	for review in reviews_seller:
		seller_points += review.rating ;

		# Neutral rating
		if review.rating > 2.4 and review.rating < 3.6:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				seller_one_month[1] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				seller_six_months[1] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				seller_twelve_months[1] += 1 ;
			else:
				seller_all_time[1] += 1 ;

		# Negative rating
		elif review.rating < 2.5:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				seller_one_month[0] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				seller_six_months[0] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				seller_twelve_months[0] += 1 ;
			else:
				seller_all_time[0] += 1 ;


		# positive rating
		elif review.rating > 3.5:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				seller_one_month[2] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				seller_six_months[2] += 1 ;
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				seller_twelve_months[2] += 1 ;
			else:
				seller_all_time[2] += 1 ;



	# Get average star rating for entire post of all the reviews associated with post
	reviews_seller_count = 0 ;

	if reviews_seller:
		reviews_seller_count = reviews_seller.count() ;


	if reviews_seller_count == 0:
		seller_points = 0.0 ;
	else:
		seller_points /= reviews_seller_count ;



	reviews_seller = reviews_seller.paginate(page=page, per_page=10) ;




















	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		if User.query.filter_by(username=search_form.text.data).first():
			return redirect(url_for('users.profile', username=search_form.text.data)) ;

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("profile/profile.html", title="Profile", current_page="profile", user=user, datetime=datetime.utcnow(),
						   search_form=search_form, Post=Post, reviews_buyer=reviews_buyer, page=page, filter_by=filter_by,
						   buyer_points=buyer_points, buyer_one_month=buyer_one_month, buyer_six_months=buyer_six_months,
						   buyer_twelve_months=buyer_twelve_months, buyer_all_time=buyer_all_time, User=User,
						   reviews_seller=reviews_seller, seller_points=seller_points, seller_all_time=seller_all_time, timedelta=timedelta,
						   seller_one_month=seller_one_month, seller_six_months=seller_six_months, seller_twelve_months=seller_twelve_months,
						   dispute_form=dispute_form) ;










@users.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
	form = UpdateProfileForm() ;


	if form.validate_on_submit():

		accepted_extensions = { "jpg", "png", "jpeg", "pneg" } ;
		# Format for form.picture.data has nonsense filler in the last three characters
		if str(form.picture.data).lower()[-7:-3] in accepted_extensions or str(form.picture.data).lower()[-6:-3] in accepted_extensions:

			# Save image
			saved_picture = save_picture(form.picture.data) ;
			current_user.profile_picture = saved_picture ;
			db.session.commit() ;

			flash("Your account has been updated!", "alert-green") ;
			return redirect(url_for("users.profile", username=current_user.username)) ;

		elif form.picture.data:
			flash("Only .jpg, .png, .jpeg, and .pneg files are allowed, please try again.", "alert-red") ;
			return redirect(url_for("users.edit_profile")) ;

		else:
			x = "" ;


	elif request.method == "GET":
		form.description.data = current_user.description ;
		form.refund.data = current_user.refund_policy ;



	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("profile/edit_profile.html", title="Edit Profile", current_page="profile", form=form, datetime=datetime.utcnow(),
						   search_form=search_form) ;













@users.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():
	page_user = request.args.get("page_user", 1, type=int) ;
	page_item = request.args.get("page_item", 1, type=int) ;

	favorite_users = FavoriteUser.query.filter_by(user_id=current_user.id).paginate(page=page_user, per_page=10) ;

	favorite_items = FavoriteItem.query.filter_by(user_id=current_user.id).paginate(page=page_item, per_page=10) ;



	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;


	# Get currency rate for fixed to fiat instances
	usdt = Currency.query.filter_by(country="USDT").first().price ;
	btc = Currency.query.filter_by(country="BTC").first().price ;
	eth = Currency.query.filter_by(country="ETH").first().price ;
	bch = Currency.query.filter_by(country="BCH").first().price ;
	ltc = Currency.query.filter_by(country="LTC").first().price ;
	doge = Currency.query.filter_by(country="DOGE").first().price ;
	xaut = Currency.query.filter_by(country="XAUT").first().price ;



	return render_template("profile/favorites.html", title="Favorites", current_page="account", Post=Post, User=User, numpy=numpy, usdt=usdt,
						   favorite_users=favorite_users, favorite_items=favorite_items, datetime=datetime.utcnow(), search_form=search_form,
						   btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, xaut=xaut, float=float, page_user=page_user, page_item=page_item) ;






@users.route("/favorites/user/add/<string:username>")
@login_required
def add_to_favorites_users(username):

	user = User.query.filter_by(username=username).first() ;
	fav_user = FavoriteUser(user_id=current_user.id, favorited_user=user.id) ;

	

	db.session.add(fav_user) ;
	db.session.commit() ;


	flash("Added to favorites.", "alert-blue") ;
	return redirect(url_for('users.profile', username=username)) ;




@users.route("/favorites/post/add/<int:post_id>")
@login_required
def add_to_favorites_posts(post_id):

	post = Post.query.filter_by(id=post_id).first() ;

	is_favorited = FavoriteItem.query.filter_by(user_id=current_user.id, post_id=post_id).first() ;

	if is_favorited:
		flash("Post is already in your favorites list", "alert-faded-yellow") ;

	else:
		fav_post = FavoriteItem(user_id=current_user.id, post_id=post_id) ;

		db.session.add(fav_post) ;
		db.session.commit() ;

		flash("Added to favorites.", "alert-blue") ;


	return redirect(url_for('listings.item', username=current_user.username, post_id=post_id, previous_page="listings.item")) ;



@users.route("/favorites/user/delete/<int:favorite_id>")
@login_required
def delete_favorites_user(favorite_id):
	fav_user = FavoriteUser.query.filter_by(id=favorite_id).first() ;
	username = User.query.filter_by(id=fav_user.user_id).first().username ;
	
	if fav_user:
		db.session.delete(fav_user) ;
		db.session.commit() ;
		flash("Deleted " + str(username) + " from your favorites", "alert-blue") ;

	else:
		flash("Error, no favorited user found to be deleted", "alert-red") ;


	
	return redirect(url_for('users.favorites')) ;


@users.route("/favorites/listing/delete/<int:favorite_id>")
@login_required
def delete_favorites_listing(favorite_id):
	fav_listing = FavoriteItem.query.filter_by(id=favorite_id).first() ;
	
	if fav_listing:
		db.session.delete(fav_listing) ;
		db.session.commit() ;
		flash("Deleted listing from your favorites", "alert-blue") ;

	else:
		flash("Error, no favorited listing found to be deleted", "alert-red") ;


	
	return redirect(url_for('users.favorites')) ;




























@users.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

	# All our forms
	change_password_form = ChangePasswordForm() ;
	one_time_password_form = OneTimePasswordForm() ;
	delete_account_form = DeleteAccountForm() ;

	add_email_form = AddEmailForm() ;
	update_email_form = UpdateEmailForm() ;
	delete_email_form = DeleteEmailForm() ; 









	# Source for getting multiple forms in a single route to work
	# https://stackoverflow.com/questions/18290142/multiple-forms-in-a-single-page-using-flask-and-wtforms

	# Basically just have all the submit buttons have a different name
	# And check the "if" statement exactly the way I have it in that order with that syntax when submit button is pressed.










	# Jump here when submit button is pressed
	if change_password_form.submit.data and change_password_form.validate_on_submit():

		# If current password is correct
		if bcrypt.check_password_hash(current_user.password, change_password_form.current_password.data):

			# Hash password and transform into a string
			hashed_password = bcrypt.generate_password_hash(change_password_form.new_password.data).decode("utf-8") ;
			current_user.password = hashed_password ;
			db.session.commit() ;


			flash("Your password has been changed!", "alert-green") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("users.settings")) ;


		# If current password is invalid
		else:
			flash("Password not correct, please try again.", "alert-red") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("users.settings")) ;



	

	elif add_email_form.submit_add_email.data and add_email_form.validate_on_submit():

		# Basic email check
		if str(add_email_form.data).find("@") == -1:

			flash("Not a valid email address, please try again", "alert-red") ;
			return redirect(url_for("users.settings")) ;




		if not User.query.filter_by(email=add_email_form.email.data.lower()).first():
			current_user.email = add_email_form.email.data.lower() ;
			db.session.commit() ;

			flash("Email account successfully added!", "alert-green") ;
			return redirect(url_for("users.settings")) ;

		else:
			flash("Email account already taken, please try another one.", "alert-red") ;
			return redirect(url_for("users.settings")) ;




	elif update_email_form.submit_update_email.data and update_email_form.validate_on_submit():

		# Basic email check
		if str(update_email_form.data).find("@") == -1:

			flash("Not a valid email address, please try again", "alert-red") ;
			return redirect(url_for("users.settings")) ;



		# If the email submitted is the user's current email
		if update_email_form.email.data.lower() == current_user.email:
			return redirect(url_for("users.settings")) ;


		if not User.query.filter_by(email=update_email_form.email.data.lower()).first():
			current_user.email = update_email_form.email.data.lower() ;
			db.session.commit() ;

			flash("Email account successfully updated!", "alert-green") ;
			return redirect(url_for("users.settings")) ;

		else:
			flash("Email account already taken, please try another one.", "alert-red") ;
			return redirect(url_for("users.settings")) ;




	# Jump here when submit button is pressed
	elif delete_email_form.submit_delete_email.data and delete_email_form.validate_on_submit():

		# If current entered password is correct
		if bcrypt.check_password_hash(current_user.password, delete_email_form.password.data):

			current_user.email = "" ;
			db.session.commit() ;


			flash("Your email has been deleted from your account!", "alert-green") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("users.settings")) ;



		# If entered password is invalid
		else:
			flash("Password not correct, please try again.", "alert-red") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("users.settings")) ;

	








	

	# Jump here when submit button is pressed
	elif one_time_password_form.submit_one_time_password.data and one_time_password_form.validate_on_submit():

		# If current entered password is correct
		if bcrypt.check_password_hash(current_user.password, one_time_password_form.password.data):

			flash("Your one-time password is: h7se3dhhgda22he1@", "alert-green") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("users.settings")) ;



		# If entered password is invalid
		else:
			flash("Password not correct, please try again.", "alert-red") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("users.settings")) ;






	

	# Jump here when submit button is pressed
	elif delete_account_form.submit_delete_account.data and delete_account_form.validate_on_submit():

		# If current entered password is correct
		if bcrypt.check_password_hash(current_user.password, delete_account_form.password.data):


			# Delete old profile picture
			delete_profile_picture(current_user.profile_picture) ;



			# Get all posts from user
			posts = Post.query.filter_by(vendor=current_user).all() ;

			# Delete them all
			for post in posts:
				delete_post(post.id) ;


			username = current_user.username ;
			db.session.delete(current_user) ;
			db.session.commit() ;

			logout_user() ;



			flash(f"Account \"{ username }\" has now been deleted.", "alert-blue") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("main.home")) ;



		# If entered password is invalid
		else:
			flash("Password is not correct, please try again.", "alert-red") ;
			# Prevent get request form pop-up on a refresh
			return redirect(url_for("users.settings")) ;





	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("settings/settings.html", title="Settings", current_page="account",
						   add_email_form=add_email_form, update_email_form=update_email_form,
						   delete_email_form=delete_email_form, one_time_password_form=one_time_password_form,
						   delete_account_form=delete_account_form, change_password_form=change_password_form,
						   datetime=datetime.utcnow(), search_form=search_form) ;





# Logout user
@users.route("/logout")
def logout():

	# Log logout date and time
	current_user.last_seen = datetime.utcnow() ;
	db.session.commit() ;

	logout_user() ;

	flash("You have been signed out.", "alert-faded-yellow") ;
	return redirect(url_for("main.home")) ;















