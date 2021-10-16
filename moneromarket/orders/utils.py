from flask_login import current_user  
from flask import current_app  
from PIL import Image  
import secrets  
import os  

import qrcode  


# Save uploaded pictures
def save_picture_qrcode(qrcode_text):
	# 8 bytes random hex
	random_hex = secrets.token_hex(8)  


	# Join the names to be, example: encrypted.png
	picture_filename = random_hex + ".png"  
	picture_path = os.path.join(current_app.root_path, "static/img/qrcodes", picture_filename)  


	# Resize image before saving
	output_size = (128, 128)  

	reduced_image = qrcode.make(qrcode_text) 
	reduced_image.thumbnail(output_size)  

	# Commit save
	reduced_image.save(picture_path)  



	'''
	# Delete old profile picture
	previous_picture = os.path.join(current_app.root_path, "static/img/posts", current_user.profile_picture)
	if os.path.exists(previous_picture) and current_user.profile_picture != "default.jpg":
		os.remove(previous_picture)  '''




	# String of file name
	return picture_filename  



def delete_picture_qrcode(image):
	# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/qrcodes", image)
		if os.path.exists(previous_picture):
			os.remove(previous_picture)  







def delete_picture_of_receipt(image):
	# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/employees/receipts", image)
		if os.path.exists(previous_picture):
			os.remove(previous_picture)  











# Save uploaded pictures
def save_picture_copied_post(form_picture):
	# 8 bytes random hex
	random_hex = secrets.token_hex(8)  

	# Get file extension, example: .jpg, .png
	_, file_extension = os.path.splitext(form_picture)  

	# Join the names to be, example: encrypted.png
	picture_filename = random_hex + file_extension.lower()  
	picture_path = os.path.join(current_app.root_path, "static/img/posts/originals", picture_filename)  


	# Resize image before saving
	output_size = (1024, 1024)  
	reduced_image = Image.open(os.path.join(current_app.root_path, "static/img/posts/", form_picture)).copy()  

	reduced_image.thumbnail(output_size)  

	# Commit save
	reduced_image.save(picture_path)  



	'''
	# Delete old profile picture
	previous_picture = os.path.join(current_app.root_path, "static/img/posts", current_user.profile_picture)
	if os.path.exists(previous_picture) and current_user.profile_picture != "default.jpg":
		os.remove(previous_picture)  '''




	# String of file name
	return picture_filename  









def delete_post_picture_path(gallery_index):
	# Delete old profile picture
		previous_picture = os.path.join(current_app.root_path, "static/img/posts/originals", gallery_index)
		if os.path.exists(previous_picture):
			os.remove(previous_picture)  