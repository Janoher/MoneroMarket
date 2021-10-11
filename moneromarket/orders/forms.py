from flask_wtf import FlaskForm  
from wtforms import StringField, TextAreaField, SubmitField, IntegerField  
from wtforms.validators import DataRequired, Length  

class CheckoutForm(FlaskForm):
	return_address = StringField("Return address")   # validators=[DataRequired(), Length(min=95, max=95)])  

	name_and_address = TextAreaField("Name and Address", validators=[DataRequired()])  

	submit = SubmitField("Place Order")  



class AddToCartForm(FlaskForm):
	quantity = IntegerField("Quantity")  

	post_id = IntegerField("post_id")  

	submit_cart = SubmitField("Add to Cart")  
	submit_buy = SubmitField("Buy Now")  
	submit_saved = SubmitField("Save for Later")  


class UpdateCartForm(FlaskForm):
	#quantity = IntegerField("Quantity")  

	cart_id = IntegerField("cart_id")  

	submit_update_cart = SubmitField("Update")  


class UpdateSavedForLaterForm(FlaskForm):
	#quantity = IntegerField("Quantity")  

	saved_id = IntegerField("saved_id")  

	submit_update_saved = SubmitField("Update")  
	submit_add_to_cart = SubmitField("Add to Cart")  




class OrderAcceptancePhysicalForm(FlaskForm):
	tracking_number = StringField("Tracking Number/ID", validators=[DataRequired()])  
	wallet_address = StringField("Wallet Address")  
	description = TextAreaField("Description")  

	submit = SubmitField("Submit")  
	decline = SubmitField("Decline")  


class OrderAcceptanceDigitalForm(FlaskForm):
	wallet_address = StringField("Wallet Address")  
	description = TextAreaField("Description", validators=[DataRequired()])  

	submit = SubmitField("Submit")  
	decline = SubmitField("Decline")  





class RequestBuyerReturnForm(FlaskForm):
	tracking_number = StringField("Tracking Number/ID", validators=[DataRequired()])  
	description = TextAreaField("Description")  

	submit = SubmitField("Submit")  
	#decline = SubmitField("Decline")  













