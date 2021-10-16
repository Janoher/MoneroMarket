from wtforms.validators import ValidationError  


# Validator for username to not contain any symbols, white spaces, or special characters except '_'
def alpha_num(form, field):
	# First character MUST be a letter
	if field.data[0].isnumeric() or field.data[0] == '_' or field.data[0].isalpha() != True:
		raise ValidationError("Username cannot start with a number or underscore(\'_\'), it must start with a letter.")  



	# Loop through string to find any symbols
	for character in field.data:
		if character.isnumeric() != True and character.isalpha() != True and character != '_':
			raise ValidationError("Username can only contain letters, numbers, and underscores(\'_\').")  





# Validator to except only certain file extensions when being uploaded or selected
def files_allowed(form, field):
	# Get file extension  .filename returns a string
	last_four = field.data.filename[-4:].lower()  
	last_five = field.data.filename[-5:].lower()  


	# Paramaters that are allowed
	if last_four != ".jpg" and last_four != ".png" and last_five != ".jpeg" and last_five != ".pneg":
		raise ValidationError("Only png, jpg, pneg, and jpeg files are allowed. Please choose a different file.")  






# Documentation: https://wtforms.readthedocs.io/en/2.3.x/validators/


































