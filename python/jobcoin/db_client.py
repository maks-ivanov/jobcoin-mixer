import sqlite3
from sqlite3 import Error
ADDRESS_TABLE_NAME = 'addresses'
DEPOSIT_ADDRESS_COLUMN_NAME = 'DEPOSIT_ADDRESS'
RETURN_ADDRESS_COLUMN_NAME = 'RETURN_ADDRESS'
DB_FILE = './jobcoin_db.sqlite'

class DbClient:
    def delete_tables(self, tables, db_file=DB_FILE):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        for table in tables:
            c.execute('DROP TABLE IF EXISTS %s' % table)
        conn.close()

    def create_address_table(self, db_file=DB_FILE):
        try:
            q = 'CREATE TABLE IF NOT EXISTS %s (%s TEXT NOT NULL, %s TEXT UNIQUE NOT NULL);' % (ADDRESS_TABLE_NAME, DEPOSIT_ADDRESS_COLUMN_NAME, RETURN_ADDRESS_COLUMN_NAME)
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute(q)
            c.close()
        except Error as e:
            print(e)

    def insert_addresses(self, deposit_address, return_addresses, db_file=DB_FILE):
        try:
            if self.check_address_in_table(deposit_address):
                print('Address is already allocated')
                return False

            rows = [(deposit_address, return_address) for return_address in return_addresses]
            q = 'INSERT INTO %s values (?,?)' % ADDRESS_TABLE_NAME
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.executemany(q, rows)
            conn.commit()
            conn.close()
            return True
        except Error as e:
            print(e)
            return False

    def check_address_in_table(self, deposit_address, db_file=DB_FILE):
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        q = 'SELECT DISTINCT %s FROM %s WHERE %s = \"%s\";' % (DEPOSIT_ADDRESS_COLUMN_NAME, ADDRESS_TABLE_NAME, DEPOSIT_ADDRESS_COLUMN_NAME, deposit_address)
        c.execute(q)
        existing_deposit_address = c.fetchall()
        exists = len(existing_deposit_address) > 0
        if exists:
            conn.close()
            return exists
        q = 'SELECT DISTINCT %s FROM %s WHERE %s = \"%s\";' % (RETURN_ADDRESS_COLUMN_NAME, ADDRESS_TABLE_NAME, RETURN_ADDRESS_COLUMN_NAME, deposit_address)
        c.execute(q)
        existing_deposit_address = c.fetchall()
        exists = len(existing_deposit_address) > 0
        conn.close()
        return exists

    def get_return_addresses(self, deposit_address, db_file=DB_FILE):
        try:
            q = 'SELECT %s FROM %s WHERE %s = \"%s\";' % (RETURN_ADDRESS_COLUMN_NAME, ADDRESS_TABLE_NAME, DEPOSIT_ADDRESS_COLUMN_NAME, deposit_address)
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute(q)
            rows = c.fetchall()
            conn.close()
            return [str(row[0]) for row in rows]
        except Error as e:
            print(e)

    def get_deposit_address(self, return_address='', db_file=DB_FILE):
        if return_address != '':
            q = 'SELECT %s FROM %s WHERE %s = \"%s\";' % (DEPOSIT_ADDRESS_COLUMN_NAME, ADDRESS_TABLE_NAME, RETURN_ADDRESS_COLUMN_NAME, return_address)
        else:
            q = 'SELECT %s FROM %s;' % (DEPOSIT_ADDRESS_COLUMN_NAME, ADDRESS_TABLE_NAME)
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute(q)
        rows = c.fetchall()
        conn.close()
        return [str(row[0]) for row in rows]