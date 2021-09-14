from flask_login import current_user ;
from flask import current_app ;
from PIL import Image ;
import secrets ;
import os ;

from moneromarket import db ;
from moneromarket.database.models import Post ;




# Save uploaded pictures
def save_picture(form_picture):
	# 8 bytes random hex
	random_hex = secrets.token_hex(8) ;

	# Get file extension, example: .jpg, .png
	_, file_extension = os.path.splitext(form_picture.filename) ;

	# Join the names to be, example: encrypted.png
	picture_filename = random_hex + file_extension.lower() ;
	picture_path = os.path.join(current_app.root_path, "static/img/profiles", picture_filename) ;


	# Resize image before saving
	output_size = (512, 512) ;
	reduced_image = Image.open(form_picture) ;
	reduced_image.thumbnail(output_size) ;

	# Commit save
	reduced_image.save(picture_path) ;


	# Delete old profile picture
	previous_picture = os.path.join(current_app.root_path, "static/img/profiles", current_user.profile_picture)
	if os.path.exists(previous_picture) and current_user.profile_picture != "default.jpg":
		os.remove(previous_picture) ;


	# String of file name
	return picture_filename ;


def delete_profile_picture(profile_picture):
	previous_picture = os.path.join(current_app.root_path, "static/img/profiles", profile_picture)
	if os.path.exists(previous_picture) and profile_picture != "default.jpg":
		os.remove(previous_picture) ;





def delete_post(post_id):
	post = Post.query.filter_by(id=post_id).first() ;


	# Permanently delete images from database
	if post.gallery_1:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_1)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_1 = "" ;

	if post.gallery_2:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_2)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_2 = "" ;

	if post.gallery_3:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_3)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_3 = "" ;

	if post.gallery_4:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_4)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_4 = "" ;

	if post.gallery_5:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_5)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_5 = "" ;

	if post.gallery_6:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_6)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_6 = "" ;

	if post.gallery_7:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_7)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_7 = "" ;

	if post.gallery_8:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_8)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_8 = "" ;

	if post.gallery_9:
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_9)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

		post.gallery_9 = "" ;



	db.session.delete(post) ;
	db.session.commit() ;









