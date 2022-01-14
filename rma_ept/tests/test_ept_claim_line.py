from odoo.tests import common, tagged
from datetime import datetime


class TestEptClaimLine(common.TransactionCase):
    @tagged("post_install", "-at_install")
    def test_check_warranty(self):
        """Checks if the check_warranty works properly"""
        product = self.env["product.template"].create(
            {
                "name": "Test Warrantee",
                "warranty": 30,
                "warranty_type": "day",
            }
        )
        ept_line = self.env["claim.line.ept"]
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2020, 1, 31)
        )
        self.assertEqual(value, True)
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2020, 2, 10)
        )
        self.assertEqual(value, False)
        product.warranty_type = "week"
        product.warranty = 7
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2020, 2, 10)
        )
        self.assertEqual(value, True)
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2020, 3, 20)
        )
        self.assertEqual(value, False)
        product.warranty_type = "month"
        product.warranty = 3
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2020, 3, 20)
        )
        self.assertEqual(value, True)
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2020, 4, 20)
        )
        self.assertEqual(value, False)
        product.warranty_type = "year"
        product.warranty = 1
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2020, 12, 31)
        )
        self.assertEqual(value, True)
        value = ept_line.check_guaarantee(
            product, datetime(2020, 1, 1), datetime(2021, 1, 2)
        )
        self.assertEqual(value, False)
