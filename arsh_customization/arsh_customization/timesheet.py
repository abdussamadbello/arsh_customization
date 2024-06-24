import frappe
from frappe import _
from frappe.utils import flt
from erpnext.projects.doctype.timesheet.timesheet import Timesheet
from arsh_customization.arsh_customization.doctype.manpower_budget.manpower_budget import (
    validate_hours_against_manhours, get_budget_hours, get_actual_hours, get_budget_record)

class ArioshTimesheet(Timesheet):
    def validate(self):
        self.set_status()
        self.validate_dates()
        self.validate_time_logs()
        self.validate_manhour()
        self.update_cost()
        self.calculate_total_amounts()
        self.calculate_percentage_billed()
        self.set_dates()
    
    def validate_manhour(self):
        if self.docstatus == 0:
            if self.parent_project:
                self.validate_project_user()

            for data in self.get("time_logs"):
                if data.project:
                    validate_designation(self.employee, data.designation, data.project)
                    validate_task(data.project, data.task)
                    args = data.as_dict()
                    args.update({"company": self.company, "employee": self.employee})
                    validate_hours_against_manhours(args)
                    
    def validate_project_user(self):
        # throw error if employee UID is not in project user list

        project_user = frappe.db.get_all("Project User",
            filters={"parent": self.parent_project}, fields=["user"], pluck="user") or []
   
        employee_user = frappe.db.get_value("Employee", self.employee, "user_id") or "unset"

        if employee_user not in project_user:
            frappe.throw(_("Employee {0} is not assigned to project {1}. Update the project user list"
                ).format(frappe.bold(self.employee), frappe.bold(self.parent_project)), title=_("Unassigned User Error"))
  
    @frappe.whitelist()
    def get_timesheet_warnings(self) -> list:
        if not self.get("parent_project"):
            return
        
        timesheet_warnings = []   
        for log in self.time_logs:
            args = log.as_dict()
            progress = frappe.get_value("Task", args.task, "progress")
            args.update({"company": self.company, "employee": self.employee, "progress": progress})
            budget_record, project_budget = get_budget_record(args)
            budget_hours = get_budget_hours(budget_record)
            actual_hours = get_actual_hours(args)
            total_hours = actual_hours + flt(args.hours)
            warning_threshold = flt(project_budget["trigger_alert_percentage"])
            spend = total_hours * 100 / budget_hours
            performance = progress * 100 /spend
            msg, color_code = compare_partial_budget(args, budget_hours, actual_hours, total_hours, warning_threshold)
            if msg:
                timesheet_warnings.append(
                    {"task": args.task, "designation": args.designation, "earned": args.progress,"spend":f'{spend:.2f}', 
                     "performance": f'{performance:.2f}', "warning": msg, "budget": budget_hours, 
                     "hours_before_approval": actual_hours, "hour_after_approval": total_hours, "color_code" : color_code})
        return timesheet_warnings

def validate_designation(employee, designation, project):
    permitted_designation = get_permitted_designation(employee, project)
    if designation not in permitted_designation:   
        frappe.throw(_("Employee {0} is not assigned as {1} to project {2}. Contact Project Manager"
            ).format(frappe.bold(employee), frappe.bold(designation), frappe.bold(project)),
            title=_("Unassigned Designation Error"))

def validate_task(project, task):
    if not task:
        frappe.throw(_("Task field is mandatory"), title=_("Task Error")) 
    
    project_task = frappe.db.get_value("Task", task, "project")
    if project_task != project:   
        frappe.throw(_("Task {0} is not part of {1} project"
            ).format(frappe.bold(task), frappe.bold(project)),
            title=_("Task Error"))

def compare_partial_budget(args, budget_hours, actual_hours, total_hours, warning_threshold):
    threshold_hours = warning_threshold * budget_hours / 100
    earned_hours = budget_hours * args.progress / 100
    msg = None
    color_code = None
    if total_hours > threshold_hours:
        if actual_hours > threshold_hours:
            tense = "is already"
            diff = actual_hours - threshold_hours
        else:
            tense = "will be"
            diff = total_hours - threshold_hours

        msg = _("Budget warning threshold is {0} and {1} exceeded by {2}. <br> \
                Actual hours will be {3} , budget hours is {4} and remaining budget is {5}").format(
            frappe.bold(threshold_hours), tense, frappe.bold(diff), frappe.bold(total_hours),
            frappe.bold(budget_hours), frappe.bold(budget_hours - total_hours))
        color_code = "lightpink"

    elif total_hours > earned_hours:
        diff = total_hours - earned_hours
        msg = _("Actual hours will be {0} and it will exceed earned hours({1}) by {2}").format(
            frappe.bold(total_hours), frappe.bold(earned_hours), frappe.bold(diff))   
        color_code = "khaki"    
    return (msg, color_code)

@frappe.whitelist()   
def get_permitted_designation(employee, project):
    primary_designation = frappe.db.get_value("Employee", employee, "designation") or "nil"
    permitted_designation = frappe.db.get_all("Permitted Designation",
        filters={"employee": employee, "parent": project}, fields=["designation"], pluck="designation") or []
    permitted_designation.append(primary_designation)
    return permitted_designation
