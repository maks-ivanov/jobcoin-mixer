import config
import time
from queue import Queue
from random import uniform, shuffle
import threading
from jobcoin import *

class Mixer:
	def __init__(self):
		self.house_address = config.HOUSE_ADDRESS

		self.mix_accounts = dict()
		self.deposit_addresses = Queue()
		self.mix_requests = Queue()

		self.run_threads = False
		self.address_pollers = tuple([threading.Thread(target=self.run_poll_loop) for _ in range(config.NUM_ADDRESS_POLLERS)])
		self.request_processors = tuple([threading.Thread(target=self.run_process_request_loop) for _ in range(config.NUM_REQUEST_PROCESSORS)]) 
		
		# ensures that worker threads terminate when the main thread does
		for t in self.address_pollers + self.request_processors:
			t.daemon = True

	def create_mix_account(self, deposit_address, return_addresses):
		shuffle_copy = return_addresses[:]
		shuffle(shuffle_copy)
		self.mix_accounts[deposit_address] = set(shuffle_copy)
		self.deposit_addresses.put(deposit_address)


	def begin_mixing(self, deposit_address, amount):
		return_addresses = self.mix_accounts[deposit_address]
		mix_request = MixRequest(return_addresses, amount)
		self.transfer_to_house(deposit_address, amount)
		self.mix_requests.put(mix_request)

	def transfer_to_house(self, deposit_address, balance):
		send_coin(deposit_address, self.house_address, balance)

	def handle_request(self, mix_request):
		return_addresses = set(mix_request.return_addresses)
		amount = mix_request.amount

		send_address = return_addresses.pop()
		if len(return_addresses) == 0:
			send_amount = amount
		else:
			send_amount = uniform(10**(-config.TRUNCATE_DIGITS), amount)

		response = send_coin(self.house_address, send_address, send_amount)
		return send_address, send_amount

	def poll_next_address(self):
		if self.deposit_addresses.qsize() == 0:
			time.sleep(config.ADDRESS_POLLER_SLEEP_SECONDS)
			return

		deposit_address = self.deposit_addresses.get()
		balance = get_balance(deposit_address)

		if balance > 0:
			self.begin_mixing(deposit_address, balance)
		else:
			time.sleep(uniform(0, config.ADDRESS_POLLER_SLEEP_SECONDS))

		self.deposit_addresses.put(deposit_address)

	def process_next_mix_request(self):
		if self.mix_requests.qsize() == 0:
			time.sleep(config.REQUEST_PROCESSOR_SLEEP_SECONDS)
			return

		mix_request = self.mix_requests.get()
		sent_address, sent_amount = self.handle_request(mix_request)

		total_amount = mix_request.amount
		remaining_amount = total_amount - sent_amount
		return_addresses = set(mix_request.return_addresses)

		if remaining_amount > 0:
			return_addresses.remove(sent_address)
			next_request = MixRequest(return_addresses, remaining_amount)
			self.mix_requests.put(next_request)

	def run_poll_loop(self):
		while self.run_threads:
			self.poll_next_address()

	def run_process_request_loop(self):
		while self.run_threads:
			self.process_next_mix_request()

	def start(self):
		if not self.run_threads:
			self.run_threads = True

			for t in self.address_pollers: 
				t.start()

			for t in self.request_processors:
				t.start()

	def stop(self):
		self.run_threads = False

class MixRequest:
	def __init__(self, return_addresses, amount):
		self.return_addresses = return_addresses
		self.amount = amount