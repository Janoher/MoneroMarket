from flask_wtf import FlaskForm  
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, SelectField, MultipleFileField, IntegerField, DateField  
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, Optional, ValidationError  
from flask_wtf.file import FileField, FileAllowed  



class CreateOutgoingShipmentForm(FlaskForm):
	tracking_number = StringField("Tracking Number/ID", validators=[DataRequired()])  
	description = TextAreaField("Description", validators=[DataRequired()])  
	shipping_cost = DecimalField("Shipping Cost", validators=[DataRequired()])  

	expected_arrival_date = DateField("Expected Arrival", format='%m/%d/%Y', validators=[DataRequired()])  

	pictures = MultipleFileField("Upload Pictures (6 - 21)")  
	receipt_picture = FileField("Upload Receipt")  

	submit = SubmitField("Submit")  



class CreateOutgoingDigitalShipmentForm(FlaskForm):
	description = TextAreaField("Description", validators=[DataRequired()])  
	description_digital = TextAreaField("Description to Buyer", validators=[DataRequired()])  

	pictures = MultipleFileField("Upload Pictures (6 - 21)")  

	submit = SubmitField("Submit")  



class ChangeBuyerAddressForm(FlaskForm):
	return_address = StringField("Return Address", validators=[DataRequired(), Length(min=95, max=95)])  

	submit_buyer = SubmitField("Change")  

class ChangeVendorAddressForm(FlaskForm):
	return_address = StringField("Return Address", validators=[DataRequired(), Length(min=95, max=95)])  

	submit_vendor = SubmitField("Change")  

class ChangeBuyerShippingAddressForm(FlaskForm):
	shipping_address = TextAreaField("Return Address", validators=[DataRequired()])  

	submit_shipping_buyer = SubmitField("Change")  







class SearchOrderForm(FlaskForm):
	order_number = StringField("Order Number", validators=[DataRequired(), Length(min=1)])  

	submit = SubmitField("Search")  


class SearchTransactionIDForm(FlaskForm):
	transaction_id = StringField("Transaction ID", validators=[DataRequired(), Length(min=64, max=64)])  

	submit_transaction_id = SubmitField("Search")  

class SearchPublicAddressForm(FlaskForm):
	public_address = StringField("Public Address", validators=[DataRequired(), Length(min=95, max=95)])  

	submit_public_address = SubmitField("Search")  

class SearchPaymentIDForm(FlaskForm):
	payment_id = StringField("Payment ID", validators=[DataRequired(), Length(min=16, max=16)])  

	submit_payment_id = SubmitField("Search")  

class AdminEditingForm(FlaskForm):
	lowest_price = DecimalField("Lowest Price in Monero")  

	shipping_address = TextAreaField("Shipping Address")  

	submit = SubmitField("Update")  











class SplitFundsForm(FlaskForm):
	to_buyer = DecimalField("To Buyer", validators=[DataRequired()])  
	to_vendor = DecimalField("To Vendor", validators=[DataRequired()])  

	description = TextAreaField("Description", validators=[DataRequired()])  

	submit_split = SubmitField("Split")  





class ReleaseBuyerForm(FlaskForm):
	description = TextAreaField("Description", validators=[DataRequired()])  

	submit_buyer = SubmitField("Release")  


class ReleaseVendorForm(FlaskForm):
	description = TextAreaField("Description", validators=[DataRequired()])  

	submit_vendor = SubmitField("Release")  




class AddFeaturedPost(FlaskForm):
	post_id = IntegerField("Post Id", validators=[DataRequired()])  

	submit_featured = SubmitField("Add")  




