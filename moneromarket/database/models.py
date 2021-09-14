from moneromarket import db, login_manager ;

from flask_sqlalchemy import SQLAlchemy ;
from datetime import datetime ;




# Manage login session
from flask_login import UserMixin ;

# Login by username
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id)) ;




class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key =True) ;
	username = db.Column(db.String(16), unique =True, nullable =False) ;


	is_admin = db.Column(db.Boolean, nullable =False, default =False) ;
	is_employee = db.Column(db.Boolean, nullable =False, default =False) ;


	# Email is optional, and will be unique if there is a value.
	# Unique constraint will have to be implemented via Python, as SQLite doesn't allow for multiple NULLS when unique =True ):
	email = db.Column(db.String(99), nullable =True) ;
	profile_picture = db.Column(db.String(20), nullable =False, default="default.jpg") ;
	password = db.Column(db.String(300), nullable =False) ;	# change to size 128




	# Text fields in the profile section
	description   = db.Column(db.Text, nullable =True) ;
	refund_policy = db.Column(db.Text, nullable =True) ;


	date_created = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;
	last_login   = db.Column(db.DateTime, nullable =True) ;
	last_seen    = db.Column(db.DateTime, nullable =True) ;




	# To refer to the user's Monero wallet account, encrypted, and qr code, encrypted as well!
	account_number = db.Column(db.String(300), nullable =False) ;
	public_address = db.Column(db.String(300), nullable =False) ;
	qr_code = db.Column(db.String(20), nullable =False) ;



	warnings = db.Column(db.String(50), nullable =True) ;
	muted = db.Column(db.DateTime, nullable =True) ;
	suspended = db.Column(db.DateTime, nullable =True) ;
	to_be_deleted = db.Column(db.DateTime, nullable =True) ;


	buys = db.Column(db.Integer, nullable =False, default =0) ;
	sales = db.Column(db.Integer, nullable =False, default =0) ;

	disputes_won = db.Column(db.Integer, nullable =False, default =0) ;
	disputes_lost = db.Column(db.Integer, nullable =False, default =0) ;
	disputes_neutral = db.Column(db.Integer, nullable =False, default =0) ;
	no_response = db.Column(db.Integer, nullable =False, default =0) ;

	currently_buying = db.Column(db.Integer, nullable =False, default =0) ;
	currently_selling = db.Column(db.Integer, nullable =False, default =0) ;



	# Containing multiple posts
	posts = db.relationship("Post", backref="vendor", lazy =True) ;
	cart = db.relationship("CartItem", backref="cart_vendor", lazy=True) ;
	saved_for_later = db.relationship("SavedForLaterItem", backref="saved_for_later_vendor", lazy=True) ;

	orders = db.relationship("Order", backref="orders_vendor", lazy=True) ;

	favorite_users = db.relationship("FavoriteUser", backref="users_favorite", lazy=True) ;
	favorite_posts = db.relationship("FavoriteItem", backref="posts_favorite", lazy=True) ;





	# Containing multiple ratings
	sent_reviews = db.relationship("Review", backref="user_review", lazy =True) ;
	received_reviews = db.relationship("Review", backref="foreigner_review", lazy =True) ;




	def __repr__(self):
		return f"User('{ self.id }', '{ self.username }', '{ self.email }', '{ self.password }', '{ self.profile_picture }')" ;




class UserFee(db.Model):
	__tablename__ = "user_fee" ;
	id = db.Column(db.Integer, primary_key =True) ;

	user_id = db.Column(db.Integer, nullable =False) ;
	vendor_id = db.Column(db.Integer, nullable =False) ;
	order_id = db.Column(db.Integer, nullable =True) ;


	total_amount_owed_5_percent = db.Column(db.String(100), nullable =True) ;
	total_amount_owed_10_percent_plus_shipping = db.Column(db.String(100), nullable =True) ;
	total_amount_paid_off = db.Column(db.String(100), nullable =True) ;

	date_reserved = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;
	date_paid_off = db.Column(db.DateTime, nullable =True) ;



class Post(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;
	title = db.Column(db.String(50), nullable =False) ;
	description = db.Column(db.Text, nullable =False) ;
	date_posted = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;
	date_edited = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;

	refund_policy = db.Column(db.Text, nullable =True) ;

	price = db.Column(db.Float(precision =8), nullable =False) ;
	fixed_to_fiat = db.Column(db.Boolean, nullable =False, default =True) ;

	# Update to be like the bottom one, and default =0
	supply = db.Column(db.Integer, nullable =False, default =0) ;
	pending = db.Column(db.Integer, nullable =False, default =0) ;
	#last_change_available_amount = db.Column(db.DateTime, default =datetime.utcnow) ;

	disputes_won = db.Column(db.Integer, nullable =False, default =0) ;
	disputes_lost = db.Column(db.Integer, nullable =False, default =0) ;
	disputes_neutral = db.Column(db.Integer, nullable =False, default =0) ;


	# sub_categories = db.relationship("SubCategory", backref=db.backref("sub_category", uselist=False)) ;
	
	shipping_from = db.Column(db.String(50), nullable =False) ;
	shipping_to = db.Column(db.String(50), nullable =False) ;




	# Post pictures, at lease 3 are REQUIRED
	gallery_1 = db.Column(db.String(20), nullable =False) ;
	gallery_2 = db.Column(db.String(20), nullable =False) ;
	gallery_3 = db.Column(db.String(20), nullable =False) ;
	gallery_4 = db.Column(db.String(20), nullable =True) ;
	gallery_5 = db.Column(db.String(20), nullable =True) ;
	gallery_6 = db.Column(db.String(20), nullable =True) ;
	gallery_7 = db.Column(db.String(20), nullable =True) ;
	gallery_8 = db.Column(db.String(20), nullable =True) ;
	gallery_9 = db.Column(db.String(20), nullable =True) ;



	views = db.Column(db.Integer, nullable =False, default =0) ;
	sales = db.Column(db.Integer, nullable =False, default =0) ;


	# Links back to the original user who posted the item
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable =False) ;

	# Containing multiple ratings
	reviews = db.relationship("Review", backref="post_review", lazy=True) ;

	sub_category = db.Column(db.Integer, db.ForeignKey("sub_category.id"), nullable =False) ;


	cart = db.relationship("CartItem", backref=db.backref("cart_post", uselist=False)) ;
	orders = db.relationship("Order", backref=db.backref("orders_post", uselist=False)) ;
	saved_for_later = db.relationship("SavedForLaterItem", backref=db.backref("saved_for_later_post", uselist=False)) ;

	favorite = db.relationship("FavoriteItem", backref=db.backref("favorite_post", uselist=False)) ;




	def __repr__(self):
		return f"User('{ self.id }', '{ self.title }', '{ self.date_posted }', '{ self.user_id }')" ;





class Review(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;
	rating = db.Column(db.Float(precision =1), nullable =False) ;
	title = db.Column(db.String(50), nullable =False) ;
	description = db.Column(db.Text, nullable =False) ;

	date_posted = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;


	# Picture or video reviews
	gallery_1 = db.Column(db.String(20), nullable =True) ;
	gallery_2 = db.Column(db.String(20), nullable =True) ;
	gallery_3 = db.Column(db.String(20), nullable =True) ;


	# Links back to the original user who posted the review
	# Nullable is set to true so that way reviews can be anonymous if the user wants to remain anounymous.
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable =True) ;
	vendor_id = db.Column(db.Integer, nullable =True) ;
	to_buyer = db.Column(db.Integer, nullable =True) ;

	# Links back to the original post
	post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable =False) ;
	order_id = db.Column(db.Integer, nullable =True) ;


	# To dispute a false review
	dispute_date = db.Column(db.DateTime, nullable =True) ;
	dispute_text = db.Column(db.Text, nullable =True) ; # Encrypted

	dispute_resolved = db.Column(db.DateTime, nullable =True) ;





# Source: https://social.msdn.microsoft.com/forums/sqlserver/en-US/8f7d83ec-6669-47b9-a4f3-34b0d5716833/database-with-categoriessubcategories
# Source: https://dba.stackexchange.com/questions/81311/why-would-a-table-use-its-primary-key-as-a-foreign-key-to-itself
class Category(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;
	name = db.Column(db.String(30), nullable =False) ;

	# Tree ladder if category is a sub-category to another category
	previous_category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable =True) ;
	sub_categories = db.relationship("SubCategory", backref="sub_category", lazy=True) ;
	value = db.Column(db.String(30), nullable =False) ;
	

class SubCategory(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;
	name = db.Column(db.String(30), nullable =False) ;

	# Identifer for select option html tags
	value = db.Column(db.String(30), nullable =False) ;


	category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable =True) ;
	# post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable =False) ;
	

	def __repr__(self):
		return f"{ self.name }" ;



'''
# Many-to-many relationship
# Source: https://overiq.com/flask-101/database-modelling-in-flask/


class Country(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;
	name = db.Column(db.String(50), nullable =False) ;

	# Digital and Worldwide will also be added as countries in the table
	exchange_rate = db.Column(db.Integer, db.ForeignKey("exchange_rates.id"), nullable =False) ;

	posts = db.relationship("Post", secondary="posts_countries", backref="listing_country", lazy=True) ;






class ExchangeRates(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;
	

	countries = db.relationship("Country", backref="country", lazy=True) ;

	amount = db.Column(db.Float(precision =12), nullable =False) ;

'''

class PendingOrderScreen(db.Model):
	__tablename__ = "pending_order_screen" ;

	id = db.Column(db.Integer, primary_key=True) ;

	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable =False) ;
	date_reserved = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;

	# To refer to the order's Monero wallet account, encrypted!
	account_number = db.Column(db.String(300), nullable =False) ;
	public_address = db.Column(db.String(300), nullable =False) ;
	payment_total = db.Column(db.String(50), nullable =False) ;
	qr_code = db.Column(db.String(20), nullable =False) ;

	# [0] = cart_item.id, [1] = price, [2] = buying, [3] = post_id; IN STRING FORMAT!
	list_of_list_of_items = db.Column(db.Text, nullable =False) ;
	payment_id = db.Column(db.String(16), nullable=True) ;

	# Use this to check and see if user's cart was edited
	latest_time = db.Column(db.DateTime, nullable =False) ;


class Order(db.Model):
	__tablename__ = "order_table" ;

	id = db.Column(db.Integer, primary_key=True) ;

	post_id = db.Column(db.Integer, db.ForeignKey("post.id")) ;

	date_ordered = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;
	waiting_for_vendor = db.Column(db.DateTime, nullable =True) ;
	vendor_accepted = db.Column(db.DateTime, nullable =True) ;
	vendor_declined = db.Column(db.DateTime, nullable =True) ;
	vendor_shipped = db.Column(db.DateTime, nullable =True) ;
	arrived_to_office = db.Column(db.DateTime, nullable =True) ;
	shipped_from_office = db.Column(db.DateTime, nullable =True) ;
	buyer_received = db.Column(db.DateTime, nullable =True) ;
	escrow_released = db.Column(db.DateTime, nullable =True) ;
	pending_releasing = db.Column(db.DateTime, nullable =True) ;
	buyer_disputed = db.Column(db.DateTime, nullable =True) ;
	vendor_disputed = db.Column(db.DateTime, nullable =True) ;
	request_buyer_return = db.Column(db.DateTime, nullable =True) ;

	buyer_shipped = db.Column(db.DateTime, nullable =True) ;
	vendor_received = db.Column(db.DateTime, nullable =True) ;

	order_cancelled = db.Column(db.DateTime, nullable =True) ;
	order_refunded = db.Column(db.DateTime, nullable =True) ;
	excess_received = db.Column(db.DateTime, nullable =True) ;
	excess_received_refunded = db.Column(db.DateTime, nullable =True) ;
	order_normal = db.Column(db.DateTime, nullable =True) ;

	recent_update = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;
	auto_finalization_timer = db.Column(db.DateTime, nullable =True) ;



	buying_amount = db.Column(db.String(100), nullable =False) ;
	price_per_item = db.Column(db.String(100), nullable =False) ;
	total_amount_for_payment_id = db.Column(db.String(100), nullable =False) ;


	total_amount_received = db.Column(db.String(100), nullable =True) ;
	total_amount_of_orders_for_payment_id = db.Column(db.String(100), nullable =False) ;

	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable =False) ;
	vendor_id = db.Column(db.Integer, nullable =False) ;


	payment_id = db.Column(db.String(16), nullable=True) ;
	public_address = db.Column(db.String(300), nullable =False) ;
	return_address = db.Column(db.String(300), nullable =True) ;
	vendor_address = db.Column(db.String(300), nullable =True) ;
	account_number = db.Column(db.String(300), nullable =False) ;
	transaction_id = db.Column(db.String(300), nullable =True) ;
	amount_refunded = db.Column(db.String(300), nullable =True) ;

	name_and_address = db.Column(db.Text, nullable =False) ;


	status = db.Column(db.String(32), nullable =True) ;
	tracking_number = db.Column(db.String(300), nullable =True) ; # Change to 300!!
	shipping_to_tracking_number = db.Column(db.String(300), nullable =True) ; # Change to 300!!
	description = db.Column(db.Text, nullable =True) ; # Will be encrypted...
	description_vendor = db.Column(db.Text, nullable =True) ; # Will be encrypted...
	description_buyer = db.Column(db.Text, nullable =True) ; # Will be encrypted...
	description_dispute = db.Column(db.Text, nullable =True) ; # Will be encrypted...
	description_digital = db.Column(db.Text, nullable =True) ; # Will be encrypted...

	confirmations = db.Column(db.Integer, nullable =False, default =0) ;

	# Next update, encrypt this dawg.
	cost_for_shipping_to_buyer = db.Column(db.String(50), nullable =True) ;
	cost_for_shipping_to_vendor = db.Column(db.String(50), nullable =True) ;
	cost_for_shipping_from_buyer = db.Column(db.String(50), nullable =True) ;


	# Only used to differentiate whether or not to refund to buyer or seller, and also to split between two if neutral dispute.
	percentage_to_buyer = db.Column(db.String(300), nullable =True) ;
	percentage_to_vendor = db.Column(db.String(300), nullable =True) ;




	# To know whether buyer or vendor submitted a review
	buyer_reviewed = db.Column(db.Boolean, nullable =True, default =False) ;
	vendor_reviewed = db.Column(db.Boolean, nullable =True, default =False) ;

	buyer_deleted = db.Column(db.Boolean, nullable =True, default =False) ;
	vendor_deleted = db.Column(db.Boolean, nullable =True, default =False) ;



	# Links back to the original user who posted the item
	order_pictures_id = db.Column(db.Integer, db.ForeignKey("order_pictures.id"), nullable =True) ;
	order_post_details = db.Column(db.Integer, db.ForeignKey("order_post_details.id"), nullable =True) ;


	# Change to True
	qr_code = db.Column(db.String(80), nullable =False) ;
	


class OrderPictures(db.Model):
	__tablename__ = "order_pictures" ;

	id = db.Column(db.Integer, primary_key =True) ;
	orders = db.relationship("Order", backref="order_pictures", lazy =True) ;

	receipt_picture = db.Column(db.String(20), nullable =False) ;
	date_arrival = db.Column(db.DateTime, nullable =False) ;	# Change to date_arrival, a DateTime Object
	notes_about_item = db.Column(db.Text, nullable =False) ;

	gallery_1 = db.Column(db.String(20), nullable =False) ;
	gallery_2 = db.Column(db.String(20), nullable =False) ;
	gallery_3 = db.Column(db.String(20), nullable =False) ;
	gallery_4 = db.Column(db.String(20), nullable =False) ;
	gallery_5 = db.Column(db.String(20), nullable =False) ;
	gallery_6 = db.Column(db.String(20), nullable =False) ;
	gallery_7 = db.Column(db.String(20), nullable =True) ;
	gallery_8 = db.Column(db.String(20), nullable =True) ;
	gallery_9 = db.Column(db.String(20), nullable =True) ;
	gallery_10 = db.Column(db.String(20), nullable =True) ;
	gallery_11 = db.Column(db.String(20), nullable =True) ;
	gallery_12 = db.Column(db.String(20), nullable =True) ;
	gallery_13 = db.Column(db.String(20), nullable =True) ;
	gallery_14 = db.Column(db.String(20), nullable =True) ;
	gallery_15 = db.Column(db.String(20), nullable =True) ;
	gallery_16 = db.Column(db.String(20), nullable =True) ;
	gallery_17 = db.Column(db.String(20), nullable =True) ;
	gallery_18 = db.Column(db.String(20), nullable =True) ;
	gallery_19 = db.Column(db.String(20), nullable =True) ;
	gallery_20 = db.Column(db.String(20), nullable =True) ;
	gallery_21 = db.Column(db.String(20), nullable =True) ;



# Static post details to compare to just in case vendor updates post to try and scam users.....
class OrderPostDetails(db.Model):
	__tablename__ = "order_post_details" ;

	id = db.Column(db.Integer, primary_key =True) ;

	shipping_from = db.Column(db.String(300), nullable =True) ;
	shipping_to = db.Column(db.String(300), nullable =True) ;

	post_title = db.Column(db.String(300), nullable =True) ;
	post_description = db.Column(db.Text, nullable =True) ;
	post_refund_policy = db.Column(db.Text, nullable =True) ;

	buying_amount = db.Column(db.String(100), nullable =False) ;
	price_per_item = db.Column(db.String(100), nullable =False) ;



	# Post pictures, at lease 3 are REQUIRED
	gallery_1 = db.Column(db.String(20), nullable =False) ;
	gallery_2 = db.Column(db.String(20), nullable =False) ;
	gallery_3 = db.Column(db.String(20), nullable =False) ;
	gallery_4 = db.Column(db.String(20), nullable =True) ;
	gallery_5 = db.Column(db.String(20), nullable =True) ;
	gallery_6 = db.Column(db.String(20), nullable =True) ;
	gallery_7 = db.Column(db.String(20), nullable =True) ;
	gallery_8 = db.Column(db.String(20), nullable =True) ;
	gallery_9 = db.Column(db.String(20), nullable =True) ;


	post_id = db.Column(db.Integer, nullable=True) ;
	payment_id = db.Column(db.String(16), nullable=True) ;
	date_reserved = db.Column(db.DateTime, nullable =True, default =datetime.utcnow) ;


	pending_order_screen_id = db.Column(db.Integer, nullable =True) ;
	cart_id = db.Column(db.Integer, nullable =True) ;




class Message(db.Model):
	id = db.Column(db.Integer, primary_key=True) ;

	# Encrypted
	#title = db.Column(db.String(300), nullable =False) ; # change to this biiii
	title = db.Column(db.String(300), nullable =False) ;
	description = db.Column(db.Text, nullable =False) ;

	# Encrypted
	status = db.Column(db.String(50), nullable =False, default ="UNOPENED") ;
	message_type = db.Column(db.String(50), nullable =True) ;
	message_type_id = db.Column(db.Integer, nullable =True) ;


	# Cannot be encrypted ):
	message_from = db.Column(db.Integer, nullable =False) ;
	message_to = db.Column(db.Integer, nullable =False) ;

	deleted_from_sender = db.Column(db.Boolean, nullable =False, default =False) ; 
	deleted_from_reciever = db.Column(db.Boolean, nullable =False, default =False) ; 


	date_created = db.Column(db.DateTime, nullable =False, default =datetime.utcnow()) ;

	# Links back to the original message who posted the dispute
	disputes_id = db.Column(db.Integer, db.ForeignKey("dispute.id"), nullable =True) ;
	order_id = db.Column(db.Integer, nullable =True) ;
	#viewer_for_dispute = db.Column(db.Integer, nullable =True) ;

	


class Dispute(db.Model):
	__tablename__ = "dispute" ;

	id = db.Column(db.Integer, primary_key=True) ;
	messages = db.relationship("Message", backref="disputes_pictures", lazy =True) ;

	# To handle disputes
	dispute_order_id = db.Column(db.Integer, nullable =False) ;
	dispute_gallery_1 = db.Column(db.String(20), nullable =True) ;
	dispute_gallery_2 = db.Column(db.String(20), nullable =True) ;
	dispute_gallery_3 = db.Column(db.String(20), nullable =True) ;




class CartItem(db.Model):
	id = db.Column(db.Integer, primary_key=True) ;

	# Foreign keys
	post_id = db.Column(db.Integer, db.ForeignKey("post.id")) ;
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable =False) ;


	buying = db.Column(db.Integer, nullable=False, default =1) ;

	date_saved = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;

	# By default it will be == to date_saved EXACTLY!
	date_edited = db.Column(db.DateTime, nullable =False) ;



class SavedForLaterItem(db.Model):
	id = db.Column(db.Integer, primary_key=True) ;

	# Foreign keys
	post_id = db.Column(db.Integer, db.ForeignKey("post.id")) ;
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable =False) ;


	buying = db.Column(db.Integer, nullable=False, default =1) ;

	date_saved = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;











class FavoriteUser(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;

	user_id = db.Column(db.Integer, db.ForeignKey("user.id")) ;

	favorited_user = db.Column(db.Integer, nullable =False) ;



class FavoriteItem(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;

	user_id = db.Column(db.Integer, db.ForeignKey("user.id")) ;

	post_id = db.Column(db.Integer, db.ForeignKey("post.id")) ;








class Currency(db.Model):
	id = db.Column(db.Integer, primary_key =True) ;

	country = db.Column(db.String(6), nullable =False) ;
	price = db.Column(db.Float(precision =8), nullable =False) ;





'''
class NetworkFee(db.Model):
	__tablename__ = "network_fee" ;
	id = db.Column(db.Integer, primary_key =True) ;

	name = db.Column(db.String(30), nullable =False) ;
	price = db.Column(db.String(14), nullable =False) ;
'''




class AdminEditing(db.Model):
	__tablename__ = "adming_editing" ;
	id = db.Column(db.Integer, primary_key =True) ;
	admin_who_edited = db.Column(db.Integer, db.ForeignKey("user.id")) ;
	last_time_edited = db.Column(db.DateTime, nullable =False, default =datetime.utcnow) ;

	# To change the price manually for lowest possible price a user can enter, that accounts for transaction fees
	# So that their money doesn't get all eaten up by the transaction fee, ya know.
	lowest_price_possible_for_listing = db.Column(db.Float(12), nullable =False) ;
	shipping_address = db.Column(db.Text, nullable =False) ;





'''
class PendingFinalization(db.Model):
	__tablename__ = "pending_finalization" ;

	id = db.Column(db.Integer, primary_key =True) ;
	order_id = db.Column(db.Integer, nullable =False) ;

	sweep_all = db.Column(db.Boolean, nullable =False, default =False) ;
	send_to_buyer = db.Column(db.Integer, nullable =True) ;
	send_to_vendor = db.Column(db.Integer, nullable =True) ;
'''



class SweepAll(db.Model):
	__tablename__ = "sweep_all" ;

	id = db.Column(db.Integer, primary_key =True) ;
	account_number = db.Column(db.String(300), nullable =False) ;
# https://www.youtube.com/watch?v=OvhoYbjtiKc





class FeaturedPost(db.Model):
	__tablename__ = "featured_post" ;

	id = db.Column(db.Integer, primary_key =True) ;
	post_id = db.Column(db.Integer, nullable =False) ;
	priority = db.Column(db.Integer, nullable =True) ;
	date = db.Column(db.DateTime, nullable =False) ;




class Statistics(db.Model):
	__tablename__ = "statistics" ;

	id = db.Column(db.Integer, primary_key =True) ;

	disputes = db.Column(db.Integer, nullable =False, default =0) ;
	sales = db.Column(db.Integer, nullable =False, default =0) ;


