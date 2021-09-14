from flask_login import current_user ;
from flask import current_app ;
from PIL import Image ;
import secrets ;
import os ;

from moneromarket.database.models import Post ;


# Save uploaded pictures
def save_picture_created_post(form_picture):
	# 8 bytes random hex
	random_hex = secrets.token_hex(8) ;

	# Get file extension, example: .jpg, .png
	_, file_extension = os.path.splitext(form_picture.filename) ;

	# Join the names to be, example: encrypted.png
	picture_filename = random_hex + file_extension.lower() ;
	picture_path = os.path.join(current_app.root_path, "static/img/posts", picture_filename) ;


	# Resize image before saving
	output_size = (1024, 1024) ;
	reduced_image = Image.open(form_picture) ;
	reduced_image.thumbnail(output_size) ;

	# Commit save
	reduced_image.save(picture_path) ;



	'''
	# Delete old profile picture
	previous_picture = os.path.join(current_app.root_path, "static/img/posts", current_user.profile_picture)
	if os.path.exists(previous_picture) and current_user.profile_picture != "default.jpg":
		os.remove(previous_picture) ;'''




	# String of file name
	return picture_filename ;




# Save updated pictures
def save_picture_edit_post(form_picture, index, post_id):
	# 8 bytes random hex
	random_hex = secrets.token_hex(8) ;

	# Get file extension, example: .jpg, .png
	_, file_extension = os.path.splitext(form_picture.filename) ;

	# Join the names to be, example: encrypted.png
	picture_filename = random_hex + file_extension.lower() ;
	picture_path = os.path.join(current_app.root_path, "static/img/posts", picture_filename) ;


	# Resize image before saving
	output_size = (1024, 1024) ;
	reduced_image = Image.open(form_picture) ;
	reduced_image.thumbnail(output_size) ;

	# Commit save
	reduced_image.save(picture_path) ;













	# Get Post ID
	post = Post.query.filter_by(id=post_id).first() ;

	
	if index == 0:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_1)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

	elif index == 1:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_2)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;

	elif index == 2:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_3)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;


	elif index == 3:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_4)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;


	elif index == 4:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_5)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;


	elif index == 5:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_6)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;


	elif index == 6:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_7)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;


	elif index == 7:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_8)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;


	elif index == 8:
		# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts", post.gallery_9)
		if os.path.exists(previous_picture):
			os.remove(previous_picture) ;





	# String of file name
	return picture_filename ;



def delete_post_picture_path(gallery_index):
	# Delete old profile picture
	previous_picture = os.path.join(current_app.root_path, "static/img/posts", gallery_index) ;
	if os.path.exists(previous_picture):
		os.remove(previous_picture) ;

		return True ;
	return False ;





































