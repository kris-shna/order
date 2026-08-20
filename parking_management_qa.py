import unittest
from datetime import datetime, timedelta
from parking_management import ParkingManagement, ParkingSlot, Vehicle

class TestParkingQA(unittest.TestCase):

    def setUp(self):
        self.system = ParkingManagement()
        # Add basic slots
        self.system.add_slot(ParkingSlot("S_BIKE_1", "BIKE_SLOT"))
        self.system.add_slot(ParkingSlot("S_CAR_1", "CAR_SLOT"))
        self.system.add_slot(ParkingSlot("S_SUV_1", "SUV_SLOT"))
        self.system.add_slot(ParkingSlot("S_LARGE_1", "LARGE_SLOT"))
        self.system.add_slot(ParkingSlot("S_EV_1", "EV_SLOT"))
        self.system.add_slot(ParkingSlot("S_VIP_1", "CAR_SLOT", is_vip_reserved=True))

        self.entry_time = datetime(2026, 8, 20, 12, 0, 0)

    # 1. Successful Vehicle Entry
    def test_01_successful_entry(self):
        car = Vehicle("KA01AB1234", "CAR")
        res = self.system.vehicle_entry(car, self.entry_time)
        self.assertTrue(res["success"])
        self.assertEqual(res["slot_id"], "S_CAR_1")

    # 2. Duplicate Vehicle Prevention
    def test_02_duplicate_vehicle_entry(self):
        car = Vehicle("KA01AB1234", "CAR")
        self.system.vehicle_entry(car, self.entry_time)
        res2 = self.system.vehicle_entry(car, self.entry_time)
        self.assertFalse(res2["success"])

    # 3. Full Parking Lot (No available slot)
    def test_03_full_parking_lot(self):
        c1 = Vehicle("CAR1", "CAR")
        c2 = Vehicle("CAR2", "CAR") # Will take larger slot or fail if no size fits
        self.system.vehicle_entry(c1, self.entry_time)
        # Fill remaining compatible larger slots
        self.system.vehicle_entry(Vehicle("SUV1", "SUV"), self.entry_time)
        self.system.vehicle_entry(Vehicle("TRUCK1", "TRUCK"), self.entry_time)
        self.system.vehicle_entry(Vehicle("EV1", "EV"), self.entry_time)
        
        # Next standard car should fail
        res = self.system.vehicle_entry(c2, self.entry_time)
        self.assertFalse(res["success"])

    # 4. Wrong Vehicle-Slot Combination (Truck can't fit in Bike slot)
    def test_04_wrong_vehicle_slot_fit(self):
        sys_small = ParkingManagement()
        sys_small.add_slot(ParkingSlot("S_BIKE_ONLY", "BIKE_SLOT"))
        truck = Vehicle("TRK99", "TRUCK")
        res = sys_small.vehicle_entry(truck, self.entry_time)
        self.assertFalse(res["success"])

    # 5. Automatic Slot Size Upgrade (Bike taking Car Slot if no Bike slot)
    def test_05_automatic_slot_upgradation(self):
        self.system.slots["S_BIKE_1"].is_occupied = True
        bike = Vehicle("BK99", "BIKE")
        res = self.system.vehicle_entry(bike, self.entry_time)
        self.assertTrue(res["success"])
        self.assertEqual(res["slot_id"], "S_CAR_1")

    # 6. Lost Ticket Handling Fee
    def test_06_lost_ticket_penalty(self):
        car = Vehicle("KA01AB1234", "CAR")
        entry = self.system.vehicle_entry(car, self.entry_time)
        exit_t = self.entry_time + timedelta(hours=2)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t, is_lost_ticket=True)
        self.assertEqual(res["fee"], 100.0)

    # 7. Early Exit / Minimum Hourly Charge (15 mins charged as 1 hour)
    def test_07_early_exit_minimum_charge(self):
        car = Vehicle("KA01AB1234", "CAR")
        entry = self.system.vehicle_entry(car, self.entry_time)
        exit_t = self.entry_time + timedelta(minutes=15)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 20.0)  # Standard 1 hr rate

    # 8. Peak-Hour Dynamic Surge Pricing
    def test_08_peak_hour_surge_pricing(self):
        car = Vehicle("KA01AB1234", "CAR")
        peak_entry = datetime(2026, 8, 20, 8, 30, 0)  # Peak time 8 AM
        entry = self.system.vehicle_entry(car, peak_entry)
        exit_t = peak_entry + timedelta(hours=1)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 30.0)  # 20 base * 1.5 peak surge

    # 9. Overnight Discount Pricing
    def test_09_overnight_parking_discount(self):
        car = Vehicle("KA01AB1234", "CAR")
        night_entry = datetime(2026, 8, 20, 1, 0, 0)  # 1 AM
        entry = self.system.vehicle_entry(car, night_entry)
        exit_t = night_entry + timedelta(hours=1)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 16.0)  # 20 base * 0.8 overnight rate

    # 10. EV Charging Station Allocation and Fee
    def test_10_ev_charging_fee(self):
        ev = Vehicle("EV100", "EV", needs_ev_charging=True)
        entry = self.system.vehicle_entry(ev, self.entry_time)
        self.assertEqual(entry["slot_id"], "S_EV_1")
        exit_t = self.entry_time + timedelta(hours=1)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 40.0)  # 25 base + 15 flat charging fee

    # 11. VIP Parking Reservation Access
    def test_11_vip_vehicle_reservation(self):
        non_vip = Vehicle("NORMAL", "CAR", is_vip=False)
        vip = Vehicle("VIP1", "CAR", is_vip=True)
        
        # Fill non-VIP car slot
        self.system.slots["S_CAR_1"].is_occupied = True
        
        # Non-VIP cannot take VIP slot, moves to next available size (SUV)
        res_non_vip = self.system.vehicle_entry(non_vip, self.entry_time)
        self.assertEqual(res_non_vip["slot_id"], "S_SUV_1")

        # VIP takes VIP slot
        res_vip = self.system.vehicle_entry(vip, self.entry_time)
        self.assertEqual(res_vip["slot_id"], "S_VIP_1")

    # 12. VIP Billing Discount
    def test_12_vip_billing_discount(self):
        vip = Vehicle("VIP1", "CAR", is_vip=True)
        entry = self.system.vehicle_entry(vip, self.entry_time)
        exit_t = self.entry_time + timedelta(hours=1)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 16.0)  # 20 base * 0.8 VIP discount

    # 13. SUV Base Rate Billing
    def test_13_suv_billing_rate(self):
        suv = Vehicle("SUV99", "SUV")
        entry = self.system.vehicle_entry(suv, self.entry_time)
        exit_t = self.entry_time + timedelta(hours=2)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 60.0)  # 30 * 2 hrs

    # 14. Truck Base Rate Billing
    def test_14_truck_billing_rate(self):
        truck = Vehicle("TRK1", "TRUCK")
        entry = self.system.vehicle_entry(truck, self.entry_time)
        exit_t = self.entry_time + timedelta(hours=1)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 50.0)

    # 15. Multi-hour Over-night transition
    def test_15_multi_hour_overnight_transition(self):
        car = Vehicle("KA01AB1234", "CAR")
        entry_t = datetime(2026, 8, 20, 22, 0, 0)  # 10 PM
        entry = self.system.vehicle_entry(car, entry_t)
        exit_t = entry_t + timedelta(hours=2)  # 10 PM -> 12 AM (1 hr normal, 1 hr overnight)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 36.0)  # 20 + 16

    # 16. Invalid Vehicle Input
    def test_16_invalid_vehicle_details(self):
        bad_vehicle = Vehicle("", "CAR")
        res = self.system.vehicle_entry(bad_vehicle, self.entry_time)
        self.assertFalse(res["success"])

    # 17. Invalid Ticket Exit
    def test_17_invalid_ticket_exit(self):
        res = self.system.vehicle_exit("INVALID_TICKET", self.entry_time)
        self.assertFalse(res["success"])

    # 18. Slot Reuse after Exit
    def test_18_slot_reuse_after_exit(self):
        c1 = Vehicle("CAR1", "CAR")
        e1 = self.system.vehicle_entry(c1, self.entry_time)
        self.system.vehicle_exit(e1["ticket_id"], self.entry_time + timedelta(hours=1))

        c2 = Vehicle("CAR2", "CAR")
        e2 = self.system.vehicle_entry(c2, self.entry_time)
        self.assertTrue(e2["success"])
        self.assertEqual(e2["slot_id"], "S_CAR_1")

    # 19. Bike Standard Hourly Billing
    def test_19_bike_hourly_billing(self):
        bike = Vehicle("BK01", "BIKE")
        entry = self.system.vehicle_entry(bike, self.entry_time)
        exit_t = self.entry_time + timedelta(hours=3)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 30.0)  # 10 * 3 hrs

    # 20. EV without Charging Request Billing
    def test_20_ev_without_charging_request(self):
        ev = Vehicle("EV200", "EV", needs_ev_charging=False)
        entry = self.system.vehicle_entry(ev, self.entry_time)
        exit_t = self.entry_time + timedelta(hours=1)
        res = self.system.vehicle_exit(entry["ticket_id"], exit_t)
        self.assertEqual(res["fee"], 25.0)  # Base EV rate without $15 charge fee

if __name__ == "__main__":
    unittest.main()