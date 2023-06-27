
from erpnext.payroll.doctype.salary_slip.salary_slip import SalarySlip
import frappe


class TotalExemptionAmount(SalarySlip):
	def get_total_exemption_amount(self):
		total_exemption_amount = 0
		if self.tax_slab.allow_tax_exemption:
			if self.deduct_tax_for_unsubmitted_tax_exemption_proof:
				exemption_proof = frappe.db.get_value(
					"Employee Tax Exemption Proof Submission",
					{"employee": self.employee, "payroll_period": self.payroll_period.name, "docstatus": 1},
					["exemption_amount"],
				)
				if exemption_proof:
					total_exemption_amount = exemption_proof
			else:
				declaration = frappe.db.get_value(
					"Employee Tax Exemption Declaration",
					{"employee": self.employee, "payroll_period": self.payroll_period.name, "docstatus": 1},
					["total_exemption_amount"],
				)
				if declaration:
					total_exemption_amount = declaration
				total_exemption_amount += max(0.21 * self.gross_pay, 16666.7+0.02*self.gross_pay)
		return total_exemption_amount
	

