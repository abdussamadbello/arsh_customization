import json
import frappe
from frappe import _
from datetime import datetime

def get_employee_by_field(employee_fieldname, employee_field_value):
    """Helper function to fetch an employee based on a specific field."""
    employee = frappe.db.get_value(
        "Employee",
        {employee_fieldname: employee_field_value},
        ["name", "employee_name", employee_fieldname],
        as_dict=True,
    )
    if not employee:
        frappe.throw(
            _("No Employee found for the given employee field value. '{}': {}").format(
                employee_fieldname, employee_field_value
            )
        )
    return employee

def create_employee_checkin(employee, timestamp, device_id, log_type, skip_auto_attendance=False):
    """Helper function to create an Employee Checkin document."""
    doc = frappe.new_doc("Employee Checkin")
    doc.employee = employee.name
    doc.employee_name = employee.employee_name
    doc.time = timestamp
    doc.device_id = device_id
    doc.log_type = log_type
    doc.shift = "Regular"
    doc.skip_auto_attendance = "1" if skip_auto_attendance else "0"
    doc.insert()
    return doc

def parse_timestamp(timestamp_str):
    """Helper function to parse and validate the timestamp."""
    parsed_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    return parsed_time.strftime("%Y-%m-%d %H:%M:%S")

 
@frappe.whitelist()
def add_log_based_on_employee_field():
    try:
        params = json.loads(frappe.request.data)
        employee_fieldname = "attendance_device_id"

        # Validate input parameters
        if not params.get("employee_field_value"):
            frappe.throw(_("'employee_field_value' is required."))
        if not params.get("timestamp"):
            frappe.throw(_("'timestamp' is required."))

        timestamp = parse_timestamp(params["timestamp"])
        employee = get_employee_by_field(employee_fieldname, params["employee_field_value"])
        doc = create_employee_checkin(
            employee,
            timestamp,
            params.get("device_id"),
            params.get("log_type")
        )

        return {"status": "success", "message": f"Checkin record {doc.name} created"}
    except Exception as err:
        frappe.log_error(frappe.get_traceback(), f"Error: {str(err)}")
        frappe.throw(_("An error occurred while adding the log. Error: {}").format(str(err)))

@frappe.whitelist()
def bulkload_employee_checkin():
    try:
        data = json.loads(frappe.request.data)
        employee_fieldname = "attendance_device_id"
        checkin_records = []
        error_count = 0

        for index, item in enumerate(data.get('record', []), start=1):
            try:
                # Validate input parameters
                if not item.get("employee_field_value"):
                    frappe.throw(_("'employee_field_value' is required in row {}.").format(index))
                if not item.get("timestamp"):
                    frappe.throw(_("'timestamp' is required in row {}.").format(index))

                timestamp = parse_timestamp(item["timestamp"])
                employee = get_employee_by_field(employee_fieldname, item["employee_field_value"])
                doc = create_employee_checkin(
                    employee,
                    timestamp,
                    item.get("device_id"),
                    item.get("log_type"),
                    skip_auto_attendance=int(item.get("skip_auto_attendance", 0)) == 1
                )

                checkin_records.append(f"Row {index}: Checkin record {doc.name} created")
            except Exception as err:
                frappe.log_error(frappe.get_traceback(), f'Error in row {index}: {str(err)} in file {data.get("filename")}')
                checkin_records.append(f"Row {index}: Error - {str(err)}")
                error_count += 1

        return {"status": "completed", "records": checkin_records, "errors": error_count}
    except Exception as err:
        frappe.log_error(frappe.get_traceback(), f"Error: {str(err)}")
        frappe.throw(_("An error occurred during bulk loading employee checkins. Error: {}").format(str(err)))

