

import frappe
from frappe import _
from frappe.utils import flt

import erpnext
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

from hrms.hr.doctype.expense_claim.expense_claim import get_outstanding_amount_for_claim

class ArioshPaymentEntry(PaymentEntry):
	def validate_allocated_amount(self):
		if self.payment_type == "Internal Transfer":
			return

		if self.party_type in ("Customer", "Supplier"):
			self.validate_allocated_amount_with_latest_data()
		else:
			fail_message = _("Row #{0}: Allocated Amount cannot be greater than outstanding amount.")
			for d in self.get("references"):
				if d.reference_doctype == "Employee Advance":
					res = get_reference_details_for_employee("Employee Advance", d.reference_name, self.party_account_currency)

					if (flt(d.allocated_amount)) > 0 and flt(d.allocated_amount) > flt(res.outstanding_amount):
						frappe.throw(fail_message.format(d.idx))

					if flt(d.allocated_amount) < 0 and flt(d.allocated_amount) < flt(res.outstanding_amount):
						frappe.throw(fail_message.format(d.idx))

				elif (flt(d.allocated_amount)) > 0 and flt(d.allocated_amount) > flt(d.outstanding_amount):
					frappe.throw(fail_message.format(d.idx))

				# Check for negative outstanding invoices as well
				elif flt(d.allocated_amount) < 0 and flt(d.allocated_amount) < flt(d.outstanding_amount):
					frappe.throw(fail_message.format(d.idx))

	def get_valid_reference_doctypes(self):
		if self.party_type == "Customer":
			return ("Sales Order", "Sales Invoice", "Journal Entry", "Dunning")
		elif self.party_type == "Supplier":
			return ("Purchase Order", "Purchase Invoice", "Journal Entry")
		elif self.party_type == "Shareholder":
			return ("Journal Entry",)
		elif self.party_type == "Employee":
				return ("Journal Entry", "Employee Advance", "Expense Claim")

@frappe.whitelist()
def get_pending_amount(employee, posting_date, exchange_rate):
	employee_due_amount = frappe.get_all(
		"Employee Advance",
		filters={"employee": employee, "docstatus": 1, "posting_date": ("<=", posting_date)},
		fields=["advance_amount", "paid_amount", "exchange_rate"],
	)
	pending_amount = 0
	
	for emp in employee_due_amount:
		pending_amount += emp.exchange_rate*(emp.advance_amount - emp.paid_amount)

	return (pending_amount / float(exchange_rate))

@frappe.whitelist()
def get_reference_details_for_employee(reference_doctype, reference_name, party_account_currency):
	"""
	Returns payment reference details for employee related doctypes:
	Employee Advance, Expense Claim, Gratuity
	"""

	total_amount = outstanding_amount = exchange_rate = None

	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	company_currency = ref_doc.get("company_currency") or erpnext.get_company_currency(
		ref_doc.company
	)

	total_amount, exchange_rate = get_total_amount_and_exchange_rate(
		ref_doc, party_account_currency, company_currency
	)

	if reference_doctype == "Expense Claim":
		outstanding_amount = get_outstanding_amount_for_claim(ref_doc)
	elif reference_doctype == "Employee Advance":
		outstanding_amount = flt(ref_doc.advance_amount) - flt(ref_doc.paid_amount)
		if party_account_currency != ref_doc.currency:
			outstanding_amount = flt(outstanding_amount) * flt(exchange_rate)
	elif reference_doctype == "Gratuity":
		outstanding_amount = ref_doc.amount - flt(ref_doc.paid_amount)
	else:
		outstanding_amount = flt(total_amount) - flt(ref_doc.advance_paid)

	return frappe._dict(
		{
			"due_date": ref_doc.get("due_date"),
			"total_amount": flt(total_amount),
			"outstanding_amount": flt(outstanding_amount),
			"exchange_rate": flt(exchange_rate),
		}
	)


def get_total_amount_and_exchange_rate(ref_doc, party_account_currency, company_currency):
	
	total_amount = exchange_rate = None

	if ref_doc.doctype == "Expense Claim":
		total_amount = flt(ref_doc.total_sanctioned_amount) + flt(ref_doc.total_taxes_and_charges)
	elif ref_doc.doctype == "Employee Advance":
		total_amount = ref_doc.advance_amount
		exchange_rate = ref_doc.get("exchange_rate")
		if party_account_currency != ref_doc.currency:
			total_amount = flt(total_amount) * flt(exchange_rate)
		# Remove last part (unnecessary) of this code
		# if party_account_currency == company_currency:
		# 	exchange_rate = 1

	elif ref_doc.doctype == "Gratuity":
		total_amount = ref_doc.amount

	if not total_amount:
		if party_account_currency == company_currency:
			total_amount = ref_doc.base_grand_total
			exchange_rate = 1
		else:
			total_amount = ref_doc.grand_total

	if not exchange_rate:
		# Get the exchange rate from the original ref doc
		# or get it based on the posting date of the ref doc.
		exchange_rate = ref_doc.get("conversion_rate") or get_exchange_rate(
			party_account_currency, company_currency, ref_doc.posting_date
		)

	return total_amount, exchange_rate