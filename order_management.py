from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Product:
    id: str
    name: str
    category: str
    unit_price: float
    stock_available: int

@dataclass
class OrderItem:
    product: Optional[Product]
    quantity: int

class OrderManagement:
    FREE_SHIPPING_THRESHOLD = 500.0
    STANDARD_SHIPPING_FEE = 40.0
    MAXIMUM_ALLOWED_DISCOUNT = 300.0
    BULK_THRESHOLD_QTY = 10
    BULK_DISCOUNT_PERCENT = 0.05
    GST_RATE = 0.18

    VALID_COUPONS: Dict[str, float] = {
        "SAVE10": 0.10,
        "SUPER20": 0.20,
        "MEGA50": 0.50
    }

    def process_order(self, items: List[OrderItem], coupon_code: Optional[str] = None) -> dict:
        if not items:
            return {"success": False, "message": "Order must contain at least one item."}

        raw_subtotal = 0.0
        category_discount = 0.0
        bulk_discount = 0.0

        for item in items:
            if not item or not item.product:
                return {"success": False, "message": "Invalid product entry found in order."}

            product = item.product
            qty = item.quantity

            if qty < 0:
                return {"success": False, "message": f"Negative quantity for product: {product.id}"}
            if qty == 0:
                return {"success": False, "message": f"Zero quantity specified for product: {product.id}"}
            if qty > product.stock_available:
                return {"success": False, "message": f"Product {product.id} is out of stock. Requested: {qty}, Available: {product.stock_available}"}

            item_total = product.unit_price * qty
            raw_subtotal += item_total

            cat_upper = product.category.upper()
            if cat_upper == "ELECTRONICS":
                category_discount += item_total * 0.05
            elif cat_upper == "CLOTHING":
                category_discount += item_total * 0.10

            if qty >= self.BULK_THRESHOLD_QTY:
                bulk_discount += item_total * self.BULK_DISCOUNT_PERCENT

        coupon_discount = 0.0
        if coupon_code and coupon_code.strip():
            code_upper = coupon_code.strip().upper()
            if code_upper not in self.VALID_COUPONS:
                return {"success": False, "message": f"Invalid coupon code: {coupon_code}"}
            
            discounted_base = raw_subtotal - (category_discount + bulk_discount)
            coupon_discount = max(0.0, discounted_base * self.VALID_COUPONS[code_upper])

        combined_discount = min(category_discount + bulk_discount + coupon_discount, self.MAXIMUM_ALLOWED_DISCOUNT)
        taxable_amount = max(0.0, raw_subtotal - combined_discount)
        tax_amount = round(taxable_amount * self.GST_RATE, 2)
        shipping_charge = 0.0 if taxable_amount >= self.FREE_SHIPPING_THRESHOLD else self.STANDARD_SHIPPING_FEE
        final_amount = round(taxable_amount + tax_amount + shipping_charge, 2)

        return {
            "success": True,
            "message": "Order processed successfully.",
            "subtotal": round(raw_subtotal, 2),
            "category_discount": round(category_discount, 2),
            "bulk_discount": round(bulk_discount, 2),
            "coupon_discount": round(coupon_discount, 2),
            "total_discount": round(combined_discount, 2),
            "tax_amount": tax_amount,
            "shipping_charge": shipping_charge,
            "final_amount": final_amount
        }