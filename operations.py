import dotenv
import pandas as pd

from rest import OdooAPIKey, OdooWarehouseOperation, OdooPricelistOperation

# 调整显示选项
pd.set_option('display.max_columns', None)  # 显示所有列
pd.set_option('display.max_colwidth', None)  # 不限制列宽
pd.set_option('display.width', 1000)  # 增加总宽度

env_path = "conf/.env"
dotenv.load_dotenv(env_path)
key = OdooAPIKey.prod()

"""
Export
"""
def show_warehouse_quants():
    """
    显示库存量
    :return:
    """
    operation = OdooWarehouseOperation(key)
    operation.list_quants_to_show()
    print("Done")

def show_product():
    operation = OdooWarehouseOperation(key)
    operation.list_products_to_show()
    print("Done")

"""
Actions
"""
def relocate_quant_by_putaway_rules():
    """
    根据上架规则，将库存量移动到对应的上架位置
    :return:
    """
    operation = OdooWarehouseOperation(key)
    print("Test Relocate Quants to Putaway Location")
    stock_to_move = operation.find_quants_match_putaway_rules()
    ans = input("Are you sure to relocate the quants? (y/n)")
    if ans.lower() != "y":
        print("Aborted")
        return
    operation.relocate_quants_to_putaway_location(stock_to_move)
    print("Done")

def update_pricelist_items():
    operation = OdooPricelistOperation(key, debug=True)
    operation.update_price_list_item()
    print("Done")


if __name__ == '__main__':
    # show_warehouse_quants()
    # show_product()
    # relocate_quant_by_putaway_rules()
    update_pricelist_items()