
import frappe
from frappe import _
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from frappe.utils import add_days, date_diff, format_date, get_datetime, get_link_to_form

from erpnext.setup.doctype.employee.employee import is_holiday


class ArioshAttendanceRequest(AttendanceRequest):

    def on_cancel(self):
        attendance_list = frappe.get_all(
            "Attendance", {"employee": self.employee,
                           "attendance_request": self.name, "docstatus": 1}
        )
        if attendance_list:
            for attendance in attendance_list:
                attendance_obj = frappe.get_doc(
                    "Attendance", attendance["name"])
                attendance_obj.cancel()
        self.docstatus = 2

    def should_mark_attendance(self, attendance_date: str) -> bool:
        # Check if attendance_date is a holiday and override holiday is disables
        if (is_holiday(self.employee, attendance_date) and not self.override_holiday):
            frappe.msgprint(
                _("Attendance not submitted for {0} as it is a Holiday.").format(
                    frappe.bold(format_date(attendance_date))
                )
            )
            return False

        # Check if employee is on leave and override leave option disabled
        if (self.has_leave_record(attendance_date) and not self.override_leave):
            frappe.msgprint(
                _("Attendance not submitted for {0} as {1} is on leave.").format(
                    frappe.bold(format_date(attendance_date)
                                ), frappe.bold(self.employee)
                )
            )
            return False

        return True

    @frappe.whitelist()
    def get_attendance_warnings(self) -> list:
        attendance_warnings = []
        request_days = date_diff(self.to_date, self.from_date) + 1

        for day in range(request_days):
            attendance_date = add_days(self.from_date, day)
            if is_holiday(self.employee, attendance_date):
                if self.override_holiday:
                    attendance_warnings.append(
                        {"date": attendance_date, "reason": "Holiday", "action": "Overwrite"})
                else:
                    attendance_warnings.append(
                        {"date": attendance_date, "reason": "Holiday", "action": "Skip"})
            elif self.has_leave_record(attendance_date):
                if self.override_leave:
                    attendance_warnings.append(
                        {"date": attendance_date, "reason": "On Leave", "action": "Overwrite"})
                else:
                    attendance_warnings.append(
                        {"date": attendance_date, "reason": "On Leave", "action": "Skip"})
            else:
                attendance = self.get_attendance_record(attendance_date)
                if attendance:
                    attendance_warnings.append(
                        {
                            "date": attendance_date,
                            "reason": "Attendance already marked",
                            "record": attendance,
                            "action": "Overwrite",
                        }
                    )

        return attendance_warnings

    def create_or_update_attendance(self, date: str):
        attendance_name = self.get_attendance_record(date)
        status = self.get_attendance_status(date)
        field_days = self.get_field_days()

        if attendance_name:
            # update existing attendance, change the status
            doc = frappe.get_doc("Attendance", attendance_name)
            old_status = doc.status
            old_field_days = doc.field_days

            if (old_status != status or field_days != old_field_days):
                doc.db_set(
                    {"status": status, "attendance_request": self.name, "field_days": self.field_days})
                text = _("changed the status from {0} to {1} via Attendance Request").format(
                    frappe.bold(old_status), frappe.bold(status)
                )
                doc.add_comment(comment_type="Info", text=text)
                frappe.msgprint(
                    _("Updated status from {0} to {1} for date {2} in the attendance record {3}").format(
                        frappe.bold(old_status),
                        frappe.bold(status),
                        frappe.bold(format_date(date)),
                        get_link_to_form("Attendance", doc.name),
                    ),
                    title=_("Attendance Updated"),
                )
        else:
            # submit a new attendance record
            doc = frappe.new_doc("Attendance")
            doc.employee = self.employee
            doc.attendance_date = date
            doc.company = self.company
            doc.attendance_request = self.name
            doc.status = status
            doc.field_days = self.field_days
            doc.insert(ignore_permissions=True)
            doc.submit()

    def get_field_days(self):
        if self.field_days == "Onshore":
            return "Onshore"
        elif self.field_days == "Offshore":
            return "Offshore"


@frappe.whitelist()
def field_bulk_attendance(data):
    import json

    if isinstance(data, str):
        data = json.loads(data)
    data = frappe._dict(data)
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
        }
        attendance = frappe.get_doc(doc_dict).insert()
        attendance.submit()
