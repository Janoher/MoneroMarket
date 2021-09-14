from flask_wtf import FlaskForm ;
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, SelectField, MultipleFileField, IntegerField, FileField ;
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, Optional, ValidationError ;

from flask_login import current_user ;

from moneromarket.database.models import User, Post ;
import decimal ;



class CreateListingForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired(), Length(min=5, max=50)]) ;
	description = TextAreaField("Description", validators=[DataRequired()]) ;

	price = DecimalField("Price", places=5, rounding=decimal.ROUND_UP, validators=[DataRequired()]) ;
	supply = IntegerField("Supply", validators=[DataRequired()]) ;
	'''
	category = SelectField("Category") ;

	shipping_from = SelectField("Shipping from") ;
	shipping_to = SelectField("Shipping to") ;'''

	refund_policy = TextAreaField("Refund Policy", validators=[DataRequired()]) ;

	pictures = MultipleFileField("Upload Pictures (3 - 12)") ;

	submit = SubmitField("Post") ;



class EditListingForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired(), Length(min=5, max=50)]) ;
	description = TextAreaField("Description", validators=[DataRequired()]) ;

	price = DecimalField("Price", places=5, validators=[DataRequired()]) ;
	supply = IntegerField("Supply", validators=[DataRequired()]) ;
	'''
	category = SelectField("Category") ;

	shipping_from = SelectField("Shipping from") ;
	shipping_to = SelectField("Shipping to") ;'''

	refund_policy = TextAreaField("Refund Policy", validators=[DataRequired()]) ;


	picture_1 = FileField("Update Picture") ;
	picture_2 = FileField("Update Picture") ;
	picture_3 = FileField("Update Picture") ;
	picture_4 = FileField("Update Picture") ;
	picture_5 = FileField("Update Picture") ;
	picture_6 = FileField("Update Picture") ;
	picture_7 = FileField("Update Picture") ;
	picture_8 = FileField("Update Picture") ;
	picture_9 = FileField("Update Picture") ;


	submit = SubmitField("Update") ;




















