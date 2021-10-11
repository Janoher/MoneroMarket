from flask_wtf import FlaskForm  
from wtforms import StringField, PasswordField, SubmitField, TextAreaField  
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, Optional, ValidationError  
from flask_wtf.file import FileField, FileAllowed  

from flask_login import current_user  

from moneromarket.users.validators import alpha_num  
from moneromarket.database.models import User  


class RegistrationForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired(), Length(min =4, max =16), alpha_num])  

	email = StringField("Email", validators=[Email(), Optional()])  

	password = PasswordField("Password", validators=[InputRequired(), Length(max=64)])  

	confirm_password = PasswordField("Confirm Password", validators=[InputRequired(), EqualTo("password")])  


	submit = SubmitField("Register")  



	def validate_username(self, username):
		# Check to see if username exists in the database
		user = User.query.filter(User.username.like('%' + username.data + '%')).first()  

		if user:
			raise ValidationError("That username is already taken, please choose another one.")  

	def validate_email(self, email):
		# Lowercase email and check to see if email exists
		email = User.query.filter_by(email=email.data.lower()).first()  

		if email:
			raise ValidationError("That email is already taken, please choose another one.")  




class LoginForm(FlaskForm):
	username_or_email = StringField("Username or email", validators=[DataRequired()])  

	password = PasswordField("Password", validators=[InputRequired(), Length(max=30)])  


	submit = SubmitField("Login")  
















class UpdateProfileForm(FlaskForm):
	description = StringField("⇩ Update Description ⇩")  
	refund = StringField("⇩ Update Refund Policy ⇩")

	picture = FileField("Update Picture:")  

	submit = SubmitField("Save Changes")  

















class ChangePasswordForm(FlaskForm):
	current_password = PasswordField("Current password", validators=[InputRequired(), Length(max=30)])  

	new_password = PasswordField("New password", validators=[InputRequired(), Length(max=30)])  

	confirm_password = PasswordField("Confirm Password", validators=[InputRequired(), EqualTo("new_password")])  


	submit = SubmitField("Submit")  




class AddEmailForm(FlaskForm):
	email = StringField("Email", validators=[])  

	submit_add_email = SubmitField("Add")  







class UpdateEmailForm(FlaskForm):
	email = StringField("Email", validators=[Email()])  

	submit_update_email = SubmitField("Update")  







class DeleteEmailForm(FlaskForm):
	password = PasswordField("Password", validators=[InputRequired(), Length(max=30)])  

	submit_delete_email = SubmitField("Delete")  




class OneTimePasswordForm(FlaskForm):
	password = PasswordField("Password", validators=[InputRequired(), Length(max=30)])  

	submit_one_time_password = SubmitField("Submit")  

class DeleteAccountForm(FlaskForm):
	password = PasswordField("Password", validators=[InputRequired(), Length(max=30)])  

	submit_delete_account = SubmitField("Submit")  








































