from ..jobcoin.db_client import *

def test_create_delete_address_table():
	client = DbClient()
	client.create_address_table()
	client.delete_tables([ADDRESS_TABLE_NAME])

def test_insert_get_addresses():
	client = DbClient()
	client.create_address_table()
	assert client.insert_addresses('a', ['b', 'c'])
	assert not client.insert_addresses('a', ['b', 'c']) # should not be able to insert again for any of the above 3 addresses
	assert not client.insert_addresses('c', ['d', 'e'])
	assert client.get_return_addresses('a') == [u'b', u'c']
	for address in ['b', 'c']:
		assert client.get_deposit_address(address) == [u'a']
	client.delete_tables([ADDRESS_TABLE_NAME])

def test_deposit_addresses_in_table():
	client = DbClient()
	client.create_address_table()
	assert not client.check_address_in_table('a')
	client.insert_addresses('a', ['b', 'c'])
	assert client.check_address_in_table('a')
	assert client.check_address_in_table('b')
	client.delete_tables([ADDRESS_TABLE_NAME])

