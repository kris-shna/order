import unittest
from order_management import OrderManagement, Product, OrderItem

class TestOrderManagementQA(unittest.TestCase):

    def setUp(self):
        self.system = OrderManagement()
        self.p_phone = Product("P101", "Smartphone", "ELECTRONICS", 300.0, 15)
        self.p_shirt = Product("P102", "T-Shirt", "CLOTHING", 25.0, 50)
        self.p_apple = Product("P103", "Apple", "GROCERY", 2.0, 100)
        self.p_out_stock = Product("P104", "Limited Shoe", "FOOTWEAR", 150.0, 0)

    # 1. Single product
    def test_01_single_product(self):
        res = self.system.process_order([OrderItem(self.p_apple, 10)])
        self.assertTrue(res["success"])
        self.assertEqual(res["subtotal"], 20.0)
        self.assertEqual(res["shipping_charge"], 40.0)

    # 2. Multiple products
    def test_02_multiple_products(self):
        res = self.system.process_order([OrderItem(self.p_shirt, 2), OrderItem(self.p_apple, 10)])
        self.assertTrue(res["success"])
        self.assertEqual(res["subtotal"], 70.0)

    # 3. Zero quantity
    def test_03_zero_quantity(self):
        res = self.system.process_order([OrderItem(self.p_shirt, 0)])
        self.assertFalse(res["success"])
        self.assertIn("Zero quantity", res["message"])

    # 4. Negative quantity
    def test_04_negative_quantity(self):
        res = self.system.process_order([OrderItem(self.p_shirt, -5)])
        self.assertFalse(res["success"])
        self.assertIn("Negative quantity", res["message"])

    # 5. Invalid product
    def test_05_invalid_null_product(self):
        res = self.system.process_order([OrderItem(None, 2)])
        self.assertFalse(res["success"])
        self.assertIn("Invalid product", res["message"])

    # 6. Out-of-stock products
    def test_06_out_of_stock(self):
        res = self.system.process_order([OrderItem(self.p_out_stock, 1)])
        self.assertFalse(res["success"])
        self.assertIn("out of stock", res["message"])

    # 7. Quantity exceeding available stock
    def test_07_exceed_available_stock(self):
        res = self.system.process_order([OrderItem(self.p_phone, 20)])
        self.assertFalse(res["success"])
        self.assertIn("out of stock", res["message"])

    # 8. Invalid coupon
    def test_08_invalid_coupon(self):
        res = self.system.process_order([OrderItem(self.p_apple, 5)], "INVALID123")
        self.assertFalse(res["success"])
        self.assertIn("Invalid coupon code", res["message"])

    # 9. Valid coupon discount
    def test_09_valid_coupon_save10(self):
        res = self.system.process_order([OrderItem(self.p_apple, 50)], "SAVE10")
        self.assertTrue(res["success"])
        self.assertEqual(res["coupon_discount"], 10.0)

    # 10. Category discount (Electronics)
    def test_10_electronics_category_discount(self):
        res = self.system.process_order([OrderItem(self.p_phone, 1)])
        self.assertEqual(res["category_discount"], 15.0)

    # 11. Category discount (Clothing)
    def test_11_clothing_category_discount(self):
        res = self.system.process_order([OrderItem(self.p_shirt, 4)])
        self.assertEqual(res["category_discount"], 10.0)

    # 12. Bulk order discount
    def test_12_bulk_order_discount(self):
        res = self.system.process_order([OrderItem(self.p_apple, 10)])
        self.assertEqual(res["bulk_discount"], 1.0)

    # 13. Maximum discount limit
    def test_13_maximum_discount_cap(self):
        p_expensive = Product("P999", "TV", "ELECTRONICS", 2000.0, 10)
        res = self.system.process_order([OrderItem(p_expensive, 2)], "MEGA50")
        self.assertEqual(res["total_discount"], 300.0)

    # 14. Tax calculation (18% GST)
    def test_14_gst_tax_calculation(self):
        res = self.system.process_order([OrderItem(self.p_apple, 50)])
        self.assertAlmostEqual(res["tax_amount"], 17.10, places=2)

    # 15. Free shipping threshold (Below limit)
    def test_15_shipping_below_threshold(self):
        res = self.system.process_order([OrderItem(self.p_shirt, 2)])
        self.assertEqual(res["shipping_charge"], 40.0)

    # 16. Free shipping threshold (Above limit)
    def test_16_free_shipping_above_threshold(self):
        res = self.system.process_order([OrderItem(self.p_phone, 2)])
        self.assertEqual(res["shipping_charge"], 0.0)

    # 17. Free shipping threshold (Exact boundary limit)
    def test_17_free_shipping_exact_boundary(self):
        p_exact = Product("PBND", "Item", "GROCERY", 500.0, 5)
        res = self.system.process_order([OrderItem(p_exact, 1)])
        self.assertEqual(res["shipping_charge"], 0.0)

    # 18. Empty order
    def test_18_empty_order(self):
        res = self.system.process_order([])
        self.assertFalse(res["success"])

    # 19. Case-insensitive coupon validation
    def test_19_case_insensitive_coupon(self):
        res = self.system.process_order([OrderItem(self.p_apple, 50)], "save10")
        self.assertTrue(res["success"])
        self.assertEqual(res["coupon_discount"], 10.0)

    # 20. Complex multi-rule combo order
    def test_20_complex_combo_order(self):
        items = [OrderItem(self.p_phone, 1), OrderItem(self.p_shirt, 10)]
        res = self.system.process_order(items, "SUPER20")
        self.assertTrue(res["success"])
        self.assertEqual(res["subtotal"], 550.0)
        self.assertEqual(res["total_discount"], 152.0)

if __name__ == "__main__":
    unittest.main()