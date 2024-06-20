# Copyright (c) 2024, Optisol and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class ManBudgetError(frappe.ValidationError):
	pass

class DuplicateManBudgetError(frappe.ValidationError):
	pass

class ManpowerBudget(Document):
	def validate(self):
		if not self.get(frappe.scrub("project")):
			frappe.throw(_("Project is mandatory"))
		if not self.is_supplement:
			self.validate_duplicate()
		self.validate_tasks()

	def validate_duplicate(self):
		for task in self.tasks:
			existing_budget = frappe.db.get_value("Task Budget", 
				{"docstatus":1, "task":task.task, "designation":task.designation},
				"parent")
			
			if existing_budget:
				frappe.throw(
				_("Approved Budget {0} already exists for {1} against {2}"
				).format(frappe.bold(existing_budget), frappe.bold(task.designation), frappe.bold(task.task)),
				DuplicateManBudgetError,title=_("Duplicate Budget Error"))
        
	def validate_tasks(self):
		task_list = []
		for d in self.get("tasks"):
			if d.task:
				task_details = frappe.db.get_value("Task", d.task, ["is_group", "company", "status"], as_dict=1)

				if task_details.is_group:
					frappe.throw(_("Hours cannot be allocated to Group Task {0}").format(frappe.bold(d.task)))
				elif task_details.company != self.company:
					frappe.throw(_("task {0} does not belongs to company {1}"
					).format(frappe.bold(d.task), frappe.bold(self.company)))
				elif task_details.status in ["Template", "Completed", "Cancelled"]:
					frappe.throw(_("Cannot budget against task {0} with status {1}"
					).format(frappe.bold(d.task), frappe.bold(task_details.status)))

				if d.task + " " + d.designation in task_list:
					frappe.throw(_("Task {0} and designation {1} have been entered multiple times"
					).format(frappe.bold(d.task), frappe.bold(d.designation)))
				else:
					task_list.append(d.task + " " + d.designation)				

def validate_hours_against_manhours(args):
	budget_record, project_recocrd = get_budget_record(args)
	if budget_record:
		validate_budget_records(args, budget_record, project_recocrd)

	else:
		msg = _("No approved budget for {0} against task {1} of project {2}.").format(
			frappe.bold(args.designation),frappe.bold(args.task),frappe.bold(args.project_name),)
		frappe.throw(msg, ManBudgetError, title=_("No Budget"))

def validate_budget_records(args, budget_record, project_record):

	def compare_hours_with_budget(budget_hours,actual_hours, total_hours, action):
		if total_hours > budget_hours:
			if actual_hours > budget_hours:
				error_tense = _("is already")
				diff = actual_hours - budget_hours
			else:
				error_tense = _("will be")
				diff = total_hours - budget_hours

			msg = _("{0} Budget for Task {1} against {2} is {3}. It {4} exceed by {5}").format(
				frappe.bold(args.designation),frappe.bold(args.task),frappe.bold(budget_record[0].parent),
				frappe.bold(budget_hours),error_tense,frappe.bold(diff),)

			if (frappe.flags.exception_approver_role
				and frappe.flags.exception_approver_role in frappe.get_roles(frappe.session.user)):
				action = "Warn"

			if action == "Stop":
				frappe.throw(msg, ManBudgetError, title=_("Budget Exceeded"))
			else:
				frappe.msgprint(msg, indicator="orange", title=_("Budget Exceeded"))

	budget_hours = get_budget_hours(budget_record)
	actual_hours =  get_actual_hours(args)
	total_hours =  actual_hours + flt(args.hours)
	action = project_record.action_if_total_manhour_exceeded
	#action = frappe.db.get_value ("Manpower Budget", budget_record[0].parent, "action_if_total_manhour_exceeded")
	if action in ("Stop", "Warn"):
		compare_hours_with_budget(budget_hours, actual_hours, total_hours, action)

def get_budget_hours(budget_record):
	budget_hours = 0
	for record in budget_record:
		budget_hours += record.manhour
	return budget_hours
@frappe.whitelist()
def get_actual_hours(args):
	actual_hours = 0
	hours_log = frappe.db.get_all("Timesheet Detail",
			filters={"task":args.task, "designation":args.designation, "docstatus":1,},
			fields=["hours"], pluck="hours")
	if hours_log:
		for hours in hours_log:
			actual_hours += flt(hours)
		return actual_hours
	else:
		return 0

def get_budget_record(args):
	#returns of tuple containing budget_record (list) and project_budget (frappe.dict)
	args = frappe._dict(args)
	project_budget = frappe.db.get_value("Manpower Budget",
		{"project":args.project, "docstatus":1, "is_supplement":0},
		["name","applicable_on_booking_actual_hours", "action_if_total_manhour_exceeded","trigger_alert_percentage"], as_dict=1)  
	if not project_budget:
		frappe.throw("No approved budget for project {}".format(frappe.bold(args.project)),
			   ManBudgetError, title=_("No Budget"))

	if project_budget.applicable_on_booking_actual_hours == 0:
		return
	
	budget_record = frappe.db.get_all("Task Budget",
		{"docstatus":1, "task":args.task, "designation":args.designation, "parent_project":args.project},
		["task", "designation", "manhour","parent"],)
	
	return (budget_record, project_budget)