from flask_wtf import FlaskForm  
from wtforms import StringField, SubmitField  
from wtforms.validators import DataRequired, InputRequired, Length, EqualTo, Optional, ValidationError  
from flask_wtf.file import FileField, FileAllowed  

from flask_login import current_user  

from moneromarket.users.validators import alpha_num  
from moneromarket.database.models import User  


class SearchForm(FlaskForm):
	text = StringField("Search..", validators=[InputRequired(), Length(max =50)])  

	submit_search = SubmitField("Search")  




class AdvancedSearchForm(FlaskForm):
	# search_for = StringField("Item..")  
	# vendor = StringField("Vendor..")  

	# ratings = radiobuttons
	# pricerange = 2 numberfields
	# ships from and to = 2 select fields

	submit_advanced_search = SubmitField("Get Results")  
























		