from pydantic import BaseModel


class StockToMove(BaseModel):
    product_id: int
    product_name: str
    location_in_id: int
    location_in_name: str
    location_out_id: int
    location_out_name: str
    quant_id: int
    quant_quantity: float

    def __str__(self):
        product_name = self.product_name.split(' ')[0]
        location_in_name = self.location_in_name.split('/')[-1]
        location_out_name = self.location_out_name.split('/')[-1]
        return f"{self.quant_quantity}x {product_name} from {location_in_name} to {location_out_name}"


class QuantVO(BaseModel):
    product_id: int
    product_name: str
    location_id: int
    location_name: str
    product_uom: str
    warehouse_name: str
    quantity: float
    available_quantity: float

    def __str__(self):
        product_name = self.product_name.split(' ')[0]
        return f"{self.quantity}x {product_name} in {self.location_name} ({self.warehouse_name})"

class ProductVO(BaseModel):
    id: int
    name: str
    list_price: float
    default_code: str
    barcode: str
    standard_price: float
    write_date: str
    active: bool
    qty_available: float

