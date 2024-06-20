import json
import frappe
from frappe import _

@frappe.whitelist()
def add_log_based_on_employee_field():
   try:
      params = json.loads(frappe.request.data)
      employee_fieldname = "attendance_device_id"
      if not params["employee_field_value"] or not params["timestamp"]:
         frappe.throw(_("'employee_field_value' and 'timestamp' are required."))
      employee = frappe.db.get_values(
         "Employee",
         {employee_fieldname: params["employee_field_value"]},
         ["name", "employee_name", employee_fieldname],
         as_dict=True,
      )
      if employee:
         employee = employee[0] 
      else:
         frappe.throw(
            _("No Employee found for the given employee field value. '{}': {}").format(
               employee_fieldname, params["employee_field_value"]))
      doc = frappe.new_doc("Employee Checkin")
      doc.employee = employee.name
      doc.employee_name = employee.employee_name
      doc.time = params["timestamp"]
      doc.device_id = params["device_id"]
      doc.log_type = params["log_type"]
      doc.insert()

      return doc
   except Exception as err:
         frappe.log_error(frappe.get_traceback(), f'{err}')
      
@frappe.whitelist()
def bulkload_employee_checkin():
   data = json.loads(frappe.request.data)
   employee_fieldname = "attendance_device_id"
   checkin_records = []
   index = 0
   error_count = 0
   for item in data['record']:
      index += 1
      try:
         if not item["employee_field_value"] or not item["timestamp"]:
            frappe.throw(_("'employee_field_value' and 'timestamp' are required."))
         employee = frappe.db.get_values(
               "Employee",
               {employee_fieldname: item["employee_field_value"]},
               ["name", "employee_name", employee_fieldname],
               as_dict=True,
               )
         if employee:
            employee = employee[0] 
            doc = frappe.new_doc("Employee Checkin")
            doc.employee = employee.name
            doc.employee_name = employee.employee_name
            doc.time = item["timestamp"]
            doc.device_id = item["device_id"]
            doc.log_type = item["log_type"]
            if int(item["skip_auto_attendance"]) == 1:
               doc.skip_auto_attendance = "1"
            doc.insert()
            checkin_records.append(f"Checkin record {doc.name} created")
         else:
            frappe.throw(
               _("No Employee found for the given employee field value. '{}': {}").format(
                  employee_fieldname, item["employee_field_value"]
               )
            )
      except Exception as err:
         frappe.log_error(frappe.get_traceback(), f'{err} from file {data["filename"]}')
         checkin_records.append(f"Row {index} returned error: {err.args}")
         error_count += 1

   return (checkin_records, error_count)
