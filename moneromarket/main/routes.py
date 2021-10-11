from flask import Blueprint, render_template, url_for, redirect, request  
from flask_login import current_user  

from datetime import datetime  

from moneromarket import db  
from moneromarket.database.models import Currency, Category, SubCategory, Post, User, Dispute, Review  


from moneromarket.main.forms import SearchForm, AdvancedSearchForm  
from moneromarket.main.utils import get_category_info  

import numpy  



main = Blueprint("main", __name__)  



@main.route("/", methods=["GET", "POST"])
@main.route("/home", methods=["GET", "POST"])
def home():

	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  


	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  





	# Source: https://develie.hashnode.dev/exploring-flask-sqlalchemy-queries
	newest_posts = Post.query.order_by(Post.date_posted.desc()).limit(6).all()  

	
	









	search_form = SearchForm()  
	if search_form.submit_search.data and search_form.validate_on_submit():

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

		



	return render_template("home.html", title="Home", current_page="home", datetime=datetime.utcnow(),
						   usdt=usdt, btc=btc, eth=eth, bch=bch, ltc=ltc, doge=doge, search_form=search_form,
						   xaut=xaut, advanced_search_form=advanced_search_form, numpy=numpy, Currency=Currency,
						   categories=get_category_info(), statistic_users=statistic_users, statistic_listings=statistic_listings, 
						   statistic_disputes=statistic_disputes, newest_posts=newest_posts, User=User, SubCategory=SubCategory, Review=Review)  



@main.route("/pgp")
def pgp():
	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("questions/pgp.html", title="PGP", current_page="pgp", datetime=datetime.utcnow(), search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  



@main.route("/faq")
def faq():
	statistic_users = len(User.query.all())  
	statistic_listings = len(Post.query.all())  
	statistic_disputes = len(Dispute.query.all())  

	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  

	return render_template("questions/faq.html", title="FAQ", current_page="faq", datetime=datetime.utcnow(), search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes)  


































