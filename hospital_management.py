from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Patient:
    patient_id: str
    name: str
    age: int
    is_emergency: bool = False
    is_senior_citizen: bool = False
    has_insurance: bool = False
    insurance_co_pay_percent: float = 0.20  # Patient pays 20% by default if insured

@dataclass
class LabTest:
    test_id: str
    name: str
    price: float

@dataclass
class Medicine:
    med_id: str
    name: str
    unit_price: float
    quantity: int

class HospitalManagement:
    BASE_CONSULTATION_FEE = 100.0
    EMERGENCY_SURCHARGE = 150.0
    SENIOR_DISCOUNT_PERCENT = 0.15
    FOLLOWUP_DISCOUNT_PERCENT = 0.50

    def calculate_billing(
        self,
        patient: Patient,
        doctor_name: str,
        department: str,
        appointment_type: str,  # "REGULAR", "EMERGENCY", "FOLLOW_UP"
        duration_minutes: int,
        lab_tests: Optional[List[LabTest]] = None,
        medicines: Optional[List[Medicine]] = None
    ) -> dict:
        if not patient:
            return {"success": False, "message": "Invalid patient details."}
        if duration_minutes <= 0:
            return {"success": False, "message": "Consultation duration must be greater than zero."}

        # 1. Base Consultation Fee Calculation
        consultation_fee = self.BASE_CONSULTATION_FEE
        if duration_minutes > 30:
            extra_slots = (duration_minutes - 30 + 14) // 15
            consultation_fee += extra_slots * 25.0

        app_type_upper = appointment_type.upper()
        if app_type_upper == "EMERGENCY" or patient.is_emergency:
            consultation_fee += self.EMERGENCY_SURCHARGE
        elif app_type_upper == "FOLLOW_UP":
            consultation_fee *= (1.0 - self.FOLLOWUP_DISCOUNT_PERCENT)

        # Senior Citizen Discount on Consultation
        if patient.age >= 60 or patient.is_senior_citizen:
            consultation_fee *= (1.0 - self.SENIOR_DISCOUNT_PERCENT)

        consultation_fee = round(consultation_fee, 2)

        # 2. Lab Charges
        lab_charges = 0.0
        if lab_tests:
            for test in lab_tests:
                if test.price < 0:
                    return {"success": False, "message": f"Invalid lab test price: {test.price}"}
                lab_charges += test.price
        lab_charges = round(lab_charges, 2)

        # 3. Medicine Charges
        medicine_charges = 0.0
        if medicines:
            for med in medicines:
                if med.unit_price < 0 or med.quantity < 0:
                    return {"success": False, "message": f"Invalid medicine pricing or quantity for: {med.name}"}
                medicine_charges += med.unit_price * med.quantity
        medicine_charges = round(medicine_charges, 2)

        gross_total = consultation_fee + lab_charges + medicine_charges

        # 4. Insurance Coverage Calculation
        insurance_coverage = 0.0
        if patient.has_insurance:
            # Insurance covers (1 - co_pay) of gross bill
            co_pay = max(0.0, min(1.0, patient.insurance_co_pay_percent))
            insurance_coverage = round(gross_total * (1.0 - co_pay), 2)

        patient_payable = round(gross_total - insurance_coverage, 2)

        return {
            "success": True,
            "message": "Billing calculated successfully.",
            "patient_id": patient.patient_id,
            "doctor": doctor_name,
            "department": department,
            "consultation_fee": consultation_fee,
            "lab_charges": lab_charges,
            "medicine_charges": medicine_charges,
            "gross_total": round(gross_total, 2),
            "insurance_coverage": insurance_coverage,
            "patient_payable": patient_payable
        }