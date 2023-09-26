import main
import unittest
import sqlite3
import requests
from unittest import mock
from unittest.mock import patch
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('MY_API_KEY')

db_path = './app_data/dbase.db'

my_api_key = api_key

class userTests(unittest.TestCase):

    test_telegram_id = 999999999999999999
    test_telegram_id_for_creation = 999999999999999991

    def setUp(self):#здесь он что-то создал
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY)')
        cursor.execute('INSERT INTO users (telegram_id) VALUES (?)', (self.test_telegram_id,))
        conn.commit()
        conn.close()
    
    def tearDown(self):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE telegram_id = ?', (self.test_telegram_id,))
        cursor.execute('DELETE FROM users WHERE telegram_id = ?', (self.test_telegram_id_for_creation,))
        conn.commit()
        conn.close()

    def testCheckUserExistance(self):#здесь проверил существование того, что создал
        user = main.User(self.test_telegram_id)
        result = user.checkUserRecord()
        self.assertEqual(result, self.test_telegram_id)

    def testCreateUser(self):#здесь он создал нового пользователя и проверил, что он есть в базе
        user = main.User(self.test_telegram_id_for_creation)
        result_creation = user.createUserRecord()
        result_check = user.checkUserRecord()
        self.assertEqual(result_check, self.test_telegram_id_for_creation)

class currencyTests(unittest.TestCase):
    
    test_cur_id_1 = "USD"
    test_cur_id_2 = "EUR"
    ret_value = {
    "Realtime Currency Exchange Rate": {
        "1. From_Currency Code": "USD",
        "2. From_Currency Name": "United States Dollar",
        "3. To_Currency Code": "EUR",
        "4. To_Currency Name": "Euro",
        "5. Exchange Rate": "0.93910000",
        "6. Last Refreshed": "2023-09-25 05:40:02",
        "7. Time Zone": "UTC",
        "8. Bid Price": "0.93908000",
        "9. Ask Price": "0.93913000"
    }}

    def testCheckCurrencyExistance(self):

       with mock.patch('requests.get') as mock_get:
             
            mock_response_success = mock.Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = self.ret_value

            mock_response_error= mock.Mock()
            mock_response_error.status_code = 404
            mock_response_error.json.return_value = None

            mock_get.return_value = mock_response_success
            result_success = main.curTocur(self.test_cur_id_1, self.test_cur_id_2)
            self.assertTrue(result_success, mock_get.return_value)

            mock_get.return_value = mock_response_error
            result_error = main.curTocur(self.test_cur_id_1, self.test_cur_id_2)
            self.assertFalse(result_error, mock_get.return_value)


class CurrencyTests(unittest.TestCase):
    
    test_cur_id = "USD"
    test_date = "23/09/2023"
    ret_value = """
    <ValCurs Date="23.09.2023" name="Foreign Currency Market">
        <Valute ID="R01235">
            <NumCode>840</NumCode>
            <CharCode>USD</CharCode>
            <Nominal>1</Nominal>
            <Name>Доллар США</Name>
            <Value>96,0419</Value>
        </Valute>
    </ValCurs>
"""

    def testCheckCurrencyExistance(self):

       with mock.patch('requests.get') as mock_get:
            mock_response_success = mock.Mock()
            mock_response_success.status_code = 200
            mock_response_success.text = self.ret_value

            mock_response_error= mock.Mock()
            mock_response_error.status_code = 404
            mock_response_error.text = None

            mock_get.return_value = mock_response_success
            result = main.checkCurrency(self.test_date, self.test_cur_id)
            self.assertEqual(result, 96.04)

            mock_get.return_value = mock_response_error
            result_error = main.curTocur(self.test_date, self.test_cur_id)
            self.assertFalse(result_error, mock_get.return_value)


if __name__ == '__main__':
        unittest.main()
