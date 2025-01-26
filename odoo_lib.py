import re

from rest.base import OdooAPIKey, OdooAPIBase
import os
import pandas as pd

# 设置环境变量
os.environ['ODOO_ACCESS_KEY'] = 'odoo-api-prod.json'
os.environ['ODOO_ACCESS_KEY_INDEX'] = "0"

api_key = OdooAPIKey.prod()
base = OdooAPIBase(api_key)
cli = base.client


def __extract_internal_ref_from_product_name(product_name):
    # 正则表达式匹配中括号内的内容
    pattern = r'\[(.*?)\]'
    match = re.search(pattern, product_name)
    content = ""
    if match:
        content = match.group(1)
    else:
        print(f"No match found: {product_name}")
    return content


def fetch_all_sales__order_details():
    """
    获取所有销售订单及详情
    :return:
        1. 所有销售订单信息
        2. 所有销售订单对应的订单行ID
    """
    domain = [('user_id', 'not in', [8, 6])]
    order_ids = cli.search('sale.order', [domain])
    orders_ = cli.read('sale.order', [order_ids])
    sale_orders = []
    for od in orders_:
        so = dict(
            id=od['id'],
            name=od['name'],
            company=od['company_id'][1],
            partner=od['partner_id'][1],
            state=od['state'],
            date_order=od['date_order'],
            invoice_status=od['invoice_status'],
            shipping_weight=od['shipping_weight'],
            orderline_ids=od['order_line']
        )
        sale_orders.append(so)
    df_sale_order = pd.DataFrame.from_dict(sale_orders)

    orderline_ids = set()
    for od in orders_:
        orderline_ids.update(od['order_line'])
    orderline_ids = list(orderline_ids)
    return df_sale_order, orderline_ids


def fetch_sales_orderline_details(orderline_ids):
    fields = ['order_id', 'name', 'currency_id', 'order_partner_id', 'salesman_id', 'product_template_id',
              'state', 'product_uom', 'product_uom_qty', 'product_qty', 'price_unit',
              'price_subtotal', 'price_tax', 'price_total', 'qty_to_invoice', 'qty_to_deliver',
              'product_type', 'create_date', 'is_delivery', 'display_type', 'discount'
             ]
    # fields = []
    orderlines_ = cli.read('sale.order.line', [orderline_ids], {"fields": fields})
    orderlines = []

    for odl in orderlines_:
        if odl['display_type'] == 'line_note':
            continue
        try:
            line = {
                "order_number": odl['order_id'][1],  # 订单号
                "product_name": odl['product_template_id'][1],
                "product_id": odl['product_template_id'][0],
                "internal_reference": __extract_internal_ref_from_product_name(odl['product_template_id'][1]),
                "currency": odl['currency_id'][1],
                "order_partner": odl['order_partner_id'][1], # 客户
                "salesman": odl['salesman_id'][1], # 销售员
                'state': odl['state'],
                'uom': odl['product_uom'][1],  # 单位
                'product_uom_qty': odl['product_uom_qty'],   #product_qty
                'product_qty': odl['product_qty'],  # 数量
                'price_unit': odl['price_unit'],  # 单价
                'price_subtotal': odl['price_subtotal'], # 小计
                'price_tax': odl['price_tax'], # 含税
                'price_total': odl['price_total'], # 总计
                'qty_to_invoice': odl['qty_to_invoice'],
                'qty_to_deliver': odl['qty_to_deliver'],
                'product_type': odl['product_type'],
                'create_date': odl['create_date'],
                'is_delivery': odl['is_delivery'],
                'discount': odl['discount'],
            }
        except Exception as e:
            print(e)
            print(odl)
        orderlines.append(line)
    df_sale_order_lines = pd.DataFrame.from_dict(orderlines)
    df_sale_order_lines['create_date'] = pd.to_datetime(df_sale_order_lines['create_date'], format='%Y-%m-%d %H:%M:%S')
    df_sale_order_lines.sort_values(by='create_date', inplace=True)
    return df_sale_order_lines

def fetch_all_purchase_order_details():
    """
    """
    domain = [('partner_id', 'not in', [39, 316])]
    order_ids = cli.search('purchase.order', [domain])
    orders_ = cli.read('purchase.order', [order_ids])
    purchase_orders = []
    for od in orders_:
        so = dict(
            id=od['id'],
            name=od['name'],
            company=od['company_id'][1],
            partner=od['partner_id'][1],
            state=od['state'],
            date_order=od['date_order'],
            invoice_status=od['invoice_status'],
            # shipping_weight = od['shipping_weight'],
            orderline_ids=od['order_line']
        )
        purchase_orders.append(so)
    df_purchase_orders = pd.DataFrame.from_dict(purchase_orders)

    orderline_ids = set()
    for od in orders_:
        orderline_ids.update(od['order_line'])
    orderline_ids = list(orderline_ids)
    return df_purchase_orders, orderline_ids

def fetch_all_purchase_orderline_details(orderline_ids):
    orderlines = []
    orderlines_ = cli.read('purchase.order.line', [orderline_ids])
    for odl in orderlines_:
        if odl['display_type'] == 'line_note':
            continue
        line = {
            "order_number": odl['order_id'][1],  # 订单号
            "product_name": odl['name'],
            "internal_reference": __extract_internal_ref_from_product_name(odl['name']),
            "currency": odl['currency_id'][1],
            "order_partner": odl['partner_id'][1],  # 客户
            'state': odl['state'],
            'uom': odl['product_uom'][1],  # 单位
            'product_uom_qty': odl['product_uom_qty'],  # product_qty
            'product_qty': odl['product_qty'],  # 数量
            'price_unit': odl['price_unit'],  # 单价
            'price_subtotal': odl['price_subtotal'],  # 小计
            'price_tax': odl['price_tax'],  # 含税
            'price_total': odl['price_total'],  # 总计
            'qty_to_invoice': odl['qty_to_invoice'],
            'qty_received': odl['qty_received'],
            'date_order': odl['date_order'],
            'product_type': odl['product_type'],
            'create_date': odl['create_date'],
            'discount': odl['discount'],
        }

        orderlines.append(line)

    df_purchase_order_lines = pd.DataFrame.from_dict(orderlines)
    df_purchase_order_lines['create_date'] = pd.to_datetime(df_purchase_order_lines['create_date'],
                                                            format='%Y-%m-%d %H:%M:%S')
    df_purchase_order_lines.sort_values(by='create_date', inplace=True)
    return df_purchase_order_lines


def fetch_all_product_template_details(product_ids):
    # Get Product Details
    domain = [("id", "in", product_ids), "|", ("active", "=", True), ("active", "=", False)]
    fields = {
        "fields":
            ['id', 'name', 'display_name', 'list_price', 'default_code', 'uom_name',
             'active', 'barcode', 'standard_price', 'volume', 'weight', 'categ_id']
    }
    products_ = cli.search_read('product.template', [domain], fields)

    products = []
    for prod in products_:
        product_dict = {
            'id': prod['id'],
            'name': prod['name'],
            'display_name': prod['display_name'],
            'categ_id': prod['categ_id'][1],
            'list_price': prod['list_price'],
            'default_code': prod['default_code'],
            'barcode': prod['barcode'],
            'standard_price': prod['standard_price'],
            'volume': prod['volume'],
            'weight': prod['weight'],
            'uom_name': prod['uom_name'],
        }
        products.append(product_dict)

    df_products = pd.DataFrame.from_dict(products)
    return df_products




if __name__ == '__main__':
    # orders = fetch_all_sales__order_details()
    # print(orders)

    # orderlines = fetch_sales_orderline_details([1, 2, 3])
    # print(orderlines)

    # df_purchase_orders, orderline_ids = fetch_all_purchase_order_details()
    # print(df_purchase_orders)
    # print(orderline_ids)

    # df_purchase_order_lines = fetch_all_purchase_orderline_details([1, 2, 3])
    # print(df_purchase_order_lines)

    df_products = fetch_all_product_template_details([9720, 4066, 4555])
    print(df_products)
