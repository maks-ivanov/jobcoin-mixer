import config
from math import trunc
import requests
# Write your Jobcoin API client here.

def get_balance(address):
    return truncate(float(requests.get(config.API_ADDRESS_URL + '/' + address).json()['balance']))

def send_coin(from_, to, amount):
	if amount <= 0.0:
		return

	data = {
	'fromAddress': from_,
	'toAddress': to,
	'amount': amount,
	}

	return requests.post(config.API_TRANSACTIONS_URL, data=data)

def truncate(number, digits=config.TRUNCATE_DIGITS):
    stepper = 10.0 ** digits
    return trunc(stepper * number) / stepper

