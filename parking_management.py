from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Optional, List

# Vehicle size hierarchy for slot allocation
SLOT_COMPATIBILITY = {
    "BIKE": ["BIKE_SLOT", "CAR_SLOT", "SUV_SLOT", "LARGE_SLOT"],
    "CAR": ["CAR_SLOT", "SUV_SLOT", "LARGE_SLOT"],
    "SUV": ["SUV_SLOT", "LARGE_SLOT"],
    "TRUCK": ["LARGE_SLOT"],
    "EV": ["EV_SLOT", "CAR_SLOT", "SUV_SLOT", "LARGE_SLOT"]
}

BASE_HOURLY_RATES = {
    "BIKE": 10.0,
    "CAR": 20.0,
    "SUV": 30.0,
    "TRUCK": 50.0,
    "EV": 25.0
}

@dataclass
class Vehicle:
    plate_number: str
    vehicle_type: str  # "BIKE", "CAR", "SUV", "TRUCK", "EV"
    is_vip: bool = False
    needs_ev_charging: bool = False

@dataclass
class ParkingSlot:
    slot_id: str
    slot_type: str  # "BIKE_SLOT", "CAR_SLOT", "SUV_SLOT", "LARGE_SLOT", "EV_SLOT"
    is_vip_reserved: bool = False
    is_occupied: bool = False
    current_vehicle: Optional[Vehicle] = None

@dataclass
class ParkingTicket:
    ticket_id: str
    vehicle: Vehicle
    slot_id: str
    entry_time: datetime
    is_lost: bool = False

class ParkingManagement:
    def __init__(self):
        self.slots: Dict[str, ParkingSlot] = {}
        self.active_tickets: Dict[str, ParkingTicket] = {}
        self.vehicle_registry: Dict[str, str] = {}  # plate -> ticket_id
        self._ticket_counter = 1000

    def add_slot(self, slot: ParkingSlot):
        self.slots[slot.slot_id] = slot

    def find_available_slot(self, vehicle: Vehicle) -> Optional[str]:
        allowed_slot_types = SLOT_COMPATIBILITY.get(vehicle.vehicle_type.upper(), [])

        # If EV charging is requested, prioritize EV_SLOT
        if vehicle.needs_ev_charging:
            allowed_slot_types = ["EV_SLOT"] + [t for t in allowed_slot_types if t != "EV_SLOT"]

        for slot_type in allowed_slot_types:
            for slot in self.slots.values():
                if slot.slot_type == slot_type and not slot.is_occupied:
                    # Match VIP designation
                    if slot.is_vip_reserved and not vehicle.is_vip:
                        continue
                    return slot.slot_id
        return None

    def vehicle_entry(self, vehicle: Vehicle, entry_time: datetime) -> dict:
        if not vehicle or not vehicle.plate_number:
            return {"success": False, "message": "Invalid vehicle details."}

        # Check for Duplicate Vehicle
        if vehicle.plate_number in self.vehicle_registry:
            return {"success": False, "message": f"Vehicle {vehicle.plate_number} is already parked inside."}

        slot_id = self.find_available_slot(vehicle)
        if not slot_id:
            return {"success": False, "message": "No suitable parking slot available."}

        slot = self.slots[slot_id]
        slot.is_occupied = True
        slot.current_vehicle = vehicle

        self._ticket_counter += 1
        t_id = f"TICK{self._ticket_counter}"
        ticket = ParkingTicket(t_id, vehicle, slot_id, entry_time)

        self.active_tickets[t_id] = ticket
        self.vehicle_registry[vehicle.plate_number] = t_id

        return {"success": True, "ticket_id": t_id, "slot_id": slot_id}

    def calculate_fee(self, ticket: ParkingTicket, exit_time: datetime, is_lost_ticket: bool = False) -> float:
        if is_lost_ticket:
            return 100.0  # Flat lost-ticket penalty fee

        duration_seconds = max(0, (exit_time - ticket.entry_time).total_seconds())
        hours = max(1, int((duration_seconds + 3599) // 3600))  # Minimum 1 hr, ceiling rounding

        vtype = ticket.vehicle.vehicle_type.upper()
        rate = BASE_HOURLY_RATES.get(vtype, 20.0)

        total_fee = 0.0
        current_time = ticket.entry_time

        # Calculate hourly dynamic fee with peak charges & overnight discount
        for _ in range(hours):
            hour_of_day = current_time.hour
            multiplier = 1.0

            # Peak Hours (08:00–11:00 & 17:00–20:00) = 50% surge
            if (8 <= hour_of_day < 11) or (17 <= hour_of_day < 20):
                multiplier = 1.5
            # Overnight Hours (23:00–06:00) = 20% discount
            elif hour_of_day >= 23 or hour_of_day < 6:
                multiplier = 0.8

            total_fee += rate * multiplier
            current_time += timedelta(hours=1)

        # VIP discount (20%)
        if ticket.vehicle.is_vip:
            total_fee *= 0.80

        # EV Charging Flat Addition ($15 flat)
        if ticket.vehicle.needs_ev_charging:
            total_fee += 15.0

        return round(total_fee, 2)

    def vehicle_exit(self, ticket_id: str, exit_time: datetime, is_lost_ticket: bool = False) -> dict:
        ticket = self.active_tickets.get(ticket_id)
        if not ticket and not is_lost_ticket:
            return {"success": False, "message": "Invalid ticket ID."}

        if is_lost_ticket and not ticket:
            # Handle ticket recovery by plate number if provided in ticket_id string
            t_id = self.vehicle_registry.get(ticket_id)
            if not t_id:
                return {"success": False, "fee": 100.0, "message": "Lost ticket penalty charged."}
            ticket = self.active_tickets[t_id]

        fee = self.calculate_fee(ticket, exit_time, is_lost_ticket)

        # Free up slot and registry
        slot = self.slots[ticket.slot_id]
        slot.is_occupied = False
        slot.current_vehicle = None

        del self.vehicle_registry[ticket.vehicle.plate_number]
        del self.active_tickets[ticket.ticket_id]

        return {"success": True, "fee": fee, "duration_calculated": True}