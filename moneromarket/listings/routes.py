from flask import Blueprint, render_template, flash, redirect, url_for, request  
from flask_login import login_required, current_user  

from moneromarket import db, bcrypt  
from moneromarket.database.models import User, Post, Category, SubCategory, CartItem, Order, Currency, SavedForLaterItem, Review, Dispute  
from moneromarket.listings.forms import CreateListingForm, EditListingForm  
from moneromarket.orders.forms import AddToCartForm  
from moneromarket.main.forms import SearchForm, AdvancedSearchForm  
from moneromarket.main.utils import get_category_info  

from moneromarket.listings.utils import save_picture_created_post, save_picture_edit_post, delete_post_picture_path  
from sqlalchemy import or_  

from datetime import datetime  
from datetime import timedelta   # To add 3 hours to current time for checkout
import numpy  
import math  
import random  



#import flask_whooshalchemy  




# Initialize Blueprint
listings = Blueprint("listings", __name__)  


@listings.route("/search/<string:text>", methods=["GET", "POST"])
def search(text):
	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	filter_by = request.args.get("filter_by", "newest", type=str)  

	page = request.args.get("page", 1, type=int)  

	posts = None  
	if filter_by == "newest":
		posts = Post.query.filter(Post.title.contains(text)).order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)  
	if filter_by == "oldest":
		posts = Post.query.filter(Post.title.contains(text)).order_by(Post.date_posted.asc()).paginate(page=page, per_page=10)  
	if filter_by == "high":
		posts = Post.query.filter(Post.title.contains(text)).order_by(Post.price.desc()).paginate(page=page, per_page=10)  
	if filter_by == "low":
		posts = Post.query.filter(Post.title.contains(text)).order_by(Post.price.asc()).paginate(page=page, per_page=10)  
	if filter_by == "random":

		gallery = [ Post.gallery_1, Post.gallery_2, Post.gallery_3 ]  
		random_gallery = random.randrange(0, 3)  
		up = random.randrange(0, 2)  

		if up:
			posts = Post.query.filter(Post.title.contains(text)).order_by(gallery[random_gallery].asc()).paginate(page=page, per_page=10)  
		else:
			posts = Post.query.filter(Post.title.contains(text)).order_by(gallery[random_gallery].desc()).paginate(page=page, per_page=10)  


	link_back = "listings.search"  







	# Failed attempt at saving amount buying when adding to cart
	form = AddToCartForm()  

	if form.validate_on_submit() and (form.submit_cart.data or form.submit_buy.data or form.submit_saved.data):

		# If user is already logged in, redirect back to home page to not allow user to register again
		if not current_user.is_authenticated:
			flash("Login required", "alert-blue")  
			return redirect(url_for("users.login"))  

		buying = request.form.get("quantity-buying")  

		if not buying:
			buying = 1  

		elif int(buying) < 1:
			flash("Can't put 0 or negative amount of item in cart..", "alert-red")  
			return redirect(url_for('listings.search', text=text, filter_by=filter_by))  


		post_id = request.form.get("hidden_post_id")  

		if post_id:
			post_id = int(post_id)  

			is_already_in_cart = CartItem.query.filter_by(user_id=current_user.id, post_id=post_id).first()  

			if is_already_in_cart:
				is_already_in_cart.buying = is_already_in_cart.buying + int(buying)  


			else:
				current_date = datetime.utcnow()  
				cart = CartItem(post_id=post_id, buying=int(buying), user_id=current_user.id, date_saved=current_date, date_edited=current_date)  
				db.session.add(cart)  

			
			db.session.commit()  

		

			flash("Successfully added to cart", "alert-blue")  







	'''
	# Get currency rate
	usd = Currency.query.filter_by(country="USD").first().price  
	eur = Currency.query.filter_by(country="EUR").first().price  
	gbp = Currency.query.filter_by(country="GBP").first().price  
	cad = Currency.query.filter_by(country="CAD").first().price  
	aud = Currency.query.filter_by(country="AUD").first().price  
	chf = Currency.query.filter_by(country="CHF").first().price  
	cny = Currency.query.filter_by(country="CNY").first().price  
	jpy = Currency.query.filter_by(country="JPY").first().price  
	krw = Currency.query.filter_by(country="KRW").first().price  
	rub = Currency.query.filter_by(country="RUB").first().price  
	inr = Currency.query.filter_by(country="INR").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	'''
	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  



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


	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  





	return render_template("listing/search.html", title="Search", link_back=link_back, posts=posts, datetime=datetime.utcnow(),
						   usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, search_form=search_form, page=page, filter_by=filter_by, text=text,
						   SubCategory=SubCategory, numpy=numpy, form=form, Currency=Currency, xaut=xaut,
						   advanced_search_form=advanced_search_form, categories=get_category_info(),
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  
















@listings.route("/advanced/search/<string:item>/<string:vendor>/<string:shipping_from>/<string:shipping_to>/<string:currency>/<float:price_from>/<float:price_to>/<int:rating_5>/<int:rating_4>/<int:rating_3>/<int:rating_2>/<int:rating_1>", methods=["GET", "POST"])
def advanced_search(item, vendor, shipping_from, shipping_to, currency, price_from, price_to, rating_5, rating_4, rating_3, rating_2, rating_1):
	filter_by = request.args.get("filter_by", "newest", type=str)  
	page = request.args.get("page", 1, type=int)  


	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  


	# Source: https://www.reddit.com/r/flask/comments/8y92c0/help_sqlalchemy_multiple_filter_queries/
	# Declare session, and initiate with if statements below
	query = db.session.query(Post)  
	if item != "{NULL}":
		query = query.filter(Post.title.contains(item))  

	if vendor != "{NULL}":
		query = query.filter(Post.vendor == User.query.filter(User.username.like('%' + vendor + '%')).first())  

	if price_from:
		currency_price = None  
		if currency == "XMR":
			currency_price = float(price_from) * float(Currency.query.filter_by(country="USDT").first().price)  

		elif currency != "USDT":
			currency_price = float(price_from) * (float(Currency.query.filter_by(country="USDT").first().price) / float(Currency.query.filter_by(country=currency).first().price))  

		elif currency == "USDT":
			currency_price = price_from  

		query = query.filter(Post.price >= currency_price)  

	if price_to:
		currency_price = None  
		if currency == "XMR":
			currency_price = float(price_to) * float(Currency.query.filter_by(country="USDT").first().price)  

		elif currency != "USDT":
			currency_price = float(price_to) * (float(Currency.query.filter_by(country="USDT").first().price) / float(Currency.query.filter_by(country=currency).first().price))  

		elif currency == "USDT":
			currency_price = price_to  

		query = query.filter(Post.price <= currency_price)  




	if shipping_from != "Any":
		query = query.filter(Post.shipping_from == shipping_from)  

	if shipping_to != "Any":
		query = query.filter(Post.shipping_to == shipping_to)  


	"""
	if rating_1:
		query = query.filter(Post.reviews == Review.query.filter_by(rating=rating_1))  
	if rating_2:
		query = query.filter(Post.reviews == Review.query.filter_by(rating=rating_2))  
	if rating_3:
		query = query.filter(Post.reviews == Review.query.filter_by(rating=rating_3))  
	if rating_4:
		query = query.filter(Post.reviews == Review.query.filter_by(rating=rating_4))  
	if rating_5:
		query = query.filter(Post.reviews == Review.query.filter_by(rating=rating_5))  
	"""


    # Get all
	result = query.all()  



	posts = None  
	if filter_by == "newest":
		posts = query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)  
	if filter_by == "oldest":
		posts = query.order_by(Post.date_posted.asc()).paginate(page=page, per_page=10)  
	if filter_by == "high":
		posts = query.order_by(Post.price.desc()).paginate(page=page, per_page=10)  
	if filter_by == "low":
		posts = query.order_by(Post.price.asc()).paginate(page=page, per_page=10)  
	if filter_by == "random":

		gallery = [ Post.gallery_1, Post.gallery_2, Post.gallery_3 ]  
		random_gallery = random.randrange(0, 3)  
		up = random.randrange(0, 2)  

		if up:
			posts = query.order_by(gallery[random_gallery].asc()).paginate(page=page, per_page=10)  
		else:
			posts = query.order_by(gallery[random_gallery].desc()).paginate(page=page, per_page=10)  


	link_back = "listings.search"  







	# Failed attempt at saving amount buying when adding to cart
	form = AddToCartForm()  

	if form.validate_on_submit() and (form.submit_cart.data or form.submit_buy.data or form.submit_saved.data):

		# If user is already logged in, redirect back to home page to not allow user to register again
		if not current_user.is_authenticated:
			flash("Login required", "alert-blue")  
			return redirect(url_for("users.login"))  

		buying = request.form.get("quantity-buying")  

		if not buying:
			buying = 1  

		elif int(buying) < 1:
			flash("Can't put 0 or negative amount of item in cart..", "alert-red")  
			return redirect(url_for('listings.search', text=text, filter_by=filter_by))  


		post_id = request.form.get("hidden_post_id")  

		if post_id:
			post_id = int(post_id)  

			is_already_in_cart = CartItem.query.filter_by(user_id=current_user.id, post_id=post_id).first()  

			if is_already_in_cart:
				is_already_in_cart.buying = is_already_in_cart.buying + int(buying)  


			else:
				current_date = datetime.utcnow()  
				cart = CartItem(post_id=post_id, buying=int(buying), user_id=current_user.id, date_saved=current_date, date_edited=current_date)  
				db.session.add(cart)  

			
			db.session.commit()  

		

			flash("Successfully added to cart", "alert-blue")  



	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  



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


	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  




	return render_template("listing/advanced_search.html", title="Search", link_back=link_back, posts=posts, datetime=datetime.utcnow(),
						   usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, search_form=search_form, page=page, filter_by=filter_by,
						   SubCategory=SubCategory, numpy=numpy, form=form, Currency=Currency, xaut=xaut, advanced_search_form=advanced_search_form,
						   item=item, vendor=vendor, shipping_from=shipping_from, shipping_to=shipping_to, currency=currency, 
						   price_from=price_from, price_to=price_to, rating_5=rating_5, rating_4=rating_4, rating_3=rating_3, rating_2=rating_2,
						   rating_1=rating_1, categories=get_category_info(),
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  






@listings.route("/category/search/<string:category>", methods=["POST", "GET"])
def category_search(category):

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# source: https://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters/
	posts = None  
	if category == "books":
		posts = Post.query.filter(or_(Post.sub_category == SubCategory.query.filter_by(value="e-books").first_or_404().id, 
									  Post.sub_category == SubCategory.query.filter_by(value="hardcopy").first_or_404().id))  
	elif category == "electronics":
		posts = Post.query.filter(or_(Post.sub_category == SubCategory.query.filter_by(value="cell-phones").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="computers").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="mining").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="stereos").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="video-games").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="electronics-other").first_or_404().id))  
	elif category == "art":
		posts = Post.query.filter(or_(Post.sub_category == SubCategory.query.filter_by(value="antiques").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="music").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="paintings").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="stamps").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="art-other").first_or_404().id))  

	elif category == "clothes":
		posts = Post.query.filter(or_(Post.sub_category == SubCategory.query.filter_by(value="men-clothing").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="men-shoes").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="men-accessories").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="women-clothing").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="women-shoes").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="women-accessories").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="kid-clothing").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="kid-shoes").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="kid-accessories").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="costumes").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="make-up").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="clothes-other").first_or_404().id))  

	elif category == "sports":
		posts = Post.query.filter(or_(Post.sub_category == SubCategory.query.filter_by(value="balls-equipment").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="camping").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="padding-gear").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="sports-other").first_or_404().id))  

	elif category == "toys":
		posts = Post.query.filter(or_(Post.sub_category == SubCategory.query.filter_by(value="action-figures").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="board-games").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="dolls").first_or_404().id, 
			                     	  Post.sub_category == SubCategory.query.filter_by(value="puzzles").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="outdoor-toys").first_or_404().id,
			                     	  Post.sub_category == SubCategory.query.filter_by(value="toys-other").first_or_404().id))  
	
	elif category == "other-other":
		posts = Post.query.filter(or_(Post.sub_category == SubCategory.query.filter_by(value="other-other").first_or_404().id))  



	else:
		posts = Post.query.filter_by(sub_category=SubCategory.query.filter_by(value=category).first_or_404().id)  




	filter_by = request.args.get("filter_by", "newest", type=str)  
	page = request.args.get("page", 1, type=int)  


	if filter_by == "newest":
		posts = posts.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)  
	if filter_by == "oldest":
		posts = posts.order_by(Post.date_posted.asc()).paginate(page=page, per_page=10)  
	if filter_by == "high":
		posts = posts.order_by(Post.price.desc()).paginate(page=page, per_page=10)  
	if filter_by == "low":
		posts = posts.order_by(Post.price.asc()).paginate(page=page, per_page=10)  
	if filter_by == "random":

		gallery = [ Post.gallery_1, Post.gallery_2, Post.gallery_3 ]  
		random_gallery = random.randrange(0, 3)  
		up = random.randrange(0, 2)  

		if up:
			posts = posts.order_by(gallery[random_gallery].asc()).paginate(page=page, per_page=10)  
		else:
			posts = posts.order_by(gallery[random_gallery].desc()).paginate(page=page, per_page=10)  


	link_back = "listings.search"  







	# Failed attempt at saving amount buying when adding to cart
	form = AddToCartForm()  

	if form.validate_on_submit() and (form.submit_cart.data or form.submit_buy.data or form.submit_saved.data):

		# If user is already logged in, redirect back to home page to not allow user to register again
		if not current_user.is_authenticated:
			flash("Login required", "alert-blue")  
			return redirect(url_for("users.login"))  

		buying = request.form.get("quantity-buying")  

		if not buying:
			buying = 1  

		elif int(buying) < 1:
			flash("Can't put 0 or negative amount of item in cart..", "alert-red")  
			return redirect(url_for('listings.search', text=text, filter_by=filter_by))  


		post_id = request.form.get("hidden_post_id")  

		if post_id:
			post_id = int(post_id)  

			is_already_in_cart = CartItem.query.filter_by(user_id=current_user.id, post_id=post_id).first()  

			if is_already_in_cart:
				is_already_in_cart.buying = is_already_in_cart.buying + int(buying)  


			else:
				current_date = datetime.utcnow()  
				cart = CartItem(post_id=post_id, buying=int(buying), user_id=current_user.id, date_saved=current_date, date_edited=current_date)  
				db.session.add(cart)  

			
			db.session.commit()  

		

			flash("Successfully added to cart", "alert-blue")  



	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  



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


	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  




	return render_template("listing/category_search.html", title="Search", link_back=link_back, posts=posts, datetime=datetime.utcnow(),
						   usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, search_form=search_form, page=page, filter_by=filter_by,
						   SubCategory=SubCategory, numpy=numpy, form=form, Currency=Currency, xaut=xaut, advanced_search_form=advanced_search_form,
						   category=category, categories=get_category_info(),
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  




























@listings.route("/listing/item/<int:post_id>", methods=["GET", "POST"])
def item(post_id):
	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	filter_by = request.args.get("filter_by", 'none' ,type=str)  
	previous_page = request.args.get("previous_page", "main.home", type=str)  
	username = request.args.get("username", "MoneroMarket", type=str)  

	post = Post.query.filter_by(id=post_id).first_or_404()  

	if post.vendor != current_user:
		post.views = post.views + 1  
		db.session.commit()  




	# Get reviews
	page = request.args.get("page", 1, type=int)  

	


	form = AddToCartForm()  

	# Add to cart
	if form.submit_cart.data and form.validate_on_submit():

		amount = request.form.get("item-amount")  
		if not amount:
			amount = 1  


		if not current_user.is_authenticated:
			flash("Please login to add to cart.", "alert-blue")  
			return redirect(url_for("users.login"))  

		is_already_in_cart = CartItem.query.filter_by(user_id=current_user.id, post_id=post_id).first()  

		if is_already_in_cart:
			is_already_in_cart.buying = is_already_in_cart.buying + int(amount)  
			is_already_in_cart.date_edited = datetime.utcnow()  


		else:
			current_date = datetime.utcnow()  
			cart = CartItem(post_id=post_id, buying=int(amount), user_id=current_user.id, date_saved=current_date, date_edited=current_date)  
			db.session.add(cart)  

		
		db.session.commit()  


		flash("Added to cart.", "alert-blue")  
		return redirect(url_for('listings.item', post_id=post_id, username=username, previous_page='listings.item', page=page))  


	# Buying
	elif form.submit_buy.data and form.validate_on_submit():
		flash("Buying screen.", "alert-green")  
		return redirect(url_for("main.home"))  



	# Save for Later
	elif form.submit_saved.data and form.validate_on_submit():

		amount = request.form.get("item-amount")  
		if not amount:
			amount = 1  


		if not current_user.is_authenticated:
			flash("Please login to save for later.", "alert-blue")  
			return redirect(url_for("users.login"))  

		is_already_in_saved = SavedForLaterItem.query.filter_by(user_id=current_user.id, post_id=post_id).first()  

		if is_already_in_saved:
			is_already_in_saved.buying = is_already_in_saved.buying + int(amount)  


		else:
			current_date = datetime.utcnow()  
			saved = SavedForLaterItem(post_id=post_id, buying=int(amount), user_id=current_user.id, date_saved=current_date)  
			db.session.add(saved)  

		
		db.session.commit()  


		flash("Saved for later.", "alert-blue")  
		return redirect(url_for('listings.item', post_id=post_id, username=username, previous_page=previous_page, page=page))  




	# Reviews
	total_reviews = Review.query.filter_by(post_id=post_id, to_buyer=None).order_by(Review.date_posted.desc())  
	reviews = total_reviews.paginate(page=page, per_page=10)  



	# Variable to keep track of review counting stuff
	# for the list, it's [ 'negative' 'nuetrual' 'positive' ]
	points = 0.0  
	one_month = [ 0, 0, 0 ]  
	six_months = [ 0, 0, 0 ]  
	twelve_months = [ 0, 0, 0 ]  
	all_time = [ 0, 0, 0 ]  
	

	for review in total_reviews:
		points += review.rating  

		# Neutral rating
		if review.rating > 2.4 and review.rating < 3.6:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				one_month[1] += 1  
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				six_months[1] += 1  
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				twelve_months[1] += 1  
			else:
				all_time[1] += 1  

		# Negative rating
		elif review.rating < 2.5:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				one_month[0] += 1  
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				six_months[0] += 1  
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				twelve_months[0] += 1  
			else:
				all_time[0] += 1  


		# Neutral rating
		elif review.rating > 3.5:
			if datetime.utcnow() < datetime.utcnow() + timedelta(days=31):
				one_month[2] += 1  
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=31*6):
				six_months[2] += 1  
			elif datetime.utcnow() < datetime.utcnow() + timedelta(days=365):
				twelve_months[2] += 1  
			else:
				all_time[2] += 1  



	# Get average star rating for entire post of all the reviews associated with post
	total_reviews_count = 0  

	if total_reviews:
		total_reviews_count = total_reviews.count()  


	if total_reviews_count == 0:
		points = 0.0  
	else:
		points /= total_reviews_count  










	points_vendor = 0.0  
	total_reviews_vendor = Review.query.filter_by(vendor_id=Post.query.filter_by(id=post_id).first().vendor.id).all()  
	for review in total_reviews_vendor:
		points_vendor += review.rating  


	total_reviews_vendor_count = 0  
	if total_reviews_vendor:
		total_reviews_vendor_count = len(total_reviews_vendor)  

		points_vendor /= total_reviews_vendor_count  
	



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
	if search_form.validate_on_submit and search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	advanced_search_form = AdvancedSearchForm()  
	if advanced_search_form.submit_advanced_search.data and advanced_search_form.validate_on_submit():
		title = request.form.get("title", "", type=str)  
		if not title:
			title = "{NULL}"  

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


		return redirect(url_for("listings.advanced_search", title=title, vendor=vendor, shipping_from=shipping_from, shipping_to=shipping_to, currency=currency,
								price_from=price_from, price_to=price_to, rating_5=rating_5, rating_4=rating_4, rating_3=rating_3, rating_2=rating_2,
								rating_1=rating_1))  


	return render_template("listing/item.html", title="View Listings", post=post, previous_page=previous_page, user=username, Currency=Currency,
						   form=form, datetime=datetime.utcnow(), Order=Order, numpy=numpy, search_form=search_form, filter_by=filter_by,
						   usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, page=page, reviews=reviews, User=User,
						   total_reviews_count=total_reviews_count, points=points,
						   one_month=one_month, six_months=six_months, twelve_months=twelve_months, all_time=all_time,
						   points_vendor=points_vendor, total_reviews_vendor_count=total_reviews_vendor_count, xaut=xaut,
						   advanced_search_form=advanced_search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  





@listings.route("/listings/create", methods=["GET", "POST"])
@login_required
def create():
	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	form = CreateListingForm()  

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


		# Source: https://stackoverflow.com/questions/53021662/multiplefilefield-wtforms
		# If there were any pictures submitted
		if form.pictures.data:
			accepted_extensions = { "jpg", "png", "jpeg", "pneg" }  

			if len(form.pictures.data) < 3:
				flash("3 files minimum are required.", "alert-red")  
				return redirect(url_for('listings.create'))  

			elif len(form.pictures.data) > 9:
				flash("9 files maximum are allowed.", "alert-red")  
				return redirect(url_for('listings.create'))  

			# Go through each picture to make sure they are the right format
			for picture in form.pictures.data:
				# Format for form.picture.data has nonsense filler in the last three characters
				if str(picture).lower()[-7:-3] in accepted_extensions or str(picture).lower()[-6:-3] in accepted_extensions:
					print("Accepted")  

				else:
					flash("Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
					return redirect(url_for('listings.create'))  


			# Save each photo now in the database
			for index in range(len(form.pictures.data)):
				saved_picture = save_picture_created_post(form.pictures.data[index])  

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






		# If no images were passed through the form
		else:
			flash("No pictures submitted or registered, please try again.", "alert-red")  
			return redirect(url_for('listings.create'))  

		

		sub_category = request.form.get("sub-category")  
		print(sub_category)  
		sub_category_query = SubCategory.query.filter_by(value=sub_category).first()  


		shipping_from = request.form.get("shipping_from")  
		shipping_to = request.form.get("shipping_to")  




		fixed_to_fiat = None  
		currency = request.form.get("currency").upper()  

		# Will always be true as of now, but in the future will allow for static Monero prices.
		# Commented out original and replaced with "if True:"
		# Just uncomment and delete "if True:" whenever ready to allow for static Monero prices, as everything is already all set up.

		# if request.form.get("fiat") == "Fiat":
		if True:
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
				form.price.data = float(form.price.data) * float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "USDT":
				form.price.data = float(form.price.data) * (float(Currency.query.filter_by(country="USDT").first().price) / float(Currency.query.filter_by(country=currency).first().price))  


			# Never less than $1 USD
			if float(form.price.data) < float(1.00):
				form.price.data = float(1.00)  


		# Convert to Monero to keep it static.
		elif fixed_to_fiat == False:
			if currency == "USDT":
				form.price.data = float(form.price.data) / float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "XMR":
				form.price.data = float(form.price.data) * float(Currency.query.filter_by(country=currency).first().price) / float(Currency.query.filter_by(country="USDT").first().price)  


			# Never less than $1 USD
			if float(form.price.data) < float(1) / float(Currency.query.filter_by(country="USDT").first().price):
				form.price.data = float(1) / float(Currency.query.filter_by(country="USDT").first().price)  




		# highest int: 9223372036854775807
		random_num = random.randint(1, 9999999999999999)  
		while Post.query.filter_by(id=random_num).first():
			random_num = random.randint(1, 9999999999999999)  


		# Create an table instance and assign it values from the form
		post = Post(id=random_num, title=form.title.data, price=form.price.data, supply=form.supply.data, 
					description=form.description.data, refund_policy=form.refund_policy.data,
					gallery_1=gallery_1, gallery_2=gallery_2, gallery_3=gallery_3, gallery_4=gallery_4,
					gallery_5=gallery_5, gallery_6=gallery_6, gallery_7=gallery_7, gallery_8=gallery_8,
					gallery_9=gallery_9, vendor=current_user,
					fixed_to_fiat=fixed_to_fiat, shipping_from=str(shipping_from), shipping_to=str(shipping_to),
					sub_category=sub_category_query.id)  

		
					

		# Add and save to the database 
		db.session.add(post)  
		db.session.commit()  

		flash("Listing created successfully!", "alert-green")
		return redirect(url_for("listings.created", post_id=post.id))  





	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("listing/create.html", title="Create Listing", form=form,  datetime=datetime.utcnow(),
						   search_form=search_form, 
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  






@listings.route("/listings/created/<int:post_id>", methods=["GET", "POST"])
@login_required
def created(post_id):
	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("listing/created.html", title="Created Listing", post_id=post_id,  datetime=datetime.utcnow(),
						   search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  




@listings.route("/listings/view/<string:username>/<string:filter_by>", methods=["GET", "POST"])
def view(username, filter_by):
	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	page = request.args.get("page", 1, type=int)  

	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  



	# Failed attempt at saving amount buying when adding to cart
	form = AddToCartForm()  

	if form.validate_on_submit():
		# If user is already logged in, redirect back to home page to not allow user to register again
		if not current_user.is_authenticated:
			flash("Login required", "alert-blue")  
			return redirect(url_for("users.login"))  
		
		buying = request.form.get("quantity-buying")  

		if not buying:
			buying = 1  

		elif int(buying) < 1:
			flash("Can't put 0 or negative amount of item in cart..", "alert-red")  
			return redirect(url_for('listings.view', username=username))  


		post_id = int(request.form.get("hidden_post_id"))  

		is_already_in_cart = CartItem.query.filter_by(user_id=current_user.id, post_id=post_id).first()  

		if is_already_in_cart:
			is_already_in_cart.buying = is_already_in_cart.buying + int(buying)  


		else:
			date_current = datetime.utcnow()  
			cart = CartItem(post_id=post_id, buying=int(buying), user_id=current_user.id, date_saved=date_current, date_edited=date_current)  
			db.session.add(cart)  

		
		db.session.commit()  

	

		flash("Successfully added to cart", "alert-blue")  





	

	user = User.query.filter_by(username=username).first()  

	posts = None  
	if filter_by == "newest":
		posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "oldest":
		posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.asc()).paginate(page=page, per_page=10)  
	elif filter_by == "high":
		posts = Post.query.filter_by(user_id=user.id).order_by(Post.price.desc()).paginate(page=page, per_page=10)  
	elif filter_by == "low":
		posts = Post.query.filter_by(user_id=user.id).order_by(Post.price.asc()).paginate(page=page, per_page=10)  
	elif filter_by == "random":

		gallery = [ Post.gallery_1, Post.gallery_2, Post.gallery_3 ]  
		random_gallery = random.randrange(0, 3)  
		up = random.randrange(0, 2)  

		if up:
			posts = Post.query.filter_by(user_id=user.id).order_by(gallery[random_gallery].asc()).paginate(page=page, per_page=10)  
		else:
			posts = Post.query.filter_by(user_id=user.id).order_by(gallery[random_gallery].desc()).paginate(page=page, per_page=10)  


	link_back = "listings.view"  





	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  




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


	return render_template("listing/view.html", title="Edit Listing", posts=posts, link_back=link_back, username=username, page=page,
						   SubCategory=SubCategory, datetime=datetime.utcnow(), filter_by=filter_by, Currency=Currency,
						   usdt=usdt, btc=btc, eth=eth, ltc=ltc, bch=bch, doge=doge, numpy=numpy, search_form=search_form, form=form,
						   xaut=xaut,
						   advanced_search_form=advanced_search_form, categories=get_category_info(),
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  




@listings.route("/listings/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
	# Check to make sure it's the right user who can update the post
	post = Post.query.get_or_404(post_id)  
	if post.vendor != current_user:
		abort(403)  

	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  


	form = EditListingForm()  

	if form.validate_on_submit():
		
		# Save picture variables for end to save into database
		gallery = [None] * 9  
		existed = [None] * 9  


		# Source: https://stackoverflow.com/questions/53021662/multiplefilefield-wtforms
		# If there were any pictures submitted
		accepted_extensions = { "jpg", "png", "jpeg", "pneg" }  


		if form.picture_1.data.filename:
			if str(form.picture_1.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_1.data.filename).lower()[-3:] in accepted_extensions :
				gallery[0] = form.picture_1.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_1.data.filename:
			if post.gallery_1:
				existed[0] = post.gallery_1  




		if form.picture_2.data.filename:
			if str(form.picture_2.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_2.data.filename).lower()[-3:] in accepted_extensions :
				gallery[1] = form.picture_2.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_2.data.filename:
			if post.gallery_2:
				existed[1] = post.gallery_2  


		if form.picture_3.data.filename:
			if str(form.picture_3.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_3.data.filename).lower()[-3:] in accepted_extensions :
				gallery[2] = form.picture_3.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_3.data.filename:
			if post.gallery_3:
				existed[2] = post.gallery_3  



		if form.picture_4.data.filename:
			if str(form.picture_4.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_4.data.filename).lower()[-3:] in accepted_extensions :
				gallery[3] = form.picture_4.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_4.data.filename:
			if post.gallery_4:
				existed[3] = post.gallery_4  



		if form.picture_5.data.filename:
			if str(form.picture_5.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_5.data.filename).lower()[-3:] in accepted_extensions :
				gallery[4] = form.picture_5.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_5.data.filename:
			if post.gallery_5:
				existed[4] = post.gallery_5  



		if form.picture_6.data.filename:
			if str(form.picture_6.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_6.data.filename).lower()[-3:] in accepted_extensions :
				gallery[5] = form.picture_6.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_6.data.filename:
			if post.gallery_6:
				existed[5] = post.gallery_6  





		if form.picture_7.data.filename:
			if str(form.picture_7.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_7.data.filename).lower()[-3:] in accepted_extensions :
				gallery[6] = form.picture_7.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_7.data.filename:
			if post.gallery_7:
				existed[6] = post.gallery_7  





		if form.picture_8.data.filename:
			if str(form.picture_8.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_8.data.filename).lower()[-3:] in accepted_extensions :
				gallery[7] = form.picture_8.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_8.data.filename:
			if post.gallery_8:
				existed[7] = post.gallery_8  






		if form.picture_9.data.filename:
			if str(form.picture_9.data.filename).lower()[-4:] in accepted_extensions or str(form.picture_9.data.filename).lower()[-3:] in accepted_extensions :
				gallery[8] = form.picture_9.data  
				

			else:
				flash(f"Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red")  
				return redirect(url_for('listings.edit', post_id=post_id))  
		elif not form.picture_9.data.filename:
			if post.gallery_9:
				existed[8] = post.gallery_9  







		if len(gallery) < 3:
			flash("3 files minimum are required.", "alert-red")  
			return redirect(url_for('listings.edit', post_id=post_id))  

		elif len(gallery) > 9:
			flash("9 files maximum are allowed.", "alert-red")  
			return redirect(url_for('listings.edit', post_id=post_id))  

	


		# Fill in everything else with blank null spaces
		while len(gallery) < 9:
			gallery.append("")  



		# Save each photo now in the database
		for index in range(len(gallery)):
			if not gallery[index]:
				continue  

			saved_picture = save_picture_edit_post(gallery[index], [index], post_id)  

			if index == 0:
				if post.gallery_1:
					delete_post_picture_path(post.gallery_1)  

				post.gallery_1 = saved_picture  

			elif index == 1:
				if post.gallery_2:
					delete_post_picture_path(post.gallery_2)  

				post.gallery_2 = saved_picture  

			elif index == 2:
				if post.gallery_3:
					delete_post_picture_path(post.gallery_3)  

				post.gallery_3 = saved_picture  

			elif index == 3:
				if post.gallery_4:
					delete_post_picture_path(post.gallery_4)  

				post.gallery_4 = saved_picture  

			elif index == 4:
				if post.gallery_5:
					delete_post_picture_path(post.gallery_5)  

				post.gallery_5 = saved_picture  

			elif index == 5:
				if post.gallery_6:
					delete_post_picture_path(post.gallery_6)  

				post.gallery_6 = saved_picture  

			elif index == 6:
				if post.gallery_7:
					delete_post_picture_path(post.gallery_7)  

				post.gallery_7 = saved_picture  

			elif index == 7:
				if post.gallery_8:
					delete_post_picture_path(post.gallery_8)  

				post.gallery_8 = saved_picture  

			elif index == 8:
				if post.gallery_9:
					delete_post_picture_path(post.gallery_9)  

				post.gallery_9 = saved_picture  



		

		# Remove via checkboxes

		if request.form.get("remove-gallery_1"):
			delete_post_picture_path(post.gallery_1)  
			post.gallery_1 = ""  

		if request.form.get("remove-gallery_2"):
			delete_post_picture_path(post.gallery_2)  
			post.gallery_2 = ""  

		if request.form.get("remove-gallery_3"):
			delete_post_picture_path(post.gallery_3)  
			post.gallery_3 = ""  

		if request.form.get("remove-gallery_4"):
			delete_post_picture_path(post.gallery_4)  
			post.gallery_4 = ""  

		if request.form.get("remove-gallery_5"):
			delete_post_picture_path(post.gallery_5)  
			post.gallery_5 = ""  

		if request.form.get("remove-gallery_6"):
			delete_post_picture_path(post.gallery_6)  
			post.gallery_6 = ""  

		if request.form.get("remove-gallery_7"):
			delete_post_picture_path(post.gallery_7)  
			post.gallery_7 = ""  

		if request.form.get("remove-gallery_8"):
			delete_post_picture_path(post.gallery_8)  
			post.gallery_8 = ""  

		if request.form.get("remove-gallery_9"):
			delete_post_picture_path(post.gallery_9)  
			post.gallery_9 = ""  






		# <------- Order the list ---------->
		unordered_list = []  

		unordered_list.append(post.gallery_1)  
		unordered_list.append(post.gallery_2)  
		unordered_list.append(post.gallery_3)  
		unordered_list.append(post.gallery_4)  
		unordered_list.append(post.gallery_5)  
		unordered_list.append(post.gallery_6)  
		unordered_list.append(post.gallery_7)  
		unordered_list.append(post.gallery_8)  
		unordered_list.append(post.gallery_9)  



		ordered_list = [index for index in unordered_list if index != ""]  

		while len(ordered_list) < 9:
			ordered_list.append("")  


		post.gallery_1 = ordered_list[0]  
		post.gallery_2 = ordered_list[1]  
		post.gallery_3 = ordered_list[2]  
		post.gallery_4 = ordered_list[3]  
		post.gallery_5 = ordered_list[4]  
		post.gallery_6 = ordered_list[5]  
		post.gallery_7 = ordered_list[6]  
		post.gallery_8 = ordered_list[7]  
		post.gallery_9 = ordered_list[8]  









		sub_category = request.form.get("sub-category")  
		print(sub_category)  
		sub_category_query = SubCategory.query.filter_by(value=sub_category).first()  


		shipping_from = request.form.get("shipping_from")  
		shipping_to = request.form.get("shipping_to")  
		
		





		# Get price
		fixed_to_fiat = None  
		currency = request.form.get("currency").upper()  

		# Will always be true as of now, but in the future will allow for static Monero prices.
		# Commented out original and replaced with "if True:"
		# Just uncomment and delete "if True:" whenever ready to allow for static Monero prices, as everything is already all set up.

		# if request.form.get("fiat") == "Fiat":
		if True:
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
				form.price.data = float(form.price.data) * float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "USDT":
				form.price.data = float(form.price.data) * (float(Currency.query.filter_by(country="USDT").first().price) / float(Currency.query.filter_by(country=currency).first().price))  


			# Never less than $1 USD
			if float(form.price.data) < float(1.00):
				form.price.data = float(1.00)  


		# Convert to Monero to keep it static.
		elif fixed_to_fiat == False:
			if currency == "USDT":
				form.price.data = float(form.price.data) / float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "XMR":
				form.price.data = float(form.price.data) * float(Currency.query.filter_by(country=currency).first().price) / float(Currency.query.filter_by(country="USDT").first().price)  


			# Never less than $1 USD
			if float(form.price.data) < float(1) / float(Currency.query.filter_by(country="USDT").first().price):
				form.price.data = float(1) / float(Currency.query.filter_by(country="USDT").first().price)  





		# Update post
		post.title = form.title.data  
		post.price = form.price.data  
		post.supply = form.supply.data  
		post.description = form.description.data  
		post.refund_policy = form.refund_policy.data  
		post.shipping_to = str(shipping_to)  
		post.shipping_from = str(shipping_from)  
		post.sub_category = sub_category_query.id  
		post.fixed_to_fiat = fixed_to_fiat  
					

		db.session.commit()  

		flash(f"Listing updated successfully!", "alert-green")
		return redirect(url_for("listings.item", post_id=post_id, previous_page="listings.search", username=current_user.username))  






	elif request.method == "GET":
		form.title.data = post.title  

		if post.fixed_to_fiat == True:
			form.price.data = post.price / Currency.query.filter_by(country="USDT").first().price  
		elif post.fixed_to_fiat == False:
			form.price.data = post.price  

		form.supply.data = post.supply  
		form.description.data = post.description  
		form.refund_policy.data = post.refund_policy  

		form.picture_1.data = post.gallery_1  
		form.picture_2.data = post.gallery_2  
		form.picture_3.data = post.gallery_3  
		form.picture_4.data = post.gallery_4  
		form.picture_5.data = post.gallery_5  
		form.picture_6.data = post.gallery_6  
		form.picture_7.data = post.gallery_7  
		form.picture_8.data = post.gallery_8  
		form.picture_9.data = post.gallery_9  




	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  


	return render_template("listing/edit.html", title="Create Listing", form=form, post=post, datetime=datetime.utcnow(),
						   search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  






@listings.route("/listings/delete/<int:post_id>", methods=["GET", "POST"])
@login_required
def delete(post_id):
	post = Post.query.filter_by(id=post_id).first()  
	username = post.vendor.username  


	# Permanently delete images from database
	if post.gallery_1:
		delete_post_picture_path(post.gallery_1)  
		post.gallery_1 = ""  

	if post.gallery_2:
		delete_post_picture_path(post.gallery_2)  
		post.gallery_2 = ""  

	if post.gallery_3:
		delete_post_picture_path(post.gallery_3)  
		post.gallery_3 = ""  

	if post.gallery_4:
		delete_post_picture_path(post.gallery_4)  
		post.gallery_4 = ""  

	if post.gallery_5:
		delete_post_picture_path(post.gallery_5)  
		post.gallery_5 = ""  

	if post.gallery_6:
		delete_post_picture_path(post.gallery_6)  
		post.gallery_6 = ""  

	if post.gallery_7:
		delete_post_picture_path(post.gallery_7)  
		post.gallery_7 = ""  

	if post.gallery_8:
		delete_post_picture_path(post.gallery_8)  
		post.gallery_8 = ""  

	if post.gallery_9:
		delete_post_picture_path(post.gallery_9)  
		post.gallery_9 = ""  



	db.session.delete(post)  
	db.session.commit()  


	flash("Listing deleted.", "alert-blue")  
	return redirect(url_for('listings.view', username=username, filter_by="newest"))  





















