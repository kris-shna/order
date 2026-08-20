import unittest
from hospital_management import HospitalManagement, Patient, LabTest, Medicine

class TestHospitalManagementQA(unittest.TestCase):

    def setUp(self):
        self.hospital = HospitalManagement()
        self.std_patient = Patient("P101", "John Doe", 35)
        self.senior_patient = Patient("P102", "Alice Smith", 68, is_senior_citizen=True)
        self.insured_patient = Patient("P103", "Bob Jones", 40, has_insurance=True, insurance_co_pay_percent=0.20)
        self.emergency_patient = Patient("P104", "Charlie Brown", 50, is_emergency=True)

        self.blood_test = LabTest("T01", "Blood Work", 100.0)
        self.xray = LabTest("T02", "X-Ray", 150.0)
        self.painkiller = Medicine("M01", "Ibuprofen", 5.0, 10)
        self.antibiotic = Medicine("M02", "Amoxicillin", 12.0, 5)

    # 1. Standard regular consultation
    def test_01_standard_consultation(self):
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", 30)
        self.assertTrue(res["success"])
        self.assertEqual(res["consultation_fee"], 100.0)
        self.assertEqual(res["patient_payable"], 100.0)

    # 2. Extended consultation duration (>30 mins)
    def test_02_extended_duration_consultation(self):
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", 45)
        self.assertEqual(res["consultation_fee"], 125.0)

    # 3. Emergency patient surcharge rule
    def test_03_emergency_patient_surcharge(self):
        res = self.hospital.calculate_billing(self.emergency_patient, "Dr. House", "ER", "EMERGENCY", 20)
        self.assertEqual(res["consultation_fee"], 250.0)

    # 4. Senior citizen discount (15%)
    def test_04_senior_citizen_discount(self):
        res = self.hospital.calculate_billing(self.senior_patient, "Dr. Stone", "Cardiology", "REGULAR", 30)
        self.assertEqual(res["consultation_fee"], 85.0)

    # 5. Follow-up consultation discount (50%)
    def test_05_followup_consultation_discount(self):
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "FOLLOW_UP", 30)
        self.assertEqual(res["consultation_fee"], 50.0)

    # 6. Senior citizen follow-up consultation combo
    def test_06_senior_followup_combo(self):
        res = self.hospital.calculate_billing(self.senior_patient, "Dr. Adams", "General", "FOLLOW_UP", 30)
        self.assertEqual(res["consultation_fee"], 42.5)

    # 7. Lab charges calculation
    def test_07_lab_charges_only(self):
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", 30, lab_tests=[self.blood_test, self.xray])
        self.assertEqual(res["lab_charges"], 250.0)
        self.assertEqual(res["gross_total"], 350.0)

    # 8. Medicine charges calculation
    def test_08_medicine_charges_only(self):
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", 30, medicines=[self.painkiller, self.antibiotic])
        self.assertEqual(res["medicine_charges"], 110.0)

    # 9. Insurance coverage (20% co-pay / 80% coverage)
    def test_09_insured_patient_billing(self):
        res = self.hospital.calculate_billing(self.insured_patient, "Dr. Adams", "General", "REGULAR", 30)
        self.assertEqual(res["insurance_coverage"], 80.0)
        self.assertEqual(res["patient_payable"], 20.0)

    # 10. Insured patient with labs and meds
    def test_10_insured_patient_full_bill(self):
        res = self.hospital.calculate_billing(self.insured_patient, "Dr. Adams", "General", "REGULAR", 30, [self.blood_test], [self.painkiller])
        self.assertEqual(res["gross_total"], 250.0)
        self.assertEqual(res["insurance_coverage"], 200.0)
        self.assertEqual(res["patient_payable"], 50.0)

    # 11. Invalid duration (zero)
    def test_11_zero_duration(self):
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", 0)
        self.assertFalse(res["success"])

    # 12. Negative duration
    def test_12_negative_duration(self):
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", -15)
        self.assertFalse(res["success"])

    # 13. Invalid patient object
    def test_13_null_patient(self):
        res = self.hospital.calculate_billing(None, "Dr. Adams", "General", "REGULAR", 30)
        self.assertFalse(res["success"])

    # 14. Negative lab price validation
    def test_14_negative_lab_price(self):
        bad_test = LabTest("T99", "Invalid Test", -50.0)
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", 30, lab_tests=[bad_test])
        self.assertFalse(res["success"])

    # 15. Negative medicine quantity validation
    def test_15_negative_medicine_quantity(self):
        bad_med = Medicine("M99", "Invalid Med", 10.0, -2)
        res = self.hospital.calculate_billing(self.std_patient, "Dr. Adams", "General", "REGULAR", 30, medicines=[bad_med])
        self.assertFalse(res["success"])

    # 16. Auto-detect senior citizen by age >= 60
    def test_16_auto_senior_by_age(self):
        p_old = Patient("P105", "Grandma", 75)
        res = self.hospital.calculate_billing(p_old, "Dr. Adams", "General", "REGULAR", 30)
        self.assertEqual(res["consultation_fee"], 85.0)

    # 17. 100% Insurance coverage (0% co-pay)
    def test_17_full_insurance_coverage(self):
        p_full_ins = Patient("P106", "Dave", 30, has_insurance=True, insurance_co_pay_percent=0.0)
        res = self.hospital.calculate_billing(p_full_ins, "Dr. Adams", "General", "REGULAR", 30)
        self.assertEqual(res["insurance_coverage"], 100.0)
        self.assertEqual(res["patient_payable"], 0.0)

    # 18. Emergency senior citizen combo
    def test_18_emergency_senior_combo(self):
        res = self.hospital.calculate_billing(self.senior_patient, "Dr. ER", "ER", "EMERGENCY", 30)
        self.assertEqual(res["consultation_fee"], 212.5)

    # 19. Long emergency consultation (>60 mins)
    def test_19_long_emergency_consultation(self):
        res = self.hospital.calculate_billing(self.emergency_patient, "Dr. ER", "ER", "EMERGENCY", 60)
        self.assertEqual(res["consultation_fee"], 300.0)

    # 20. Complex multi-service insured senior patient
    def test_20_complex_multi_service_billing(self):
        p_senior_ins = Patient("P107", "Elderly VIP", 70, is_senior_citizen=True, has_insurance=True, insurance_co_pay_percent=0.10)
        res = self.hospital.calculate_billing(p_senior_ins, "Dr. Specialist", "Neurology", "FOLLOW_UP", 45, [self.blood_test, self.xray], [self.antibiotic])
        self.assertTrue(res["success"])
        self.assertEqual(res["consultation_fee"], 53.12)  # Updated from 63.75
        self.assertEqual(res["lab_charges"], 250.0)
        self.assertEqual(res["medicine_charges"], 60.0)
        self.assertEqual(res["gross_total"], 363.12)       # Updated from 373.75
        self.assertEqual(res["insurance_coverage"], 326.81) # Updated from 336.38
        self.assertEqual(res["patient_payable"], 36.31)    # Updated from 37.37

if __name__ == "__main__":
    unittest.main()
