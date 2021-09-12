#!/usr/bin/env python
import pytest
import re
from click.testing import CliRunner
from numpy import isclose
import time
from ..jobcoin import config, jobcoin, mixer
from .. import cli

class TestAccount:
    instance_count = 0
    def __init__(self, name=None, num_return_addresses = 2):
        if name == None:
            name = 'User' + str(TestAccount.instance_count)
        self.deposit_address = name + '_Deposit'
        self.return_addresses = [name + '_Return' + str(i) for i in range(num_return_addresses)]
        TestAccount.instance_count += 1

TEST_ACCOUNTS = [TestAccount(num_return_addresses= 2 + i) for i in range(4)]
TEST_ORIGIN_ADDRESS = 'Charlie'

@pytest.fixture
def response():
    import requests
    return requests.get('https://jobcoin.gemini.com/')


def test_content(response):
    assert 'Hello!' in response.content


def test_cli_basic():
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'Welcome to the Jobcoin mixer' in result.output


def test_cli_creates_address():
    runner = CliRunner()
    address_create_output = runner.invoke(cli.main, input='1234,4321').output
    output_re = re.compile(
        r'You may now send Jobcoins to address [0-9a-zA-Z]{32}. '
        'They will be mixed and sent to your destination addresses.'
    )
    assert output_re.search(address_create_output) is not None


def test_get_balance():
    balance = jobcoin.get_balance('Alice')
    assert balance == 37.0

def test_check_address_unused():
    assert not jobcoin.check_address_unused('Alice')
    assert jobcoin.check_address_unused('DO_NOT_USE')


def test_send_coin():
    starting_balance_alice = jobcoin.get_balance('Alice')
    starting_balance_bob = jobcoin.get_balance('Bob')

    jobcoin.send_coin('Alice', 'Bob', 1.0)

    intermediate_balance_alice = jobcoin.get_balance('Alice')
    intermediate_balance_bob = jobcoin.get_balance('Bob')

    assert intermediate_balance_alice - starting_balance_alice == -1.0
    assert intermediate_balance_bob - starting_balance_bob == 1.0

    jobcoin.send_coin('Bob', 'Alice', 1.0)

    final_balance_alice = jobcoin.get_balance('Alice')
    final_balance_bob = jobcoin.get_balance('Bob')

    assert final_balance_alice == starting_balance_alice 
    assert final_balance_bob == starting_balance_bob

@pytest.fixture
def reset_accounts():
    all_addresses = [config.HOUSE_ADDRESS] + [a.deposit_address for a in TEST_ACCOUNTS]
    for a in TEST_ACCOUNTS:
        all_addresses += a.return_addresses

    for address in all_addresses:
        balance = jobcoin.get_balance(address)
        jobcoin.send_coin(address, TEST_ORIGIN_ADDRESS, balance)

def test_process_request(reset_accounts):
    coin_mixer = mixer.Mixer()
    test_account = TEST_ACCOUNTS[0]
    deposit_address = test_account.deposit_address
    return_addresses = test_account.return_addresses

    coin_mixer.create_mix_account(deposit_address, return_addresses)

    assert coin_mixer.deposit_addresses.qsize() == 1

    coin_mixer.poll_next_address()

    assert coin_mixer.mix_accounts == {deposit_address : set(return_addresses)}
    assert coin_mixer.mix_requests.qsize() == 0
    assert coin_mixer.deposit_addresses.qsize() == 1

    jobcoin.send_coin(TEST_ORIGIN_ADDRESS, deposit_address, 5)

    coin_mixer.poll_next_address()
    house_balance = jobcoin.get_balance(config.HOUSE_ADDRESS)

    assert house_balance == 5
    assert coin_mixer.mix_requests.qsize() == 1

    coin_mixer.process_next_mix_request()
    house_balance = jobcoin.get_balance(config.HOUSE_ADDRESS)
    return_address_balance = [jobcoin.get_balance(x) for x in return_addresses]

    assert house_balance < 5
    assert isclose(sum(return_address_balance), 5 - house_balance)
    assert coin_mixer.mix_requests.qsize() == 1

    coin_mixer.process_next_mix_request()
    assert coin_mixer.mix_requests.qsize() == 0

    return_address_balance = [jobcoin.get_balance(x) for x in return_addresses]
    house_balance = jobcoin.get_balance(config.HOUSE_ADDRESS)
    assert isclose(sum(return_address_balance), 5)

def test_process_request_multi_user(reset_accounts):
    # a day in life of a coin_mixer
    coin_mixer = mixer.Mixer()
    
    # create mixing addresses for a couple of test accounts
    for i in range(2):
        coin_mixer.create_mix_account(TEST_ACCOUNTS[i].deposit_address, TEST_ACCOUNTS[i].return_addresses)
    assert len(coin_mixer.mix_accounts) == 2
    assert coin_mixer.deposit_addresses.qsize() == 2

    # nothing should be happening yet
    coin_mixer.poll_next_address()
    assert len(coin_mixer.mix_accounts) == 2
    assert coin_mixer.mix_requests.qsize() == 0
    assert coin_mixer.deposit_addresses.qsize() == 2

    # send to the second user deposit address
    jobcoin.send_coin(TEST_ORIGIN_ADDRESS, TEST_ACCOUNTS[1].deposit_address, 5)
    coin_mixer.poll_next_address()

    # create two more addresses while also starting to mix
    for i in range(2, 4):
        coin_mixer.create_mix_account(TEST_ACCOUNTS[i].deposit_address, TEST_ACCOUNTS[i].return_addresses)
        coin_mixer.poll_next_address()
        coin_mixer.process_next_mix_request()
    
    assert len(coin_mixer.mix_accounts) == 4
    assert coin_mixer.mix_requests.qsize() == 1
    assert coin_mixer.deposit_addresses.qsize() == 4

    for i in range(4):
        jobcoin.send_coin(TEST_ORIGIN_ADDRESS, TEST_ACCOUNTS[i].deposit_address, 5)
        coin_mixer.process_next_mix_request()
        coin_mixer.poll_next_address()

    while coin_mixer.mix_requests.qsize() > 0:
        coin_mixer.process_next_mix_request()
        coin_mixer.poll_next_address()

    house_balance = jobcoin.get_balance(config.HOUSE_ADDRESS)
    assert isclose(house_balance, 0)

    expected_balances = (5, 10, 5, 5)
    returned_balances = [sum([jobcoin.get_balance(a) for a in x.return_addresses]) for x in TEST_ACCOUNTS]

    for i in range(4):
        assert isclose(returned_balances[i], expected_balances[i])

def test_coin_mixer(reset_accounts):
    coin_mixer = mixer.Mixer()
    coin_mixer.start()

    for i in range(4):
        coin_mixer.create_mix_account(TEST_ACCOUNTS[i].deposit_address, TEST_ACCOUNTS[i].return_addresses)
        jobcoin.send_coin(TEST_ORIGIN_ADDRESS, TEST_ACCOUNTS[i].deposit_address, i+10)

    while coin_mixer.mix_requests.qsize() == 0:
        time.sleep(1)

    while coin_mixer.mix_requests.qsize() > 0:
        time.sleep(1)

    expected_balances = (10, 11, 12, 13)
    returned_balances = [sum([jobcoin.get_balance(a) for a in x.return_addresses]) for x in TEST_ACCOUNTS]

    for i in range(4):
        assert isclose(returned_balances[i], expected_balances[i])

    coin_mixer.stop()
