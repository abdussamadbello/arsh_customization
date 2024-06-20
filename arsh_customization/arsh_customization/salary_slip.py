
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
import frappe


class ArioshSalarySlip(SalarySlip):

    def before_validate(self):
        self.get_field_days()

    def get_total_exemption_amount(self):
        total_exemption_amount = 0
        taxable_income = 0

        if self.tax_slab.allow_tax_exemption:
            if self.deduct_tax_for_unsubmitted_tax_exemption_proof:
                exemption_proof = frappe.db.get_value(
                    "Employee Tax Exemption Proof Submission",
                    {
                        "employee": self.employee,
                        "payroll_period": self.payroll_period.name,
                        "docstatus": 1,
                    },
                    ["exemption_amount"],
                )
                if exemption_proof:
                    total_exemption_amount = exemption_proof
            else:
                declaration = frappe.db.get_value(
                    "Employee Tax Exemption Declaration",
                    {
                        "employee": self.employee,
                        "payroll_period": self.payroll_period.name,
                        "docstatus": 1,
                    },
                    ["total_exemption_amount"],
                )
                if declaration:
                    total_exemption_amount = declaration

            # Calculate taxable Income -  Ysf modification
            for earning in self.earnings:
                if earning.is_tax_applicable:
                    taxable_income += earning.amount
            total_exemption_amount += max(
                0.21 * taxable_income, 16666.67 + 0.2 * taxable_income
            )

        return total_exemption_amount

    @frappe.whitelist()
    def get_field_days(self):
        # get onshore days from attendance
        self.onshore_days = len(
            frappe.get_all(
                "Attendance",
                filters={
                    "attendance_date": ["between", [self.start_date, self.end_date]],
                    "field_days": "onshore",
                    "employee": self.employee,
                    "docstatus": 1,
                },
            )
        )
        self.offshore_days = len(
            frappe.get_all(
                "Attendance",
                filters={
                    "attendance_date": ["between", [self.start_date, self.end_date]],
                    "field_days": "offshore",
                    "employee": self.employee,
                    "docstatus": 1,
                },
            )
        )
