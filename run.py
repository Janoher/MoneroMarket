from moneromarket import create_app ;


# Initialize the app ;
app = create_app() ;


if __name__ == "__main__":
	app.run(debug = True) ;