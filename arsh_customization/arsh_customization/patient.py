import frappe
from healthcare.doctype.patient.patient import Patient


def make_invoice(patient, company):
    uom = frappe.db.exists("UOM", "Nos") or frappe.db.get_single_value(
        "Stock Settings", "stock_uom")
    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.customer = frappe.db.get_value(
        "Patient", patient, "customer")
    sales_invoice.due_date = getdate()
    sales_invoice.company = company
    sales_invoice.is_pos = 0
    sales_invoice.debit_to = get_receivable_account(company)
    sales_invoice.cost_center = frappe.db.get_value(
        "Company", company, "cost_center")

    item_line = sales_invoice.append("items")
    item_line.item_name = "Registration Fee"
    item_line.description = "Registration Fee"
    item_line.qty = 1
    item_line.uom = uom
    item_line.conversion_factor = 1
    item_line.income_account = get_income_account(None, company)
    item_line.rate = frappe.db.get_single_value(
        "Healthcare Settings", "registration_fee")
    item_line.amount = item_line.rate
    sales_invoice.set_missing_values()
    return sales_invoice
