from flask import Blueprint, render_template, flash, redirect, url_for, request, abort ;
from flask_login import login_user, current_user, logout_user, login_required ;

from moneromarket import db ;

from moneromarket.messages.forms import NewMessageForm, ForwardMessageForm, NewDisputeForm ;
from moneromarket.main.forms import SearchForm ;
from moneromarket.database.models import Message, User, Order, Dispute, Post ;
from moneromarket.messages.utils import save_picture_disputes ;

from datetime import datetime ;

# Encryption and decryption
from cryptography.fernet import Fernet ;
from sqlalchemy import or_, and_ ;

import os ;
import json ;
from moneromarket.config import config ;



# Initialize the blueprint
messages = Blueprint("messages", __name__) ;




@messages.route("/messages/<filter_by>", methods=["GET", "POST"])
@login_required
def list(filter_by ="recieved"):
	# Object used to encrypt items
	key = config.get("FERNET_KEY") ;
	fernet = Fernet(key.encode()) ;


	if filter_by != "all" and filter_by != "sent" and filter_by != "received":
		abort(404) ;

	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	page = request.args.get("page", 1, type=int) ;
	query_user = request.args.get("query_user", "XMR", type=str) ;


	messages_received = messages_sent = messages_all = None ;


	if query_user == "XMR":
		# Don't get deleted messages
		if filter_by == "received":
			messages_received = Message.query.filter_by(message_to=current_user.id, deleted_from_reciever=False).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "sent":
			messages_sent = Message.query.filter_by(message_from=current_user.id, deleted_from_sender=False).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "all":
			messages_all = Message.query.filter(or_(and_(Message.message_to == current_user.id, Message.deleted_from_reciever == False), and_(Message.message_from == current_user.id, Message.deleted_from_sender == False))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;



	else:
		user = User.query.filter_by(username=query_user).first_or_404() ;
		if user.id != current_user.id:
			abort(403) ;

		# Don't get deleted messages
		if filter_by == "received":
			messages_received = Message.query.filter_by(message_to=user.id, deleted_from_reciever=False).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;

		elif filter_by == "sent":
			messages_sent = Message.query.filter_by(message_from=user.id, deleted_from_sender=False).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "all":
			messages_all = Message.query.filter(or_(and_(Message.message_to == current_user.id, Message.deleted_from_reciever == False), and_(Message.message_from == current_user.id, Message.deleted_from_sender == False))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;






	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("message/messages.html", title="Messages", messages_received=messages_received,
						   messages_sent=messages_sent, User=User, filter_by=filter_by, current_user=current_user, 
						   datetime=datetime.utcnow(), fernet=fernet, search_form=search_form, messages_all=messages_all, page=page,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes) ;



@messages.route("/message/create", methods=["GET", "POST"])
@login_required
def create():
	page = request.args.get("page", 1, type=int) ;
	filter_by = request.args.get("filter_by", "received", type=str) ;
	message_type = request.args.get("message_type", "MESSAGE", type=str) ;

	form = NewMessageForm() ;

	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	if form.validate_on_submit():

		# Object used to encrypt items
		key = config.get("FERNET_KEY") ;
		fernet = Fernet(key.encode()) ;


		username = User.query.filter(User.username.like('%' + form.message_to.data + '%')).first() ;

		
		if not username:
			flash(f"No username by the name \"{ form.message_to.data }\" exists.", "alert-red") ;
			return redirect(url_for("messages.create")) ;

		elif username.id == current_user.id:
			flash("Can't send a message to yourself, please send to another account.", "alert-red") ;
			return redirect(url_for("messages.create")) ;
		

		# Encrypt message data
		subject_encrypted = fernet.encrypt(form.subject.data.encode()).decode() ;
		description_encrypted = fernet.encrypt(form.body.data.encode()).decode() ;
		# status_encrypted = fernet.encrypt("UNOPENED".encode()).decode() ;
		# message_type_encrypted = fernet.encrypt("MESSAGE".encode()).decode() ;



		message = Message(title=subject_encrypted, description=description_encrypted, message_from=current_user.id, 
						  message_to=username.id, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type=message_type) ;


		db.session.add(message) ;
		db.session.commit() ;


		flash(f"Message sent to { username.username }.", "alert-green") ;
		return redirect(url_for("messages.list", filter_by=filter_by, page=page)) ;



	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;
	return render_template("message/create.html", title="Create Message", form=form, datetime=datetime.utcnow(),
						   search_form=search_form, filter_by=filter_by, page=page,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes,
						   message_type=message_type) ;
	# <!--  <td>{{ fernet.decrypt(message.status.encode()).decode() }}</td> -->







@messages.route("/message/view/<int:message_id>/<string:direction>", methods=["GET", "POST"])
@login_required
def view(message_id, direction):
	message = Message.query.filter_by(id=message_id).first_or_404() ;

	# No order but message is a dispute.....
	order = Order.query.filter_by(id=message.order_id).first() ;
	#if message.message_type == "DISPUTE" and not order:
	#	abort(404) ;

	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;


	if order:
		if not ((message.message_to == 1 or message.message_from == 1) and current_user.is_employee):
			if not current_user.is_admin:
				if message.message_type == "DISPUTE" and (Order.query.filter_by(id=message.order_id).first().user_id != current_user.id and Order.query.filter_by(id=message.order_id).first().vendor_id != current_user.id):
					abort(403) ;

	elif message.message_from != current_user.id:
		if message.message_to != current_user.id:
			if not ((message.message_to == 1 or message.message_from == 1) and current_user.is_employee):
				if not current_user.is_admin:
					abort(403) ;

		elif message.deleted_from_reciever:
			flash("Message was already deleted.", "alert-red") ;
			return redirect(url_for('messages.list', filter_by=direction)) ;



	elif message.deleted_from_sender:
		flash("Message was already deleted.", "alert-red") ;
		return redirect(url_for('messages.list', filter_by=direction)) ;







	page = request.args.get("page", 1, type=int) ;


	# Object used to encrypt item
	key = config.get("FERNET_KEY") ;
	fernet = Fernet(key.encode()) ;


	# Change read status to OPENED if it is a message recieved, NOT SENT!
	if direction == "received" or (direction == "all" and message.message_to == 1):
		
		# Save the encryption and commit to database
		# message.status = fernet.encrypt("OPENED".encode()).decode() ;
		message.status = "OPENED" ;
		db.session.commit() ;



	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("message/view.html", title="Message", message=message, User=User, direction=direction, page=page,
						   current_user=current_user, datetime=datetime.utcnow(), fernet=fernet, search_form=search_form, Dispute=Dispute,
						   Order=Order,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes) ;



@messages.route("/message/delete/recieved/<int:message_id>", methods=["GET", "POST"])
@login_required
def delete_received(message_id):
	message = Message.query.filter_by(id=message_id).first_or_404() ;


	if message.message_to != current_user.id:
		abort(403) ;
	elif message.deleted_from_reciever:
		flash("Message was already deleted.", "alert-red") ;
		return redirect(url_for('messages.list', filter_by=direction)) ;


	page = request.args.get("page", 1, type=int) ;
	filter_by = request.args.get("filter_by", "received", type=str) ;


	if message.deleted_from_sender:
		db.session.delete(message) ;
		db.session.commit() ;

	else:
		message.deleted_from_reciever = True ;
		db.session.commit() ;


	flash("Message deleted.", "alert-blue") ;
	return redirect(url_for('messages.list', filter_by=filter_by, page=page)) ;



@messages.route("/message/delete/sent/<int:message_id>", methods=["GET", "POST"])
@login_required
def delete_sent(message_id):
	message = Message.query.filter_by(id=message_id).first_or_404() ;


	if message.message_from != current_user.id:
		abort(403) ;
	elif message.deleted_from_sender:
		flash("Message was already deleted.", "alert-red") ;
		return redirect(url_for('messages.list', filter_by=direction)) ;





	page = request.args.get("page", 1, type=int) ;
	filter_by = request.args.get("filter_by", "sent", type=str) ;


	if message.deleted_from_reciever:
		db.session.delete(message) ;
		db.session.commit() ;

	else:
		message.deleted_from_sender = True ;
		db.session.commit() ;


	flash("Message deleted.", "alert-blue") ;
	return redirect(url_for('messages.list', filter_by=filter_by, page=page)) ;












@messages.route("/message/forward", methods=["GET", "POST"])
@login_required
def forward():
	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	user = request.args.get("username", "ADMIN", type=str) ;
	previous_page = request.args.get("previous_page", "messages.list", type=str) ;
	previous_page_id = request.args.get("previous_page_id", "0", type=str) ;
	disputes_id = request.args.get("disputes_id", 0, type=int) ;
	order_id = request.args.get("order_id", 0, type=int) ;
	sender = request.args.get("sender", None, type=str) ;
	message_type = request.args.get("message_type", "MESSAGE", type=str) ;


	order = Order.query.filter_by(id=order_id).first() ;
	if order:
		if order.status == "DISPUTING":
			if order.vendor_id == current_user.id or order.user_id == current_user.id or current_user.is_admin or current_user.is_employee:
				message_type = "DISPUTE" ;
			else:
				abort(403) ;


	if sender == None:
		sender = current_user.username ;
	else:
		if not current_user.is_admin:
			if not current_user.is_employee:
				abort(403) ;


	if previous_page != "orders.view_payment_id":
		try:
			previous_page_id = int(previous_page_id) ;
		except ValueError:
			previous_page_id = previous_page_id ;


	username = User.query.filter(User.username.like('%' + user + '%')).first_or_404() ;

	form = ForwardMessageForm() ;

	if form.validate_on_submit():

		# Object used to encrypt items
		key = config.get("FERNET_KEY") ;
		fernet = Fernet(key.encode()) ;

		
		if not username:
			flash(f"No username by the name \"{ form.message_to.data }\" exists.", "alert-red") ;
			return redirect(url_for("messages.create")) ;

		elif username.id == current_user.id:
			flash("Can't send a message to yourself, please send to another account.", "alert-red") ;
			return redirect(url_for("messages.create")) ;
		

		# Encrypt message data
		subject_encrypted = fernet.encrypt(form.subject.data.encode()).decode() ;
		description_encrypted = fernet.encrypt(form.body.data.encode()).decode() ;


		message_from = current_user.id ;
		if sender == "ADMIN":
			message_from = 1 ;

		if order:
			if order.status == "DISPUTING" and (current_user.is_admin or current_user.is_employee):
				message_from = 1 ;
		
		
		if order_id == 0:
			order_id = None ;
		if disputes_id != 0:
			message_type = "DISPUTE" ;
			if current_user.is_admin or current_user.is_employee:
				message_from = 1 ;
		else:
			disputes_id = None ;


		if message_type == "REPORT":
			order_id = User.query.filter_by(username=previous_page_id).first().id


		message = Message(title=subject_encrypted, description=description_encrypted, message_from=message_from, 
						  message_to=username.id, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type=message_type, order_id=order_id, disputes_id=disputes_id) ;



		if message_type == "DISPUTE" and order:
			other_title = None ;


			if current_user.is_employee or current_user.is_admin:
				other_title = "'" + "ADMIN" + "' replied to dispute" ;

			else:
				other_title = "'" + current_user.username + "' replied to dispute" ;



			other_body = ("For order #" + str(order.id) + " '" + order.orders_post.title + "', dispute was replied to." + 
				  "\nGo to the orders page to see entire message history." +
				  "\n\nThis is an automated message created when someone replies in a dispute.") ;

			o_t_e = fernet.encrypt(other_title.encode()).decode() ;
			o_b_e = fernet.encrypt(other_body.encode()).decode() ;



			'''
			if not current_user.is_admin and not current_user.is_employee:

				dispute_forward_to = None ;
				if order.vendor_id == username.id:
					dispute_forward_to = order.vendor_id ;
				else:
					dispute_forward_to = order.user_id ;


				other = Message(title=o_t_e, description=o_b_e, message_from=1, 
								  message_to=dispute_forward_to, date_created=datetime.utcnow(), status="UNOPENED", 
								  message_type="DISPUTE", disputes_id=disputes_id, order_id=order_id) ;

				db.session.add(other) ;


			else:'''

			if current_user.id != order.user_id:
				to_buyer = Message(title=o_t_e, description=o_b_e, message_from=1, 
								  message_to=order.user_id, date_created=datetime.utcnow(), status="UNOPENED", 
								  message_type="DISPUTE", disputes_id=disputes_id, order_id=order_id) ;

				db.session.add(to_buyer) ;

			if current_user.id != order.vendor_id:
				to_vendor = Message(title=o_t_e, description=o_b_e, message_from=1, 
								  message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
								  message_type="DISPUTE", disputes_id=disputes_id, order_id=order_id) ;

				db.session.add(to_vendor) ;



		db.session.add(message) ;
		db.session.commit() ;


		flash(f"Message sent to { username.username }.", "alert-green") ;

		if previous_page == "messages.list":
			return redirect(url_for("messages.list", filter_by="sent")) ;

		elif previous_page == "users.profile":
			return redirect(url_for("users.profile", username=user)) ;

		elif previous_page == "orders.accept":
			return redirect(url_for("orders.accept", order_id=previous_page_id)) ;
		elif previous_page == "orders.view_order":
			return redirect(url_for("orders.view_order", order_id=previous_page_id)) ;




	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;
	return render_template("message/forward.html", title="Create Message", form=form, datetime=datetime.utcnow(), order_id=order_id,
						   search_form=search_form, user=user, previous_page=previous_page, id=previous_page_id, disputes_id=disputes_id,
						   sender=sender, order=order, message_type=message_type,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes) ;






































@messages.route("/dispute/create/<int:order_id>", methods=["GET", "POST"])
@login_required
def start_dispute(order_id):
	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	previous_page = request.args.get("previous_page", "main.home", type=str) ;
	previous_page_id = request.args.get("previous_page.id", 1, type=int) ;
	order = Order.query.filter_by(id=order_id).first_or_404() ;

	if order.user_id != current_user.id:
		abort(403) ;

	if Dispute.query.filter_by(dispute_order_id=order_id).first():
		flash("Dispute already initiated.", "alert-faded-yellow") ;
		return redirect(url_for(previous_page, order_id=order_id)) ;



	form = NewDisputeForm() ;

	if form.validate_on_submit():
		# Save picture variables for end to save into database
		gallery_1 = None ; 
		gallery_2 = None ; 
		gallery_3 = None ;

		if form.pictures.data[0]:
			accepted_extensions = { "jpg", "png", "jpeg", "pneg" } ;

			if len(form.pictures.data) > 3:
				flash("3 files maximum are allowed.", "alert-red") ;
				return redirect(url_for('messages.start_dispute', order_id=order.id)) ;

			elif len(form.pictures.data) != 0:
				# Go through each picture to make sure they are the right format
				for picture in form.pictures.data:
					# Format for form.picture.data has nonsense filler in the last three characters
					if str(picture).lower()[-7:-3] in accepted_extensions or str(picture).lower()[-6:-3] in accepted_extensions:
						print("Accepted") ;

					else:
						flash("Only JPEG, JPG, PNG, & PNEG files are allowed. Please try again.", "alert-red") ;
						return redirect(url_for('messages.start_dispute', order_id=order.id)) ;


				# Save each photo now in the database
				for index in range(len(form.pictures.data)):
					saved_picture = save_picture_disputes(form.pictures.data[index]) ;

					if index == 0:
						gallery_1 = saved_picture ;

					elif index == 1:
						gallery_2 = saved_picture ;

					elif index == 2:
						gallery_3 = saved_picture ;






		# Object used to encrypt items
		key = config.get("FERNET_KEY") ;
		fernet = Fernet(key.encode()) ;

		
		

		# Encrypt message data
		subject_encrypted = fernet.encrypt(form.subject.data.encode()).decode() ;
		description_encrypted = fernet.encrypt(form.body.data.encode()).decode() ;
		# status_encrypted = fernet.encrypt("UNOPENED".encode()).decode() ;
		# message_type_encrypted = fernet.encrypt("MESSAGE".encode()).decode() ;


		dispute = Dispute(dispute_order_id=order_id, dispute_gallery_1=gallery_1, dispute_gallery_2=gallery_2, dispute_gallery_3=gallery_3) ;

		message = Message(title=subject_encrypted, description=description_encrypted, message_from=current_user.id, 
						  message_to=1, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type="DISPUTE", disputes_id=dispute.id, order_id=order_id) ;



		v_title = "'" + current_user.username + "' has initiated a dispute against you" ;
		v_body = ("For order #" + str(order.id) + " '" + order.orders_post.title + "' was disputed." + 
				  "\nWe will look into the dispute and also review your side of the story and then make a decision about what to do." +
				  "\nIf you sent the correct item(s) and didn't pull any sort of scam, then you have nothing to worry about." +
				  "\nPlease look out for messages and check your orders page constantly.") ;

		v_t_e = fernet.encrypt(v_title.encode()).decode() ;
		v_b_e = fernet.encrypt(v_body.encode()).decode() ;

		vendor = Message(title=v_t_e, description=v_b_e, message_from=1, 
						  message_to=order.vendor_id, date_created=datetime.utcnow(), status="UNOPENED", 
						  message_type="DISPUTE", disputes_id=dispute.id, order_id=order.id) ;

		order.status = "DISPUTING" ;
		date_current = datetime.utcnow() ;
		order.recent_update = date_current ;
		order.buyer_disputed = date_current ;
		db.session.add(dispute) ;
		db.session.add(vendor) ;
		db.session.add(message) ;
		db.session.commit() ;


		flash(f"Dispute sent to ADMIN.", "alert-blue") ;
		if previous_page == "orders.view_order":
			return redirect(url_for("orders.view_order", order_id=order_id)) ;
		else:
			return redirect(url_for('main.home')) ;



	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;
	return render_template("message/dispute/create.html", title="Create Message", form=form, datetime=datetime.utcnow(),
						   search_form=search_form, order=order,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes) ;
	# <!--  <td>{{ fernet.decrypt(message.status.encode()).decode() }}</td> -->








@messages.route("/messages/admin", methods=["GET", "POST"])
@login_required
def admin():
	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;

	# Object used to encrypt items
	key = config.get("FERNET_KEY") ;
	fernet = Fernet(key.encode()) ;
	filter_by = request.args.get("filter_by", "all", type=str) ;

	if filter_by != "all" and filter_by != "sent" and filter_by != "received":
		abort(404) ;

	if not current_user.is_admin:
		if not current_user.is_employee:
			abort(403) ;


	
	page = request.args.get("page", 1, type=int) ;
	message_type = request.args.get("message_type", "message", type=str) ;


	messages = None ;


	if message_type == "dispute":
		# Don't get deleted messages
		if filter_by == "received":
			messages = Message.query.filter_by(message_to=1, deleted_from_reciever=False, message_type="DISPUTE").order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "sent":
			messages = Message.query.filter_by(message_from=1, deleted_from_sender=False, message_type="DISPUTE").order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "all":
			messages = Message.query.filter(or_(and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE"), and_(Message.message_from == 1, Message.deleted_from_sender == False, Message.message_type == "DISPUTE"))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;



	else:
		#Don't get deleted messages
		if filter_by == "received":
			messages = Message.query.filter_by(message_to=1, deleted_from_reciever=False, message_type="MESSAGE").order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "sent":
			messages = Message.query.filter_by(message_from=1, deleted_from_sender=False, message_type="MESSAGE").order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "all":
			messages = Message.query.filter(or_(and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "MESSAGE"), and_(Message.message_from == 1, Message.deleted_from_sender == False, Message.message_type == "MESSAGE"))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;






	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("message/admin/list.html", title="Messages", messages=messages, User=User, filter_by=filter_by, 
						   datetime=datetime.utcnow(), fernet=fernet, search_form=search_form, page=page,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes) ;














@messages.route("/messages/disputes", methods=["GET", "POST"])
@login_required
def disputes_list():
	statistic_users = len(User.query.all()) ;
	statistic_listings = len(Post.query.all()) ;
	statistic_disputes = len(Dispute.query.all()) ;
	
	# Object used to encrypt items
	key = config.get("FERNET_KEY") ;
	fernet = Fernet(key.encode()) ;
	filter_by = request.args.get("filter_by", "all", type=str) ;
	order_id = request.args.get("order_id", 0, type=int) ;


	if filter_by != "all" and filter_by != "sent" and filter_by != "received":
		abort(404) ;


	order = Order.query.filter_by(id=order_id).first_or_404() ;

	if current_user.id != order.user_id:
		if current_user.id != order.vendor_id:
			if not current_user.is_admin:
				if not current_user.is_employee:
					abort(403) ;



	page = request.args.get("page", 1, type=int) ;


	# Find out other user in dispute
	other_user = None ;
	if current_user.id == order.user_id:
		other_user = order.vendor_id ;
	else:
		other_user = order.user_id ;



	messages = None ;


	if current_user.is_admin or current_user.is_employee:
		# Don't get deleted messages
		if filter_by == "received":
			messages = Message.query.filter(or_(and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id, Message.message_from == order.user_id), and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id, Message.message_from == order.vendor_id))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "sent":
			messages = Message.query.filter_by(message_from=1, deleted_from_sender=False, message_type="DISPUTE", order_id=order_id).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "all":
			messages = Message.query.filter(or_(and_(or_(and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id, Message.message_from == order.user_id), and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id, Message.message_from == order.vendor_id))), and_(Message.message_from == 1, Message.deleted_from_sender == False, Message.message_type == "DISPUTE", Message.order_id == order_id))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;


	else:
		# Don't get deleted messages
		if filter_by == "received":
			messages = Message.query.filter(or_(and_(Message.message_to == current_user.id, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id), and_(Message.message_from == other_user, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id), and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id, Message.message_from == 1))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "sent":
			messages = Message.query.filter_by(message_from=current_user.id, deleted_from_sender=False, message_type="DISPUTE", order_id=order_id).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;
		
		elif filter_by == "all":
			messages = Message.query.filter(or_(and_(or_(and_(Message.message_to == current_user.id, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id), and_(Message.message_from == other_user, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id), and_(Message.message_to == 1, Message.deleted_from_reciever == False, Message.message_type == "DISPUTE", Message.order_id == order_id, Message.message_from == 1))), and_(Message.message_from == current_user.id, Message.deleted_from_sender == False, Message.message_type == "DISPUTE", Message.order_id == order_id))).order_by(Message.date_created.desc()).paginate(page=page, per_page=10) ;




	# Make the search bar on the top right work
	search_form = SearchForm() ;
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data)) ;

	return render_template("message/dispute/list.html", title="Disputes", messages=messages, User=User, filter_by=filter_by, 
						   datetime=datetime.utcnow(), fernet=fernet, search_form=search_form, page=page, other_user=other_user,
						   order_id=order_id,
						   statistic_users=statistic_users, statistic_listings=statistic_listings, statistic_disputes=statistic_disputes) ;
















