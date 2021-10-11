from flask import Blueprint, render_template, flash, redirect, url_for, request  
from flask_login import login_user, current_user, logout_user, login_required  

from moneromarket import db, bcrypt  
from moneromarket.wallets.forms import SendMoneroForm  

from datetime import datetime  
from decimal import Decimal  
from moneromarket.main.forms import SearchForm  

from moneromarket.wallets.utils import MergeIncomingAndOutgoing  
from moneromarket.database.models import Currency  

from monero.wallet import Wallet  
from monero.backends.jsonrpc import JSONRPCWallet  
from monero.daemon import Daemon  
from monero.address import address  

# Encryption and decryption
from cryptography.fernet import Fernet  
import numpy  

import os  
import json  
from moneromarket.config import config  




wallets = Blueprint("wallets", __name__)  



@wallets.route("/wallet", methods=["GET", "POST"])
def home():

	# For paginations and filtering of 
	page = request.args.get("page", 1, type=int)  
	filter_by = request.args.get("filter_by", "all", type=str)  


	# Traffic wallet through TOR
	daemon = Daemon(host="xmrag4hf5xlabmob.onion", proxy_url="socks5h://127.0.0.1:9050")  
	wallet = Wallet(port=28088)  
	key = config.get("FERNET_KEY")  

	# Object used to encrypt items
	fernet = Fernet(key.encode())  


	# Get network fees:
	# network_fees = NetworkFee.query.all()  
	network_fees = [ ]  
	network_fees.append(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=1, relay=False)[0].fee)  
	network_fees.append(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=2, relay=False)[0].fee)  
	network_fees.append(wallet.accounts[2].transfer(wallet.accounts[3].address(), 0.000000000001, priority=3, relay=False)[0].fee)  
	# network_fees.append(wallet.accounts[0].transfer(wallet.accounts[1].address(), 0.000000000001, priority=4, relay=False)[0].fee)  


	transactions = None  
	if filter_by == "all":
		# For transaction history
		transactions = MergeIncomingAndOutgoing(wallet.accounts[int(fernet.decrypt(current_user.account_number.encode()).decode())].incoming(),
											    wallet.accounts[int(fernet.decrypt(current_user.account_number.encode()).decode())].outgoing())  

	elif filter_by == "sent":
		transactions = wallet.accounts[int(fernet.decrypt(current_user.account_number.encode()).decode())].outgoing()  

	elif filter_by == "received":
		transactions = wallet.accounts[int(fernet.decrypt(current_user.account_number.encode()).decode())].incoming()  






	form = SendMoneroForm()  


	if form.validate_on_submit():


		fixed_to_fiat = None  
		currency = request.form.get("currency").upper()  

		# Will always be true as of now, but in the future will allow for static Monero prices.
		# Commented out original and replaced with "if True:"
		# Just uncomment and delete "if True:" whenever ready to allow for static Monero prices, as everything is already all set up.

		# if request.form.get("fiat") == "Fiat":
		if False:
			fixed_to_fiat = True  
		else:
			fixed_to_fiat = False  

		# Least amount possible is 1 x 10^-8
		# Scratch that, that's what I wanted haha, but unfortanately the price can't be less than the transaction fees
		# Starting officialy at 0.0001 on 04-15/2021, and subject to change.
		# For Monero.....



		# Convert to fiat to adjust the price....
		if fixed_to_fiat == True:
			if currency == "XMR":
				form.amount.data = float(form.amount.data) * float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "USDT":
				form.amount.data = float(form.amount.data) * (float(Currency.query.filter_by(country="USDT").first().price) / float(Currency.query.filter_by(country=currency).first().price))  


			# Never less than $1 USD
			if float(form.amount.data) < float(1.00):
				form.amount.data = float(1.00)  


		# Convert to Monero to keep it static.
		elif fixed_to_fiat == False:
			if currency == "USDT":
				form.amount.data = float(form.amount.data) / float(Currency.query.filter_by(country="USDT").first().price)  

			elif currency != "XMR":
				form.amount.data = float(form.amount.data) * float(Currency.query.filter_by(country=currency).first().price) / float(Currency.query.filter_by(country="USDT").first().price)  


			'''
			# Never less than $1 USD
			if float(form.amount.data) < float(1) / float(Currency.query.filter_by(country="USDT").first().price):
				form.amount.data = float(1) / float(Currency.query.filter_by(country="USDT").first().price)  
			'''









		if not bcrypt.check_password_hash(current_user.password, form.password.data):
			flash("Password incorrect..", "alert-red")  
			form.amount.data = 0.0  
			return redirect(url_for('wallets.home'))  

		# Get important and frequently used variables to not have to copy & paste throughout the function...
		fee_priority = request.form.get("fee-priority")  
		unlocked_balance = wallet.accounts[int(fernet.decrypt(current_user.account_number.encode()).decode())].balance(unlocked=True)  


		# Don't attempt to send any money if user tries to send more money than what they have unlocked.
		if float(form.amount.data) > float(unlocked_balance):
			flash(f"{ form.amount.data } XMR is more than your unlocked balance, please send a different amount, or wait until balance is fully unlocked.", "alert-red")  


		# Send ALL available money, without worrying about the transaction fee interfering, only if transaction is not zero of course
		elif float(form.amount.data) == float(unlocked_balance) and float(unlocked_balance) != 0.0:
			if float(network_fees[int(fee_priority)]) >= float(unlocked_balance):
				flash(f"Fee is higher than unlocked balanced, please try with a different fee, or wait until balance is fully unlocked.", "alert-red")  
			else:
				try:
					sweep_all = wallet.accounts[int(fernet.decrypt(current_user.account_number.encode()).decode())].sweep_all(form.address.data, int(fee_priority) + 1)  
					flash("Successfully sent ALL available UNLOCKED balance to address. Check below in Transaction History for info! Transaction ID: " + str(sweep_all[0][0]), "alert-blue")  
				except ValueError:
					flash("Address is not valid, please try sending to a different address.", "alert-red")  


		# If the price of the fee makes the amount higher than what is unlocked, give the user options on what to do.
		elif float(form.amount.data) + float(network_fees[int(fee_priority)]) > float(unlocked_balance):
			flash("Amount + Network Fee is more than unlocked balance, please retry with a smaller fee size, or retry but send ALL available Monero in unlocked balance, or wait until balance is fully unlocked.", "alert-red")  


		# Prevent sending zero Monero, as this will cause an exception and crash the server.... ):
		elif float(form.amount.data) == 0.0:
			flash("Error, cannot send 0 XMR, it is not allowed. Please send an actual amount.", "alert-red")  


		# Negative amounts of monero trying to send
		elif float(form.amount.data) < 0.0:
			flash("Error, cannot send negative amounts of XMR, it is not allowed. Please send an actual amount.", "alert-red")  


		# Send normal transaction with fee specified if both combined is less than or equal to the unlocked balance (:
		elif float(form.amount.data) + float(network_fees[int(fee_priority)]) <= float(unlocked_balance):
			try:
				transaction = wallet.accounts[int(fernet.decrypt(current_user.account_number.encode()).decode())].transfer(form.address.data, Decimal(form.amount.data), int(fee_priority) + 1)  
				flash(f"Successfully sent { form.amount.data } XMR to address. Check below in Transaction History for info! Transaction ID: " + str(transaction[0]), "alert-blue")  
			except ValueError:
				flash("Address is not valid, please try sending to a different address.", "alert-red")  
			except monero.exceptions.NotEnoughMoney:
				flash("Not enough Monero to send, please try with a smaller priority network fee, or add more Monero.", "alert-red")  

		# Uknown errors
		else:
			flash("Unknown error occured... ):", "alert-red")  


		form.amount.data = 0.0  
		form.password.data = None  
		return redirect(url_for('wallets.home'))  


		# Do a try-catch block so that a high fee won't cancel the order.
		# Ideally, tell the user how much the fee is and what amount will actually send.
		# If amount sending is more than balance, cancel transaction and just redirect user back home, saying that they don't have enough $$$.








	# Get currency rate
	usdt = Currency.query.filter_by(country="USDT").first().price  
	btc = Currency.query.filter_by(country="BTC").first().price  
	eth = Currency.query.filter_by(country="ETH").first().price  
	bch = Currency.query.filter_by(country="BCH").first().price  
	ltc = Currency.query.filter_by(country="LTC").first().price  
	doge = Currency.query.filter_by(country="DOGE").first().price  
	xaut = Currency.query.filter_by(country="XAUT").first().price  








	# Make the search bar on the top right work
	search_form = SearchForm()  
	if search_form.validate_on_submit():

		return redirect(url_for("listings.search", text=search_form.text.data))  
	return render_template("wallet/home.html", title="Wallet", datetime=datetime.utcnow(), search_form=search_form, wallet=wallet,
						   fernet=fernet, int=int, numpy=numpy, form=form, network_fees=network_fees, transactions=transactions, Decimal=Decimal,
						   float=float, filter_by=filter_by, Currency=Currency, daemon=daemon,
						   btc=btc, bch=bch, ltc=ltc, doge=doge, usdt=usdt, eth=eth, xaut=xaut)  

































