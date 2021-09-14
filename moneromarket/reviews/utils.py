from flask_login import current_user ;
from flask import current_app ;
from PIL import Image ;
import secrets ;
import os ;


# Save uploaded pictures
def save_picture_review(form_picture):
	# 8 bytes random hex
	random_hex = secrets.token_hex(8) ;

	# Get file extension, example: .jpg, .png
	_, file_extension = os.path.splitext(form_picture.filename) ;

	# Join the names to be, example: encrypted.png
	picture_filename = random_hex + file_extension.lower() ;
	picture_path = os.path.join(current_app.root_path, "static/img/reviews", picture_filename) ;


	# Resize image before saving
	output_size = (1024, 1024) ;
	reduced_image = Image.open(form_picture) ;
	reduced_image.thumbnail(output_size) ;

	# Commit save
	reduced_image.save(picture_path) ;


	# String of file name
	return picture_filename ;




def delete_review_picture_path(gallery_index):
	# Delete old profile picture
	previous_picture = os.path.join(current_app.root_path, "static/img/reviews", gallery_index) ;
	if os.path.exists(previous_picture):
		os.remove(previous_picture) ;
		return True ;


	return False ;








