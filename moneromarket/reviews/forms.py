from flask_wtf import FlaskForm ;
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, SelectField, MultipleFileField, IntegerField, FileField ;
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, Optional, ValidationError ;

from flask_login import current_user ;



class CreateReviewForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired(), Length(min=5, max=50)]) ;
	description = TextAreaField("Description", validators=[DataRequired()]) ;

	pictures = MultipleFileField("Upload Pictures (0 - 3)") ;

	submit = SubmitField("Submit") ;




class DisputeReviewForm(FlaskForm):
	description = TextAreaField("Description", validators=[DataRequired()]) ;

	submit = SubmitField("Submit") ;




class EditReviewForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired(), Length(min=5, max=50)]) ;
	description = TextAreaField("Description", validators=[DataRequired()]) ;

	submit = SubmitField("Edit") ;