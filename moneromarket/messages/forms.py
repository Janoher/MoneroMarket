from flask_wtf import FlaskForm ;
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, SelectField, MultipleFileField, IntegerField, DateField ;
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, Optional, ValidationError ;
from flask_wtf.file import FileField, FileAllowed 


class NewMessageForm(FlaskForm):
	message_to = StringField("Message to", validators=[InputRequired(), Length(min=4, max=16)]) ;

	subject = StringField("Subject", validators=[InputRequired(), Length(max=50)]) ;

	body = TextAreaField("Write message here", validators=[InputRequired(), Length(max=500)]) ;


	submit = SubmitField("Send Message") ;



class ForwardMessageForm(FlaskForm):
	subject = StringField("Subject", validators=[InputRequired(), Length(max=50)]) ;

	body = TextAreaField("Write message here", validators=[InputRequired(), Length(max=500)]) ;


	submit = SubmitField("Send Message") ;















class NewDisputeForm(FlaskForm):
	subject = StringField("Subject", validators=[InputRequired(), Length(max=50)]) ;

	body = TextAreaField("Write message here", validators=[InputRequired(), Length(max=500)]) ;

	pictures = MultipleFileField("Upload Pictures (0 - 3)") ;

	submit = SubmitField("Send Message") ;






















