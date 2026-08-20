from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Passenger:
    passenger_id: str
    name: str
    age: int
    passenger_type: str = "ADULT"  # "ADULT", "CHILD", "INFANT", "SENIOR"

@dataclass
class Booking:
    booking_id: str
    flight_number: str
    passenger: Passenger
    travel_class: str
    seat_number: str
    base_fare: float
    baggage_charges: float
    total_fare: float
    status: str = "CONFIRMED"  # "CONFIRMED", "CANCELLED"

class Flight:
    def __init__(self, flight_number: str, origin: str, destination: str, travel_date: datetime, total_seats: dict, base_prices: dict):
        self.flight_number = flight_number
        self.origin = origin
        self.destination = destination
        self.travel_date = travel_date
        self.total_seats = total_seats  # {"ECONOMY": 10, "BUSINESS": 5, "FIRST": 2}
        self.booked_seats = {k: [] for k in total_seats.keys()}
        self.base_prices = base_prices  # {"ECONOMY": 100.0, "BUSINESS": 250.0, "FIRST": 500.0}

class AirlineReservation:
    def __init__(self):
        self.flights: Dict[str, Flight] = {}
        self.bookings: Dict[str, Booking] = {}
        self._booking_counter = 1000

    def add_flight(self, flight: Flight):
        self.flights[flight.flight_number] = flight

    def calculate_dynamic_fare(self, flight_number: str, travel_class: str, booking_date: datetime, passenger_type: str) -> float:
        flight = self.flights.get(flight_number)
        if not flight or travel_class not in flight.total_seats:
            return -1.0

        fare = flight.base_prices[travel_class]

        # 1. Capacity Demand Multiplier
        total = flight.total_seats[travel_class]
        booked = len(flight.booked_seats[travel_class])
        occupancy_ratio = booked / total if total > 0 else 1.0

        if occupancy_ratio >= 0.8:
            fare *= 1.50  # 50% surge
        elif occupancy_ratio >= 0.5:
            fare *= 1.20  # 20% surge

        # 2. Advance Booking Multiplier
        days_in_advance = (flight.travel_date - booking_date).days
        if days_in_advance < 3:
            fare *= 1.40  # Last-minute markup
        elif days_in_advance > 30:
            fare *= 0.85  # Early bird discount

        # 3. Passenger Type Discount
        ptype = passenger_type.upper()
        if ptype == "CHILD":
            fare *= 0.75
        elif ptype == "INFANT":
            fare *= 0.10
        elif ptype == "SENIOR":
            fare *= 0.85

        return round(fare, 2)

    def calculate_baggage_charge(self, weight_kg: float, free_allowance_kg: float = 15.0, rate_per_kg: float = 10.0) -> float:
        if weight_kg <= free_allowance_kg:
            return 0.0
        return round((weight_kg - free_allowance_kg) * rate_per_kg, 2)

    def book_passenger(self, flight_number: str, passenger: Passenger, travel_class: str, seat_number: str, baggage_weight_kg: float, booking_date: datetime) -> dict:
        if not passenger or not passenger.name:
            return {"success": False, "message": "Invalid passenger details."}

        flight = self.flights.get(flight_number)
        if not flight:
            return {"success": False, "message": f"Flight {flight_number} not found."}

        travel_class = travel_class.upper()
        if travel_class not in flight.total_seats:
            return {"success": False, "message": "Invalid travel class."}

        # Check for Fully Booked
        if len(flight.booked_seats[travel_class]) >= flight.total_seats[travel_class]:
            return {"success": False, "message": f"Flight is fully booked in {travel_class} class."}

        # Check for Double Booking on Seat
        if seat_number in flight.booked_seats[travel_class]:
            return {"success": False, "message": f"Seat {seat_number} is already booked."}

        base_fare = self.calculate_dynamic_fare(flight_number, travel_class, booking_date, passenger.passenger_type)
        baggage_fee = self.calculate_baggage_charge(baggage_weight_kg)
        total_fare = round(base_fare + baggage_fee, 2)

        self._booking_counter += 1
        b_id = f"BK{self._booking_counter}"

        booking = Booking(b_id, flight_number, passenger, travel_class, seat_number, base_fare, baggage_fee, total_fare)
        self.bookings[b_id] = booking
        flight.booked_seats[travel_class].append(seat_number)

        return {"success": True, "booking_id": b_id, "total_fare": total_fare, "seat": seat_number}

    def cancel_booking(self, booking_id: str, cancel_date: datetime) -> dict:
        booking = self.bookings.get(booking_id)
        if not booking or booking.status == "CANCELLED":
            return {"success": False, "message": "Invalid or already cancelled booking."}

        flight = self.flights[booking.flight_number]
        days_before = (flight.travel_date - cancel_date).days

        # Refund Policy Logic
        if days_before >= 7:
            refund_ratio = 0.90  # 10% penalty
        elif days_before >= 2:
            refund_ratio = 0.50  # 50% penalty
        else:
            refund_ratio = 0.00  # Non-refundable

        refund_amount = round(booking.total_fare * refund_ratio, 2)
        booking.status = "CANCELLED"
        flight.booked_seats[booking.travel_class].remove(booking.seat_number)

        return {"success": True, "refund_amount": refund_amount, "penalty": round(booking.total_fare - refund_amount, 2)}