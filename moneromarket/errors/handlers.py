from flask import Blueprint, render_template ;
from datetime import datetime ;
from moneromarket.main.forms import SearchForm ;

from moneromarket.database.models import Post, User, Dispute ;

errors = Blueprint("errors", __name__) ;




# Page that doesn't exist
@errors.app_errorhandler(404)
def error_404(error):
	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("error/404.html", datetime=datetime.utcnow(), search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes), 404 ;


# Page that user doesn't have access too
@errors.app_errorhandler(403)
def error_403(error):
	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("error/403.html", datetime=datetime.utcnow(), search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes), 403 ;


# Page that appears when the server goes down.
@errors.app_errorhandler(500)
def error_500(error):
	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("error/500.html", datetime=datetime.utcnow(), search_form=search_form,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes), 500 ;








































	