import unittest

import pandas as pd

from rest import (OdooAPIKey, ContactClient, SalesOrderClient,
                  ProductClient, ProductTemplateClient, OdooWarehouseClient,
                  OdooWarehouseOperation)
import warnings
import dotenv
# 调整显示选项
pd.set_option('display.max_columns', None)  # 显示所有列
pd.set_option('display.max_colwidth', None)  # 不限制列宽
pd.set_option('display.width', 1000)  # 增加总宽度

env_path = "conf/.env"
dotenv.load_dotenv(env_path)
key = OdooAPIKey.test()

class TestOdooAPI(unittest.TestCase):


    def test_ContactClient(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        client = ContactClient(key)
        ids = client.fetch_ids()
        print(ids)
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)

        id = ids[0:1]
        details = client.fetch_contact_details(id)
        print(details)
        self.assertIsInstance(details, list)

        customer_ids = client.fetch_customer_ids()
        print(customer_ids)
        self.assertIsInstance(customer_ids, list)
        self.assertGreater(len(customer_ids), 0)

        vendor_ids = client.fetch_vendor_ids()
        print(vendor_ids)
        self.assertIsInstance(vendor_ids, list)
        self.assertGreater(len(vendor_ids), 0)



    def test_ProductClient(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        client = ProductTemplateClient(key)
        ids = client.fetch_template_ids()
        print(ids)
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)

        details = client.fetch_template_details(ids[0:5])
        self.assertIsInstance(details, list)
        self.assertIsInstance(details[0]['id'], int)


        for detail in details:
            print(detail)

        client = ProductClient(key)
        ids = client.fetch_product_ids()
        print(ids)
        details = client.fetch_product_details(ids[0:5])
        self.assertIsInstance(details, list)
        self.assertIsInstance(details[0]['id'], int)

        for detail in details:
            print(detail)

        pricelist_details = client.fetch_pricelist_details()
        print(pricelist_details)
        self.assertIsInstance(pricelist_details, list)
        self.assertIsInstance(pricelist_details[0]['id'], int)
        for detail in pricelist_details:
            print(detail)

        item_ids = client.fetch_pricelist_item_ids(pricelist_details[0]['id'])
        print(item_ids)
        self.assertIsInstance(item_ids, list)

        item_details = client.fetch_pricelist_item_details(item_ids)
        print(item_details)
        self.assertIsInstance(item_details, list)
        self.assertIsInstance(item_details[0]['id'], int)
        for detail in item_details:
            print(detail)

    def test_SalesOrderClient(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        client = SalesOrderClient(key)
        ids = client.fetch_ids()
        print(ids)
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)

        write_dates = client.fetch_order_write_date(ids)
        print(write_dates)
        self.assertIsInstance(write_dates, list)
        self.assertIsInstance(write_dates[0]['write_date'], str)


        details = client.fetch_order_details(ids[0:5])
        self.assertIsInstance(details, list)
        self.assertIsInstance(details[0]['id'], int)

        for detail in details:
            print(detail)
            orderline_ids = detail['order_line']
            orderline_details = client.fetch_order_line_details(orderline_ids)
            self.assertIsInstance(orderline_details, list)
            self.assertIsInstance(orderline_details[0]['id'], int)
            for line_detail in orderline_details:
                print(line_detail)


    def test_OdooWarehouseClient(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        client = OdooWarehouseClient(key)
        ids = client.fetch_location_ids()
        print(ids)
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)
        ids = client.fetch_putaway_rules_ids()
        print(ids)
        details = client.fetch_putaway_rules_details(ids)
        print(details)
        self.assertIsInstance(details, list)
        self.assertIsInstance(details[0]['id'], int)



        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)
        ids = client.fetch_quant_ids()
        print(ids)
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)



    def test_OdooWarehouseOperation(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        operation = OdooWarehouseOperation(key)
        operation.list_quants_to_show()
        print("Test Relocate Quants to Putaway Location")
        stock_to_move = operation.find_quants_match_putaway_rules()
        # operation.relocate_quants_to_putaway_location(stock_to_move)

        operation.list_products_to_show()





if __name__ == "__main__":
    unittest.main()
