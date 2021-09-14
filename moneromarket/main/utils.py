from moneromarket.database.models import SubCategory, Post ;


def get_category_info():
	# Categories
	# Books
	categories = { } ;

	e_books = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="e-books").first().id).all()) ;
	hard_copies = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="hardcopy").first().id).all()) ;
	books = e_books + hard_copies ;
	categories.update({"e-books": e_books}) ;
	categories.update({"hardcopy": hard_copies}) ;
	categories.update({"books": books}) ;

	# Electronics
	cell_phones = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="cell-phones").first().id).all()) ;
	computers = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="computers").first().id).all()) ;
	mining = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="mining").first().id).all()) ;
	stereos = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="stereos").first().id).all()) ;
	video_games = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="video-games").first().id).all()) ;
	electronics_other = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="electronics-other").first().id).all()) ;
	electronics = cell_phones + computers + mining + stereos + video_games + electronics_other ;
	categories.update({"cell-phones": cell_phones}) ;
	categories.update({"computers": computers}) ;
	categories.update({"mining": mining}) ;
	categories.update({"stereos": stereos}) ;
	categories.update({"video-games": video_games}) ;
	categories.update({"electronics-other": electronics_other}) ;
	categories.update({"electronics": electronics}) ;

	# Art & Collectibles
	antiques = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="antiques").first().id).all()) ;
	music = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="music").first().id).all()) ;
	paintings = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="paintings").first().id).all()) ;
	stamps = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="stamps").first().id).all()) ;
	art_other = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="art-other").first().id).all()) ;
	art = antiques + music + paintings + stamps + art_other ;
	categories.update({"antiques": antiques}) ;
	categories.update({"music": music}) ;
	categories.update({"paintings": paintings}) ;
	categories.update({"stamps": stamps}) ;
	categories.update({"art-other": art_other}) ;
	categories.update({"art": art}) ;

	# Clothing & Accessories
	men_clothing = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="men-clothing").first().id).all()) ;
	men_shoes = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="men-shoes").first().id).all()) ;
	men_accessories = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="men-accessories").first().id).all()) ;
	women_clothing = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="women-clothing").first().id).all()) ;
	women_shoes = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="women-shoes").first().id).all()) ;
	women_accessories = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="women-accessories").first().id).all()) ;
	kid_clothing = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="kid-clothing").first().id).all()) ;
	kid_shoes = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="kid-shoes").first().id).all()) ;
	kid_accessories = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="kid-accessories").first().id).all()) ;
	costumes = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="costumes").first().id).all()) ;
	make_up = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="make-up").first().id).all()) ;
	clothes_other = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="clothes-other").first().id).all()) ;
	clothes = (men_clothing + men_shoes + men_accessories + women_clothing + women_shoes + women_accessories + kid_clothing + kid_shoes + 
			   kid_accessories + costumes + make_up + clothes_other) ;
	categories.update({"men-clothing": men_clothing}) ;
	categories.update({"men-shoes": men_shoes}) ;
	categories.update({"men-accessories": men_accessories}) ;
	categories.update({"women-clothing": women_clothing}) ;
	categories.update({"women-shoes": women_shoes}) ;
	categories.update({"women-accessories": women_accessories}) ;
	categories.update({"kid-clothing": kid_clothing}) ;
	categories.update({"kid-shoes": kid_shoes}) ;
	categories.update({"kid-accessories": kid_accessories}) ;
	categories.update({"costumes": costumes}) ;
	categories.update({"make-up": make_up}) ;
	categories.update({"clothes-other": clothes_other}) ;
	categories.update({"clothes": clothes}) ;

	# Sports
	balls_equipment = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="balls-equipment").first().id).all()) ;
	camping = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="camping").first().id).all()) ;
	padding_gear = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="padding-gear").first().id).all()) ;
	sports_other = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="sports-other").first().id).all()) ;
	sports = balls_equipment + camping + padding_gear + sports_other ;
	categories.update({"balls-equipment": balls_equipment}) ;
	categories.update({"camping": camping}) ;
	categories.update({"padding-gear": padding_gear}) ;
	categories.update({"sports-other": sports_other}) ;
	categories.update({"sports": sports}) ;

	# Toys
	action_figures = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="action-figures").first().id).all()) ;
	board_games = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="board-games").first().id).all()) ;
	dolls = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="dolls").first().id).all()) ;
	puzzles = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="puzzles").first().id).all()) ;
	outdoor_toys = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="outdoor-toys").first().id).all()) ;
	toys_other = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="toys-other").first().id).all()) ;
	toys = action_figures + board_games + dolls + puzzles + outdoor_toys + toys_other ;
	categories.update({"action-figures": action_figures}) ;
	categories.update({"board-games": board_games}) ;
	categories.update({"dolls": dolls}) ;
	categories.update({"puzzles": puzzles}) ;
	categories.update({"outdoor-toys": outdoor_toys}) ;
	categories.update({"toys-other": toys_other}) ;
	categories.update({"toys": toys}) ;

	# Other
	other_other = len(Post.query.filter_by(sub_category=SubCategory.query.filter_by(value="other-other").first().id).all()) ;
	categories.update({"other-other": other_other}) ;



	return categories ;