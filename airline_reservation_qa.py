import unittest
from datetime import datetime, timedelta
from airline_reservation import AirlineReservation, Flight, Passenger

class TestAirlineReservationQA(unittest.TestCase):

    def setUp(self):
        self.system = AirlineReservation()
        self.travel_date = datetime.now() + timedelta(days=15)
        self.booking_date = datetime.now()

        # Flight with limited seats for testing fully booked condition
        self.flight = Flight(
            flight_number="AI101",
            origin="JFK",
            destination="LHR",
            travel_date=self.travel_date,
            total_seats={"ECONOMY": 2, "BUSINESS": 1, "FIRST": 1},
            base_prices={"ECONOMY": 100.0, "BUSINESS": 250.0, "FIRST": 500.0}
        )
        self.system.add_flight(self.flight)
        self.passenger = Passenger("P1", "John Doe", 30, "ADULT")

    # 1. Successful Booking
    def test_01_successful_booking(self):
        res = self.system.book_passenger("AI101", self.passenger, "ECONOMY", "12A", 10.0, self.booking_date)
        self.assertTrue(res["success"])
        self.assertIn("BK", res["booking_id"])

    # 2. Double Booking Prevention
    def test_02_double_booking_prevention(self):
        self.system.book_passenger("AI101", self.passenger, "ECONOMY", "12A", 10.0, self.booking_date)
        p2 = Passenger("P2", "Jane Doe", 28, "ADULT")
        res = self.system.book_passenger("AI101", p2, "ECONOMY", "12A", 10.0, self.booking_date)
        self.assertFalse(res["success"])

    # 3. Fully Booked Flight
    def test_03_fully_booked_flight(self):
        p1 = Passenger("P1", "A", 30)
        p2 = Passenger("P2", "B", 30)
        p3 = Passenger("P3", "C", 30)
        self.system.book_passenger("AI101", p1, "ECONOMY", "1A", 10.0, self.booking_date)
        self.system.book_passenger("AI101", p2, "ECONOMY", "1B", 10.0, self.booking_date)
        res = self.system.book_passenger("AI101", p3, "ECONOMY", "1C", 10.0, self.booking_date)
        self.assertFalse(res["success"])

    # 4. Invalid Passenger
    def test_04_invalid_passenger(self):
        invalid_p = Passenger("P0", "", 0)
        res = self.system.book_passenger("AI101", invalid_p, "ECONOMY", "1A", 10.0, self.booking_date)
        self.assertFalse(res["success"])

    # 5. Excess Baggage Charges
    def test_05_excess_baggage_charges(self):
        charge = self.system.calculate_baggage_charge(25.0, free_allowance_kg=15.0, rate_per_kg=10.0)
        self.assertEqual(charge, 100.0)

    # 6. Normal Baggage Charges (Within Allowance)
    def test_06_within_allowance_baggage(self):
        charge = self.system.calculate_baggage_charge(12.0)
        self.assertEqual(charge, 0.0)

    # 7. Cancellation and Full/Partial Refund (7+ days prior)
    def test_07_cancellation_refund_early(self):
        bk = self.system.book_passenger("AI101", self.passenger, "ECONOMY", "12A", 10.0, self.booking_date)
        cancel_date = self.travel_date - timedelta(days=10)
        res = self.system.cancel_booking(bk["booking_id"], cancel_date)
        self.assertTrue(res["success"])
        self.assertEqual(res["refund_amount"], round(bk["total_fare"] * 0.90, 2))

    # 8. Late Cancellation Refund (Less than 2 days)
    def test_08_cancellation_late_no_refund(self):
        bk = self.system.book_passenger("AI101", self.passenger, "ECONOMY", "12A", 10.0, self.booking_date)
        cancel_date = self.travel_date - timedelta(days=1)
        res = self.system.cancel_booking(bk["booking_id"], cancel_date)
        self.assertEqual(res["refund_amount"], 0.0)

    # 9. Dynamic Pricing - High Demand (>80% Capacity)
    def test_09_dynamic_pricing_high_demand(self):
        # 1 seat booked out of 1 in BUSINESS = 100% capacity
        p1 = Passenger("P1", "A", 30)
        self.system.book_passenger("AI101", p1, "BUSINESS", "1A", 0.0, self.booking_date)
        fare = self.system.calculate_dynamic_fare("AI101", "BUSINESS", self.booking_date, "ADULT")
        self.assertEqual(fare, 375.0)  # $250 base * 1.5 multiplier

    # 10. Dynamic Pricing - Child Discount
    def test_10_child_passenger_discount(self):
        child = Passenger("P2", "Kid", 8, "CHILD")
        fare = self.system.calculate_dynamic_fare("AI101", "ECONOMY", self.booking_date, "CHILD")
        self.assertEqual(fare, 75.0)  # $100 base * 0.75 multiplier

    # 11. Dynamic Pricing - Last-minute booking (< 3 days)
    def test_11_last_minute_markup(self):
        last_minute_date = self.travel_date - timedelta(days=1)
        fare = self.system.calculate_dynamic_fare("AI101", "ECONOMY", last_minute_date, "ADULT")
        self.assertEqual(fare, 140.0)  # $100 base * 1.4 multiplier

    # 12. Dynamic Pricing - Early Bird Discount (> 30 days)
    def test_12_early_bird_discount(self):
        future_travel = datetime.now() + timedelta(days=45)
        f2 = Flight("AI102", "JFK", "LHR", future_travel, {"ECONOMY": 10}, {"ECONOMY": 100.0})
        self.system.add_flight(f2)
        fare = self.system.calculate_dynamic_fare("AI102", "ECONOMY", datetime.now(), "ADULT")
        self.assertEqual(fare, 85.0)  # $100 base * 0.85 multiplier

    # 13. Senior Citizen Discount
    def test_13_senior_citizen_discount(self):
        fare = self.system.calculate_dynamic_fare("AI101", "ECONOMY", self.booking_date, "SENIOR")
        self.assertEqual(fare, 85.0)

    # 14. Non-existent Flight Booking
    def test_14_non_existent_flight(self):
        res = self.system.book_passenger("AI999", self.passenger, "ECONOMY", "1A", 0.0, self.booking_date)
        self.assertFalse(res["success"])

    # 15. Invalid Class Booking
    def test_15_invalid_class(self):
        res = self.system.book_passenger("AI101", self.passenger, "PREMIUM_ECONOMY", "1A", 0.0, self.booking_date)
        self.assertFalse(res["success"])

    # 16. Re-booking Cancelled Seat
    def test_16_rebook_cancelled_seat(self):
        bk = self.system.book_passenger("AI101", self.passenger, "BUSINESS", "1A", 0.0, self.booking_date)
        self.system.cancel_booking(bk["booking_id"], self.booking_date)
        p2 = Passenger("P2", "New Passenger", 25)
        res = self.system.book_passenger("AI101", p2, "BUSINESS", "1A", 0.0, self.booking_date)
        self.assertTrue(res["success"])

    # 17. Cancel Non-existent Booking
    def test_17_cancel_non_existent_booking(self):
        res = self.system.cancel_booking("INVALID_ID", self.booking_date)
        self.assertFalse(res["success"])

    # 18. Infant Fare Calculation
    def test_18_infant_fare_discount(self):
        fare = self.system.calculate_dynamic_fare("AI101", "FIRST", self.booking_date, "INFANT")
        self.assertEqual(fare, 50.0)  # $500 base * 0.10

    # 19. First Class Booking Success
    def test_19_first_class_booking(self):
        res = self.system.book_passenger("AI101", self.passenger, "FIRST", "1F", 20.0, self.booking_date)
        self.assertTrue(res["success"])
        self.assertEqual(res["total_fare"], 550.0)  # $500 base + $50 excess baggage (20kg - 15kg)

    # 20. Double Cancellation Prevention
    def test_20_double_cancellation(self):
        bk = self.system.book_passenger("AI101", self.passenger, "ECONOMY", "12A", 10.0, self.booking_date)
        self.system.cancel_booking(bk["booking_id"], self.booking_date)
        second_cancel = self.system.cancel_booking(bk["booking_id"], self.booking_date)
        self.assertFalse(second_cancel["success"])

if __name__ == "__main__":
    unittest.main()