import frappe
from frappe import _
from frappe.utils import add_days, date_diff, getdate
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from erpnext.setup.doctype.employee.employee import is_holiday
from frappe.utils import get_datetime, getdate


class ArioshAttendanceRequest(AttendanceRequest):
    def on_cancel(self):
        attendance_list = frappe.get_list(
            "Attendance", {"employee": self.employee, "attendance_request": self.name}
        )
        if attendance_list:
            for attendance in attendance_list:
                attendance_obj = frappe.get_doc("Attendance", attendance["name"])
                attendance_obj.cancel()
        self.docstatus = 2
        self.status = "Cancelled"

    def create_attendance(self):
        request_days = date_diff(self.to_date, self.from_date) + 1
        for number in range(request_days):
            attendance_date = add_days(self.from_date, number)
            skip_attendance = self.validate_if_attendance_not_applicable(
                attendance_date
            )
            if not skip_attendance:
                attendance = frappe.new_doc("Attendance")
                attendance.employee = self.employee
                attendance.employee_name = self.employee_name
                if (
                    self.half_day
                    and date_diff(getdate(self.half_day_date), getdate(attendance_date))
                    == 0
                ):
                    attendance.status = "Half Day"
                elif self.reason == "Work From Home":
                    attendance.status = "Work From Home"
                else:
                    attendance.status = "Present"
                if self.field_days:
                    attendance.field_days = self.field_days
                attendance.attendance_date = attendance_date
                attendance.company = self.company
                attendance.attendance_request = self.name
                attendance.save(ignore_permissions=True)
                attendance.submit()

    def validate_if_attendance_not_applicable(self, attendance_date):
        # Check if attendance_date is a Holiday
        if is_holiday(self.employee, attendance_date) and not self.override_holiday:
            frappe.msgprint(
                _("Attendance not submitted for {0} as it is a Holiday.").format(
                    attendance_date
                ),
                alert=1,
            )
            return True

        # Check if employee on Leave
        leave_record = frappe.db.sql(
            """select half_day from `tabLeave Application`
			where employee = %s and %s between from_date and to_date
			and docstatus = 1""",
            (self.employee, attendance_date),
            as_dict=True,
        )
        if leave_record and not self.override_leave:
            frappe.msgprint(
                _("Attendance not submitted for {0} as {1} on leave.").format(
                    attendance_date, self.employee
                ),
                alert=1,
            )
            return True

        return False


@frappe.whitelist()
def field_bulk_attendance(data):
    import json

    if isinstance(data, str):
        data = json.loads(data)
    data = frappe._dict(data)
    company = frappe.get_value("Employee", data.employee, "company")
    if not data.unmarked_days:
        frappe.throw(_("Please select a date."))
        return

    for date in data.unmarked_days:
        doc_dict = {
            "doctype": "Attendance",
            "employee": data.employee,
            "attendance_date": get_datetime(date),
            "status": data.status,
            "field_days": data.field_days,
            "company": company,
        }
        attendance = frappe.get_doc(doc_dict).insert()
        attendance.submit()
