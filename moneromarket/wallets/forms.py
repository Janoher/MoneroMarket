from flask_wtf import FlaskForm  
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, DecimalField, PasswordField  
from wtforms.validators import DataRequired, Length, InputRequired  

class SendMoneroForm(FlaskForm):
	address = StringField("Address", validators=[DataRequired(), Length(min=95, max=95)])  

	amount = DecimalField("Amount", validators=[DataRequired()])  

	password = PasswordField("Password", validators=[InputRequired(), Length(max=64)])  

	submit = SubmitField("Send")  