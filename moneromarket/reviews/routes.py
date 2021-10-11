from flask import Blueprint, render_template, flash, redirect, url_for, request, abort  
from flask_login import login_user, current_user, logout_user, login_required  

from moneromarket import db, bcrypt  

from datetime import datetime, timedelta  
import os  
import json  
import random  
import numpy  
from moneromarket.config import config  


from moneromarket.main.forms import SearchForm  
from moneromarket.reviews.forms import CreateReviewForm, DisputeReviewForm  
from moneromarket.database.models import Order, SubCategory, Currency, User, Review  
from moneromarket.reviews.utils import save_picture_review  

# Encryption and decryption
from cryptography.fernet import Fernet  


from monero.wallet import Wallet  
from monero.daemon import Daemon  
from monero.address import address  
from monero.numbers import PaymentID  


# http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
from sqlalchemy import or_  




reviews = Blueprint("reviews", __name__)  




# Logout user
@reviews.route("/review", methods=["GET", "POST"])
@login_required
def create():
	order_id = request.args.get("order_id", 0, type=int)  

	order = Order.query.filter_by(id=order_id).first_or_404()  

	if current_user.id != order.vendor_id:
		if current_user.id != order.user_id:
			abort(403)  


	if order.buyer_reviewed and order.user_id == current_user.id:
		flash("Already submitted review.", "alert-faded-yellow")  
		return redirect(url_for("orders.view_order", order_id=order_id))  
	elif order.vendor_reviewed and order.vendor_id == current_user.id:
		flash("Already submitted review.", "alert-faded-yellow")  
		return redirect(url_for("orders.view_order", order_id=order_id))  


	if datetime.utcnow() > order.escrow_released + timedelta(hours=24*7, minutes=5):
		flash("Time for being able to submit a review has expired (7 days)", "alert-red")  


	if order.status == "AUTO-FINALIZED":
		do = "nothing"  
	elif order.user_id == current_user.id and (order.percentage_to_vendor and not order.percentage_to_buyer and order.buyer_disputed):
		flash("Not allowed to submit a review on a dispute that you LOST.", "alert-red")  
		return redirect(url_for("orders.view_order", order_id=order_id))  
	elif order.vendor_id == current_user.id and not order.percentage_to_vendor:
		flash("Not allowed to submit a review on a dispute that you LOST.", "alert-red")  
		return redirect(url_for("orders.view_order", order_id=order_id)) 

	# Object used to encrypt items
	key = config.get("FERNET_KEY")  
	fernet = Fernet(key.encode())  



	form = CreateReviewForm()  


	if form.validate_on_submit():

		if len(form.description.data) > 500:
			flash("Description for review must be less than 500 characters.", "alert-red")  
			return redirect(url_for("reviews.create", order_id=order_id))  

		if len(form.title.data) > 50:
			flash("Description for review must be less than 50 characters.", "alert-red")  
			return redirect(url_for("reviews.create", order_id=order_id))  


		# Save picture variables for end to save into database
		gallery_1 = None   
		gallery_2 = None   
		gallery_3 = None  


		# Source: https://stackoverflow.com/questions/53021662/multiplefilefield-wtforms
		# If there were any pictures submitted
		if form.pictures.data[0]:
			accepted_extensions = { "jpg", "png", "jpeg", "pneg" }  

			if len(form.pictures.data) > 3:
				flash("3 files maximum are allowed.", "alert-red")  
				return redirect(url_for('reviews.create', order_id=order_id))  

			# Go through each picture to make sure they are the right format
			for picture in form.pictures.data:
				# Format for form.picture.data has nonsense filler in the last three characters
				if str(picture).lower()[-7:-3] in accepted_extensions or str(picture).lower()[-6:-3] in accepted_extensions:
					print("Accepted")  

				else:
					flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
					return redirect(url_for('reviews.create', order_id=order_id))  


			# Save each photo now in the database
			for index in range(len(form.pictures.data)):
				saved_picture = save_picture_review(form.pictures.data[index])  

				if index == 0:
					gallery_1 = saved_picture  

				elif index == 1:
					gallery_2 = saved_picture  

				elif index == 2:
					gallery_3 = saved_picture  





		'''
		# If no images were passed through the form
		else:
			flash("No pictures submitted or registered, please try again.", "alert-red")  
			return redirect(url_for('reviews.create', order_id=order_id))  '''


		rating = 0  
		text = request.form.get("star")  

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
			flash(f"Please select a star rating.", "alert-red")  
			return redirect(url_for("reviews.create", order_id=order_id))  


		buyer = None  
		#vendor_id = Post.query.filter_by(id=order.post_id).first_or_404().vendor.id  
		if current_user.id == order.vendor_id:
			buyer = order.user_id  
		#	vendor_id = buyer  


		review = Review(title=form.title.data, description=form.description.data, rating=rating,
						date_posted=datetime.utcnow(), user_id=current_user.id,
						to_buyer=buyer, post_id=order.post_id, vendor_id=order.vendor_id,
						gallery_1=gallery_1, gallery_2=gallery_2, gallery_3=gallery_3, order_id=order.id)  


		if current_user.id == order.user_id:
			order.buyer_reviewed = True  
		else:
			order.vendor_reviewed = True  

		# Add and save to the database 
		db.session.add(review)  
		db.session.commit()  

		flash("Review successfully submitted", "alert-green")
		return redirect(url_for("orders.view_order", order_id=order_id))  







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


	return render_template("review/create.html", search_form=search_form, datetime=datetime.utcnow(), order=order,
						   SubCategory=SubCategory, fernet=fernet, float=float, numpy=numpy, User=User,
						   usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, form=form, xaut=xaut)  















'''
# Logout user
@reviews.route("/review", methods=["GET", "POST"])
@login_required
def dispute():
	order_id = request.args.get("order_id", 0, type=int)  

	order = Order.query.filter_by(id=order_id).first_or_404()  

	if current_user.id != order.vendor_id:
		if current_user.id != order.user_id:
			abort(403)  



	if order.dispute_date:
		abort(404)  
'''

# Logout user











