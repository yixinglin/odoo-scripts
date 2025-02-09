import json
import os
import re
import time
import xmlrpc.client
from copy import copy
from datetime import datetime
from typing import List, Union
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

from schemas import StockToMove, QuantVO, ProductVO

DATETIME_PATTERN = '%Y-%m-%d %H:%M:%S'
DATE_PATTERN = '%Y-%m-%d'


def now():
    return datetime.now().strftime(DATETIME_PATTERN)


def today():
    return datetime.now().strftime(DATE_PATTERN)

class OdooAPIKey(BaseModel):
    alias: str
    db: str
    username: str
    password: str
    host: str

    @classmethod
    def test(cls):
        load_dotenv()
        index = int(os.getenv("ODOO_ACCESS_KEY_INDEX"))
        key_path = os.getenv("ODOO_ACCESS_KEY")
        with open(f"conf/{key_path}", "r") as f:
            conf = json.load(f)['keys'][index]
            key = cls(**conf)
        return key

    @classmethod
    def prod(cls):
        load_dotenv()
        index = int(os.getenv("ODOO_ACCESS_KEY_INDEX"))
        key_path = os.getenv("ODOO_ACCESS_KEY")
        with open(f"conf/{key_path}", "r") as f:
            conf = json.load(f)['keys'][1]
            key = cls(**conf)
        return key

class OdooClient(object):

    def __init__(self, api_key: OdooAPIKey):
        self.api_key = api_key
        self.db = api_key.db
        self.username = api_key.username
        self.password = api_key.password
        self.host = api_key.host
        self.uid = None
        self.models = None

    def login(self):
        print("Odoo API Login")
        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.host), allow_none=True)
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.host), allow_none=True)
        return self

    def version(self):
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.host))
        return common.version()

    def execute_kw(self, model, method, *args, **kwargs):
        return self.models.execute_kw(self.db, self.uid, self.password,
                                      model, method, *args, **kwargs)

    def search_read(self, model, *args, **kwargs):
        return self.execute_kw(model,'search_read', *args, **kwargs)

    def search(self, model, *args, **kwargs):
        return self.execute_kw(model,'search', *args, **kwargs)

    def read(self, model, *args, **kwargs):
        return self.execute_kw(model,'read', *args, **kwargs)

    def create(self, model, *args, **kwargs):
        return self.execute_kw(model, 'create', *args, **kwargs)

    def write(self, model, *args, **kwargs):
        return self.execute_kw(model, 'write', *args, **kwargs)


class OdooAPIBase(object):

    def __init__(self, api_key: OdooAPIKey, login=True, *args, **kwargs):
        self.api_key = api_key
        self.client = OdooClient(self.api_key)
        if login:
            self.client.login()

    @classmethod
    def from_client(cls, client: OdooClient):
        """ 从已登录的 OdooClient 创建 OdooAPIBase """
        api = cls(client.api_key, login=False)
        api.client = client
        return api

    def login(self):
        self.client.login()

    def get_username(self):
        return self.api_key.username

    def get_alias(self):
        return self.api_key.alias

    def version(self):
        return self.client.version()

    def fetch_write_date(self, model, ids, *args, **kwargs):
        return self.client.read(model, [ids], {'fields': ['id', 'write_date']})


""" 
product.template 产品模版
product.product 产品变体
"""
class ProductClient(OdooAPIBase):
    _model_product = 'product.product'
    _fields_product = ['id', 'name', 'list_price', 'default_code', 'description', 'categ_id', 
               'avg_cost', 'barcode', 'standard_price', 'taxes_id', 'write_date', 'qty_available', 'active',
               'product_variant_count', 'product_variant_ids', 'product_variant_id', 'sales_count']
    
    _model_pricelist = 'product.pricelist'
    _fields_pricelist =  ['id', 'name', 'active', 'company_id'] #'product_id', 

    _model_pricelist_item = 'product.pricelist.item'
    _fields_pricelist_item = ['id', 'product_tmpl_id', 'product_id', 'pricelist_id', 'fixed_price', 'min_quantity']

    def __init__(self, api_key: OdooAPIKey,*args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_product_ids(self):
        """
        获取产品ID列表
        :param domain: 搜索条件
        :return: 产品ID列表
        """
        domain = [            
            ('active', '=', True),
            ('product_variant_count', '=', 1)
        ]
        product_ids = self.client.search(self._model_product,[domain])  # Search Domain
        return product_ids

    def fetch_product_details(self, product_ids):
        """
        获取产品详情
        :param product_ids: 产品ID列表
        :return: 产品详情列表
        """
        details = self.client.read(self._model_product, [product_ids], {"fields": self._fields_product})
        return details

    def fetch_pricelist_details(self):
        """
        获取产品价格列表
        :param product_ids: 产品ID列表
        :return: 产品价格列表
        """
        domain = [
            ('active', '=', True)
        ]
        details = self.client.search_read(self._model_pricelist, [domain], 
                                          {"fields": self._fields_pricelist})  
        return details

    def fetch_pricelist_item_ids(self, pricelist_id):
        """
        获取产品价格列表的item_ids
        :param pricelist_id: 产品价格列表ID
        :return: 产品价格列表的item_ids
        """
        domain = [
            ('pricelist_id', '=', pricelist_id)
        ]
        details = self.client.search(self._model_pricelist_item, [domain],)
        return details

    def fetch_pricelist_item_details(self, pricelist_item_ids):
        """
        获取产品价格列表的item_ids
        :param pricelist_item_ids: 产品价格列表的item_ids
        :return: 产品价格列表的item_ids
        """
        details = self.client.read(self._model_pricelist_item, [pricelist_item_ids], 
                                   {"fields": self._fields_pricelist_item})
        return details


class ProductTemplateClient(OdooAPIBase):
    _model = 'product.template'
    _fields = ['id', 'default_code', 'write_date', 'product_variant_count',
               'product_variant_ids', 'product_variant_id']

    def __init__(self, api_key: OdooAPIKey,*args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_template_ids(self):
        """
        获取产品模版ID列表
        :param domain: 搜索条件
        :return: 产品模版ID列表
        """
        domain = [
            # ['team_id', '=', 5],
            ('active', '=', True),
           ('product_variant_count', '=', 1)
        ]
        product_ids = self.client.search(self._model, [domain])  # Search Domain
        return product_ids

    def fetch_template_details(self, product_ids):
        """
        获取产品模版详情
        :param product_ids: 产品模版ID列表
        :return: 产品模版详情列表
        """
        details = self.client.read(self._model, [product_ids], {"fields": self._fields})
        return details


class ContactClient(OdooAPIBase):

    _model = "res.partner"
    _fields = ['id', 'name', 'email', 'phone']

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_ids(self):
        print("Fetching contact ids...")
        product_ids = self.client.search(self._model, [[]])
        return product_ids

    def fetch_customer_ids(self):
        print("Fetching customer ids...")
        domain = [
            ('customer_rank', '>=', 1)
        ]
        customer_ids = self.client.search(self._model, [domain])
        return customer_ids

    def fetch_vendor_ids(self):
        print("Fetching vendor ids...")
        domain = [
            ('supplier_rank', '>=', 1)
        ]
        vendor_ids = self.client.search(self._model, [domain])
        return vendor_ids

    def fetch_contact_details(self, contact_ids):
        print("Fetching contact details...")
        contact_details = self.client.read(self._model, contact_ids, {"fields": self._fields})
        return contact_details



class SalesOrderClient(OdooAPIBase):
    _model = "sale.order"
    _fields = ['id', 'name', 'date_order', 'partner_id', "state", 'amount_total',
               'partner_invoice_id', 'partner_shipping_id',  'order_line']
    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_ids(self):
        print("Fetching sale order ids...")
        sale_order_ids = self.client.search(self._model, [[]])
        return sale_order_ids

    def fetch_order_details(self, sale_order_ids):
        print("Fetching sale order details...")
        order_details = self.client.read(self._model,
                                         [sale_order_ids], {"fields": self._fields})
        return order_details

    def fetch_order_line_details(self, order_line_ids):
        print("Fetching sale order line details...")
        _fields2 = ["id", "product_id", "price_unit", "product_uom_qty", "product_uom"]
        order_line_details = self.client.read("sale.order.line",
                                              [order_line_ids],
                                              {"fields": _fields2})
        return order_line_details

    def fetch_order_write_date(self, sale_order_ids):
        print("Fetching sale order write date...")
        order_write_date = self.client.read(self._model, [sale_order_ids], {"fields": ["id", "write_date"]})
        return order_write_date

    def create_order(self, quot_data):
        print("Creating sale order...")
        order_id = self.client.create(self._model, quot_data)
        return order_id

    @staticmethod
    def make_quot_data():
        print("Making quotation data...")
        quotation_data = {
            'partner_id': 1632,  # 客户ID（必填）
            'order_line': [],  # 订单行信息（稍后添加）
        }
        # 设置订单行信息
        order_line_data = [
            (0, 0, {
                'product_id': 885,  # 产品ID（必填）
                'product_uom_qty': 2,  # 产品数量
                'price_unit': 100.0,  # 单价
            }),
            (0, 0, {
                'product_id': 881,  # 产品ID（必填）
                'product_uom_qty': 3,  # 产品数量
                'price_unit': 150.0,  # 单价
            }),
        ]
        quotation_data['order_line'] = order_line_data
        return quotation_data



class OdooWarehouseClient(OdooAPIBase):
    _model_location = "stock.location"
    _location_fields = ["id", "name", "active", "usage"]
    _model_quant = "stock.quant"
    _quant_fields = ["id", "product_id", "location_id", "quantity", "warehouse_id", 
                      "reserved_quantity", "available_quantity", "product_uom_id"]
    _model_putaway = "stock.putaway.rule"    
    _putaway_fields = ["id","active", "product_id", "location_in_id", "location_out_id", "write_date"]

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        super().__init__(api_key, *args, **kwargs)

    def fetch_putaway_rules_ids(self):
        print("Fetching putaway rules ids...")
        putaway_rules_ids = self.client.search(self._model_putaway, [[]])
        return putaway_rules_ids

    def fetch_putaway_rules_details(self, putaway_rules_ids):
        print("Fetching putaway rules details...")
        putaway_rules_details = self.client.read(self._model_putaway, [putaway_rules_ids],
                                                 {"fields": self._putaway_fields})
        return putaway_rules_details

    def fetch_location_ids(self):
        print("Fetching location ids...")
        location_ids = self.client.search(self._model_location, [[]])
        return location_ids

    def fetch_location_ids_by_complete_name(self, complete_name):
        print("Fetching location ids by complete name...")
        domain = [
            ('complete_name', 'ilike', complete_name)
        ]
        location_ids = self.client.search(self._model_location, [domain])
        return location_ids

    def fetch_location_details(self, location_ids):
        print("Fetching location details...")
        location_details = self.client.read(self._model_location, [location_ids],
                                             {"fields": self._location_fields})
        return location_details

    def fetch_quant_ids(self):
        print("Fetching quant ids...")
        domain = [('location_id', 'ilike', "WH/Stock"),  # contains WH/Stock
        ]
        quant_ids = self.client.search(self._model_quant, [domain])
        return quant_ids

    def fetch_quant_details(self, quant_ids):
        print("Fetching quant details...")
        quant_details = self.client.read(self._model_quant, [quant_ids], {"fields": self._quant_fields})
        return quant_details
    
    def fetch_quant_details_by_product_location(self, product_id, location_id):
        print("Fetching quant details by product and location...")
        domain = [
            ('product_id', '=', product_id),
            ('location_id', '=', location_id)
        ]
        quant_ids = self.client.search_read(self._model_quant, [domain], {"fields": self._quant_fields})
        return quant_ids

    def fetch_quant_details_by_products_locations(self, product_ids, location_ids):
        print("Fetching quant details by products and locations...")
        if not product_ids or not location_ids or len(product_ids) != len(location_ids):
            raise ValueError("Array product_ids and location_ids must be non-empty and have the same length!")
        domain = []
        for i in range(len(product_ids)):            
            sub_condition = ['&', ('product_id', '=', product_ids[i]), ('location_id', '=', location_ids[i])]            
            if domain:
                domain = ['|'] + domain + sub_condition
            else:
                domain = sub_condition
        quant_ids = self.client.search_read(self._model_quant, [domain], {"fields": self._quant_fields})
        return quant_ids
    

    def relocate_quant(self, quant_id, location_id):
        print(f"Relocating quant {quant_id} to location {location_id}...")
        self.client.write(self._model_quant, [[quant_id], {'location_id': location_id}])


def save_dataframe_to_temp(df, file_name):
    if not os.path.exists("temp"):
        os.makedirs("temp")
    fname = f"temp/{file_name}.xlsx"
    df.to_excel(fname, index=False)
    print(f"Saved to {fname}")
    return fname

class OdooWarehouseOperation:

    def __init__(self, api_key: OdooAPIKey, *args, **kwargs):
        self.wh_client = OdooWarehouseClient(api_key, login=True)
        self.product_client = ProductClient.from_client(self.wh_client.client)

    def find_quants_match_putaway_rules(self) -> List[StockToMove]:
        """
        寻找存在上架规则，却没有上架的产品的库存记录
        """
        putaway_rules_ids = self.wh_client.fetch_putaway_rules_ids()
        print(f"Found {len(putaway_rules_ids)} putaway rules")
        rules = self.wh_client.fetch_putaway_rules_details(putaway_rules_ids)
        dict_rules = {}
        for rule in rules:
            key = f"{rule['product_id'][0]}_{rule['location_in_id'][0]}"
            dict_rules[key] = rule

        stock_to_move: List[StockToMove] = []
        product_ids = [rule['product_id'][0] for rule in rules]
        location_in_ids = [rule['location_in_id'][0] for rule in rules]
        location_out_ids = [rule['location_out_id'][0] for rule in rules]
        quants = self.wh_client.fetch_quant_details_by_products_locations(product_ids, location_in_ids)
        # quants2 = self.wh_client.fetch_quant_details_by_products_locations(product_ids, location_out_ids)
        for quant in quants:
            quant_id = quant['id']
            quant_quantity = quant['quantity']
            rule = dict_rules.get(f"{quant['product_id'][0]}_{quant['location_id'][0]}")
            stock_to_move.append(StockToMove(
                product_id=rule['product_id'][0],
                product_name=rule['product_id'][1],
                location_in_id=rule['location_in_id'][0],
                location_in_name=rule['location_in_id'][1],
                location_out_id=rule['location_out_id'][0],
                location_out_name=rule['location_out_id'][1],
                quant_id=quant_id,
                quant_quantity=quant_quantity
            ))

        print(f"++ Matched {len(stock_to_move)} stocks to move")
        stock_to_move = [move for move in stock_to_move if int(move.quant_quantity) != 0]
        print(f"-- Filtered out {len(stock_to_move)} with 0 quantities...")
        if stock_to_move is not None and len(stock_to_move) == 0:
            print("No quants to move!")
            return []

        df = pd.DataFrame.from_dict([move.model_dump() for move in stock_to_move])
        print(f"Found {len(stock_to_move)} stock to move")
        df_dropped = copy(df[['product_name', 'location_in_name', 'location_out_name', 'quant_quantity']])
        df_dropped['location_out_name'] = df_dropped['location_out_name'].map(lambda x: x.split('/')[-1])
        df_dropped['product_name'] = df_dropped['product_name'].map(lambda x: x.split(' ')[0])
        print(df_dropped)
        fname = save_dataframe_to_temp(df, "stock_to_move")
        return stock_to_move

    
    def relocate_quants_to_putaway_location(self, quants_to_move: List[StockToMove]):
        for quant in quants_to_move:
            self.wh_client.relocate_quant(quant.quant_id, quant.location_out_id)
            print(f"Relocated {quant}")
            time.sleep(1)
    

    def list_quants_to_show(self) -> List[QuantVO]:
        quant_ids = self.wh_client.fetch_quant_ids()
        quants = self.wh_client.fetch_quant_details(quant_ids)        
        quant_to_show: List[QuantVO] = []
        for item in quants:
            quant_to_show.append(QuantVO(
                product_id=item['product_id'][0],
                product_name=item['product_id'][1],
                location_id=item['location_id'][0],
                location_name=item['location_id'][1],
                product_uom=item['product_uom_id'][1],
                warehouse_name=item['warehouse_id'][1],
                quantity=item['quantity'],
                available_quantity=item['available_quantity']
            ))
        quants_to_show = sorted(quant_to_show, key=lambda x: x.product_name)
        df = pd.DataFrame.from_dict([quant.model_dump() for quant in quants_to_show])
        print(f"Found {len(quants_to_show)} quants to show")
        df_dropped = copy(df[['product_name', 'location_name', 'warehouse_name', 'quantity', 'available_quantity']]) 
        df_dropped['location_name'] = df_dropped['location_name'].map(lambda x: x.split('/')[-1])
        df_dropped['product_name'] = df_dropped['product_name'].map(lambda x: x.split(' ')[0])
        print(df_dropped)
        fname = save_dataframe_to_temp(df, "quants_to_show")
        return quants_to_show
    



    def list_products_to_show(self):
        product_ids = self.product_client.fetch_product_ids()
        products = self.product_client.fetch_product_details(product_ids)
        print(f"Found {len(products)} products...")
        product_vo_list: List[ProductVO] = []
        for product in products:
            product_vo = ProductVO(
                id=product['id'],
                name=product['name'],
                list_price=product['list_price'],
                default_code= "" if product['default_code'] == False else product['default_code'],
                barcode= "" if product['barcode'] == False else product['barcode'],
                standard_price=product['standard_price'],
                write_date=product['write_date'],
                active=product['active'],
                qty_available=product['qty_available']
            )
            product_vo_list.append(product_vo)
        product_vo_list = list(filter(lambda x: x.active == True, product_vo_list))
        print(f"Found {len(product_vo_list)} active products...")
        df = pd.DataFrame.from_dict([product.model_dump() for product in product_vo_list])
        df_droped = copy(df[['name', 'default_code', 'barcode', 'list_price','standard_price', 'qty_available']])
        df_droped['name'] = df_droped['name'].map(lambda x: x.split(' ')[0])
        print(df_droped)
        fname = save_dataframe_to_temp(df, "products_to_show")
        return product_vo_list


class PricelistItem(BaseModel):
    id: int
    pricelist_id: int
    pricelist_name: str
    company_id: int
    company_name: str
    fixed_price: float
    name: str
    currency: str
    min_quantity: int
    product_tmpl_id: int
    product_tmpl_name: str
    default_code: str
    product_id: Union[int, None]
    product_name: Union[str, None]

# --------------- #
# 核心类及方法定义 #
# --------------- #
class OdooPricelistOperation:
    def __init__(self, api_key: 'OdooAPIKey', debug: bool = False):
        """
        :param api_key: OdooAPIKey 对象，用于认证和连接 Odoo
        :param debug: 是否处于调试模式。若为 True 则不会实际执行写入/创建操作
        """
        self.product_templ_client = ProductTemplateClient(api_key, login=True)
        self.client = self.product_templ_client.client
        self.debug = debug

    # ----------------------- #
    #  主入口：更新价格表条目  #
    # ----------------------- #
    def update_price_list_item(self) -> List[str]:
        """
        从本地读取 VIP 价格表数据，与 Odoo 中的价格表做对比，创建或更新对应的 price_list_item。
        :return: 未能在 Odoo 找到对应product template 的 internal_reference 列表
        """
        # 1. 读取 & 预处理 VIP 数据
        input("请确认VIP价格表数据已经保存到 temp/vip_price.json，然后按任意键继续...")
        df_vip_prices = self._load_and_preprocess_vip_data('temp/vip_price.json')

        # 2. 获取所有在VIP中的价格表名称
        vip_pricelist_names = df_vip_prices['group_name'].unique().tolist()
        print(f"[VIP] Total number of groups: {len(vip_pricelist_names)}")
        for i, name in enumerate(vip_pricelist_names, start=1):
            print(f"{i}. {name}")
        input("请确认VIP价格表名称，然后按任意键继续...")

        # 3. 从Odoo读取这些价格表信息
        pricelist_details = self._get_odoo_pricelist_details(vip_pricelist_names)
        vip_pricelist_names_in_odoo = [pl['name'] for pl in pricelist_details]
        vip_pricelist_names_not_in_odoo = [name for name in vip_pricelist_names if name not in vip_pricelist_names_in_odoo]

        print(f"VIP pricelist names in Odoo: {len(vip_pricelist_names_in_odoo)}")
        print(f"VIP pricelist names not in Odoo: {len(vip_pricelist_names_not_in_odoo)}")
        for i, name in enumerate(vip_pricelist_names_not_in_odoo, start=1):
            print(f"\t{i}. {name}")
        input("请确认以上价格表名称，然后按任意键继续...")

        # 4. 获取 Odoo pricelist item 与 product.template 信息
        pricelist_items = self._get_odoo_pricelist_items(vip_pricelist_names_in_odoo)
        product_templates_map = self._get_odoo_product_templates()

        # 5. 对比 VIP 与 Odoo 数据，并输出对比结果
        df_compare = self._compare_vip_and_odoo_pricelist(df_vip_prices, pricelist_items, vip_pricelist_names_in_odoo)
        df_compare.to_excel('temp/vip_odoo_pricelist_items.xlsx', index=False)
        print(f"文件已经保存到 temp/vip_odoo_pricelist_items.xlsx")
        input("请检查文件内容，确认无误后按任意键继续...")

        # 6. 更新 & 创建 Pricelist item
        print(f"注意: 以下操作将会改变Odoo数据库，请确认是否执行！！！！！！！")
        confirmed = input("确认请输入Y，否则请按任意键退出...")
        if confirmed.lower() != 'y':
            print("操作已取消，退出...")
            return []

        products_not_found = []
        products_not_found += self._update_pricelist_items(df_compare)
        products_not_found += self._create_pricelist_items(df_compare, product_templates_map, pricelist_details)

        print(f"Total number of products not found: {len(products_not_found)}")
        print(products_not_found)
        return products_not_found

    # ------------------------------- #
    #         私有方法: 读取VIP数据    #
    # ------------------------------- #
    def _load_and_preprocess_vip_data(self, file_path: str) -> pd.DataFrame:
        """从指定JSON文件加载数据，并做字段预处理，返回DataFrame。"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)['data']

        df = pd.DataFrame.from_dict(data)
        # 正则匹配 article_number => (internal_reference, size)
        pattern = r"^(.*?)(PK\d+)$"

        df['internal_reference'] = df['article_number'].str.extract(pattern, expand=False)[0]
        df['sales_units'] = df['article_number'].str.extract(pattern, expand=False)[1].str.replace('PK', '')
        df['internal_reference'] = df['internal_reference'].fillna(df['article_number'])
        df['sales_units'] = df['sales_units'].fillna(1)

        # 数量转为 int，并据此折算单价
        df['min_quantity'] = df['sales_units'].astype(int)
        df['custom_price'] = df['custom_price'] / df['min_quantity']
        df['std_price_a'] = df['std_price_a'] / df['min_quantity']
        df['std_price_b'] = df['std_price_b'] / df['min_quantity']

        # 构造 key 方便后续 merge
        df.drop(columns=['article_number'], inplace=True)
        df['key'] = df['group_name'] + '_' + df['internal_reference'].astype(str)

        # 排序 & 重置索引
        df.sort_values(by='group_name', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    # --------------------------------------------------- #
    #    私有方法: 获取Odoo中已有的 pricelist 相关信息      #
    # --------------------------------------------------- #
    def _get_odoo_pricelist_details(self, vip_pricelist_names: List[str]) -> List[dict]:
        """从Odoo 'product.pricelist' 获取指定名称的价格表详细信息。"""
        domain = [('name', 'in', [name.strip() for name in vip_pricelist_names])]
        pricelist_ids = self.client.search('product.pricelist', [domain], {})
        pricelist_details = self.client.read('product.pricelist', [pricelist_ids],
                                            {'fields': ['id', 'name', 'active']})
        print(f"[Odoo] Found {len(pricelist_details)} matching pricelists in Odoo.")
        return pricelist_details

    def _get_odoo_pricelist_items(self, pricelist_names_in_odoo: List[str]) -> List[PricelistItem]:
        """
        从 Odoo 中拉取指定价格表的 pricelist.item 列表，转换为 PricelistItem 对象列表。
        :return: PricelistItem 对象列表
        """
        if not pricelist_names_in_odoo:
            print("[Odoo] No pricelist to retrieve items from.")
            return []

        domain = [('name', 'in', pricelist_names_in_odoo)]
        fields = ["id", "company_id", "pricelist_id", "fixed_price", "name", "currency_id",
                  "min_quantity", "product_tmpl_id", "product_id"]
        pricelist_item_data = self.client.search_read('product.pricelist.item', [domain], {"fields": fields})
        print(f"[Odoo] Found {len(pricelist_item_data)} pricelist items in Odoo.")

        pricelist_items: List[PricelistItem] = []
        for item in pricelist_item_data:
            # 从 product_tmpl_id 名称中提取 [default_code]
            product_tmpl_label = item['product_tmpl_id'][1] if item['product_tmpl_id'] else ''
            match = re.search(r'\[(.*?)\]', product_tmpl_label)
            default_code = match.group(1) if match else ""

            # 组装 PricelistItem 对象
            pricelist_items.append(PricelistItem(
                id=item['id'],
                pricelist_id=item['pricelist_id'][0],
                pricelist_name=item['pricelist_id'][1].replace('(EUR)', '').strip(),
                company_id=item['company_id'][0],
                company_name=item['company_id'][1],
                fixed_price=item['fixed_price'],
                name=item['name'],
                currency=item['currency_id'][1],
                min_quantity=item['min_quantity'],
                product_tmpl_id=item['product_tmpl_id'][0] if item['product_tmpl_id'] else 0,
                product_tmpl_name=product_tmpl_label,
                default_code=default_code,
                product_id=item['product_id'][0] if item['product_id'] else None,
                product_name=item['product_id'][1] if item['product_id'] else None
            ))
        return pricelist_items

    def _get_odoo_product_templates(self) -> dict:
        """
        从 Odoo 读取所有激活的 product.template，并返回 {default_code: product_template_dict} 映射。
        """
        domain = [('active', '=', True)]
        product_templates = self.client.search_read('product.template', [domain],
                                                    {'fields': ['id', 'name', 'default_code']})
        print(f"[Odoo] Found {len(product_templates)} active product templates.")
        return {pt['default_code']: pt for pt in product_templates if pt['default_code']}

    # -------------------------------------------------- #
    #    私有方法: 对比VIP与Odoo数据，标记 create/update    #
    # -------------------------------------------------- #
    def _compare_vip_and_odoo_pricelist(
        self,
        df_vip_prices: pd.DataFrame,
        pricelist_items: List[PricelistItem],
        pricelist_names_in_odoo: List[str],
    ) -> pd.DataFrame:
        """
        将 VIP 的价格表信息与 Odoo 中的 pricelist item 合并对比，
        标记出需要 create 的行和需要 update 的行。
        :return: 结果 DataFrame，含 'action' 列（create/update）
        """
        # 先把 Odoo item 转成 DF
        df_odoo_pricelist_items = pd.DataFrame.from_records(
            [item.model_dump() for item in pricelist_items]
        )
        df_odoo_pricelist_items['key'] = (
            df_odoo_pricelist_items['pricelist_name']
            + '_'
            + df_odoo_pricelist_items['default_code']
        )

        # 内连接: key
        df_merged = df_vip_prices.merge(df_odoo_pricelist_items, on='key', how='left', suffixes=('_vip','_odoo'))

        # 只保留那些在 Odoo 中确实存在的 pricelist
        df_filtered = df_merged[df_merged['group_name'].isin(pricelist_names_in_odoo)].copy()

        # 标记 action: 如果 pricelist_id（来自 Odoo）为空 => create，否则 update
        df_filtered['action'] = df_filtered['pricelist_id'].isna().map({True: 'create', False: 'update'})

        return df_filtered

    # -------------------------------------------------- #
    #            私有方法: 更新已有的pricelist.item       #
    # -------------------------------------------------- #
    def _update_pricelist_items(self, df_compare: pd.DataFrame) -> List[str]:
        """
        对于已存在的 pricelist item，更新其 fixed_price, min_quantity 等。
        :return: 未找到产品列表（此处一般不会新增此列表，仅占位）
        """
        df_update = df_compare[df_compare['action'] == 'update'].copy()
        print(f"[Update] Number of pricelist items to update: {len(df_update)}")

        for i, row in enumerate(df_update.itertuples(), start=1):
            pricelist_item_id = int(row.id) if pd.notna(row.id) else None
            if not pricelist_item_id:
                continue  # 无效行（一般不会发生）

            update_vals = {
                'fixed_price': row.custom_price,
                'min_quantity': row.min_quantity_vip,
                'compute_price': 'fixed',
            }
            print(f"{i}. Updating pricelist item ID={pricelist_item_id} in {row.group_name}")
            print(f"    => {update_vals}")

            if not self.debug:
                self.client.write('product.pricelist.item', [[pricelist_item_id], update_vals])
                time.sleep(0.2)
        return []  # 该步骤不产生products_not_found

    # -------------------------------------------------- #
    #            私有方法: 创建新的pricelist.item         #
    # -------------------------------------------------- #
    def _create_pricelist_items(
        self,
        df_compare: pd.DataFrame,
        product_templates_map: dict,
        pricelist_details: List[dict]
    ) -> List[str]:
        """
        对于在Odoo中尚不存在的 pricelist item 行，执行创建操作。
        :param df_compare: 包含了 action='create' 的行
        :param product_templates_map: {default_code: {id, name, default_code}}
        :param pricelist_details: Odoo pricelist信息，供 name->id 的映射
        :return: 未能找到 product.template 的 default_code 列表
        """
        df_create = df_compare[df_compare['action'] == 'create'].copy()
        print(f"[Create] Number of pricelist items to create: {len(df_create)}")

        # 建立 pricelist name -> pricelist_id 映射
        name_to_pricelist_obj = {detail['name']: detail for detail in pricelist_details}
        not_found_products = []

        for i, row in enumerate(df_create.itertuples(), start=1):
            ref_code = row.internal_reference
            group_name = row.group_name
            try:
                product_tmpl_obj = product_templates_map[ref_code]
            except KeyError:
                print(f"[Warning] Product template not found for '{ref_code}'")
                not_found_products.append(ref_code)
                continue

            pricelist_obj = name_to_pricelist_obj.get(group_name)
            if not pricelist_obj:
                print(f"[Warning] Pricelist not found in Odoo for '{group_name}'")
                continue

            new_item_vals = {
                'pricelist_id': pricelist_obj['id'],
                'product_tmpl_id': product_tmpl_obj['id'],
                'fixed_price': row.custom_price,
                'min_quantity': row.min_quantity_vip,
                'compute_price': 'fixed',
            }

            print(f"{i}. Creating item in Pricelist: {group_name} for product [{ref_code}]")
            print(f"    => {new_item_vals}")

            if not self.debug:
                self.client.create('product.pricelist.item', [new_item_vals])
                time.sleep(0.2)

        return not_found_products