# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.workflow import get_workflow_name
from frappe.workflow.doctype.workflow_action.workflow_action import (
	is_workflow_action_already_created,
	update_completed_workflow_actions,
	get_next_possible_transitions,
	create_workflow_actions_for_roles,
	get_workflow_action_url,
	get_email_template
)
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import get_link_to_form
from frappe.utils.user import get_users_with_role
from datetime import datetime

def process_workflow_actions(doc, workflow_state):
	workflow = get_workflow_name(doc.get("doctype"))

	if is_workflow_action_already_created(doc):
		return

	update_completed_workflow_actions(doc, workflow=workflow, workflow_state=workflow_state)
	clear_doctype_notifications("Workflow Action")

	next_possible_transitions = get_next_possible_transitions(workflow, workflow_state, doc)

	if not next_possible_transitions:
		return

	roles = {t.allowed for t in next_possible_transitions}
	create_workflow_actions_for_roles(roles, doc)



def send_workflow_action_email(doc, user, msg, action):

	common_args = get_common_email_args(doc)
	message = common_args.pop("message", None)
	email, cc_email = (user, None)
	if action == "escalation":
		message = msg
		email = get_supervisor(user)
		cc_email = user
	email_args = {
		"recipients": email,
        "cc": cc_email,
		"args": {"actions":[
					{"action_name": "Approve",	"action_link": get_workflow_action_url("Approve", doc, user),},
					{"action_name": "Reject",	"action_link": get_workflow_action_url("Reject", doc, user),}],
                "message": message,
                },
		"reference_name": doc.name,
		"reference_doctype": doc.doctype,
	}
	email_args.update(common_args)
	try:
		frappe.sendmail(**email_args)
	except frappe.OutgoingEmailError:
		# Emails config broken, don't bother retrying next user.
		frappe.log_error("Failed to send workflow action email")
		return

def get_common_email_args(doc):
	doctype = doc.get("doctype")
	docname = doc.get("name")

	email_template = get_email_template(doc)
	if email_template:
		subject = frappe.render_template(email_template.subject, vars(doc))
		response = frappe.render_template(email_template.response, vars(doc))
	else:
		subject = _("Workflow Action") + f" on {doctype}: {docname}"
		response = get_link_to_form(doctype, docname, f"{doctype}: {docname}")

	print_format = doc.meta.default_print_format
	lang = doc.get("language") or (
		frappe.get_cached_value("Print Format", print_format, "default_print_language")
		if print_format
		else None
	)

	return {
		"template": "workflow_action",
		"header": "Workflow Action",
		"attachments": [
			frappe.attach_print(
				doctype,
				docname,
				file_name=docname,
				doc=doc,
				lang=lang,
				print_format=print_format,
			)
		],
		"subject": subject,
		"message": response,
	}

def get_overdue_doc(doc_type):
    overdue_list = frappe.db.get_list(doc_type,{"workflow_state":["like", "%Pending%"]}, 
        ["name", "cost_manager", "expense_approver", "workflow_state",] )
    
    return overdue_list

def get_action_party(doc) -> list[str]:
     if doc.workflow_state in ["Pending HOD Approval"]:
          return ([doc.expense_approver])
     elif doc.workflow_state == "Pending Cost Center Approval":
          return ([doc.expense_approver])
     else:
          role_map = {"Pending HRM Approval": "HR Manager",
                      "Pending Compliance Approval": "Compliance Approval",
                      "Pending Sales Approval": "Sales Manager",
                      "Pending CFO Approval": "CFO",
                      "Pending Account Approval": "Accounts Manager",
                      "Pending Procurement Approval":"Purchase Manager",
                      "Pending MD Approval": "MD",
                      "Pending COO Approval": "COO",}
          return get_users_with_role (role_map.get(doc.workflow_state))

def get_supervisor(user) -> str:
	supervisor_id = frappe.db.get_value("Employee", {"user_id":user}, "reports_to")
	if not supervisor_id:
		return
	return frappe.db.get_value("Employee",supervisor_id, "user_id")   

if __name__ == "__main__":
    doc_list = frappe.db.get_list("Workflow",
                    {"is_active":1},"document_type", pluck="document_type")
    
    for doc_type in doc_list:
        overdue_list = get_overdue_doc(doc_type)
        if overdue_list == [] or None :
            continue
        for item in overdue_list:
            doc = frappe.get_doc(doc_type, item.name)
            time_elapsed = datetime.now() - item.modified
            if time_elapsed.total_seconds() < 36_000 or time_elapsed.days > 10:
                process_workflow_actions(doc, item.workflow_state)
                continue
            user = get_action_party(doc)
            message, action= (None, None)
            if time_elapsed.total_seconds()/3600 >= 10 and time_elapsed.days <= 2:
                message = f"""
				This is a reminder that  {frappe.bold(doc.doctype)} - '{doc.name}' is awaiting {user}'s action since {doc.modified.strftime('%Y-%m-%d %H:%M:%S')}.
                Please take necessary action to progress the document."""
                action = "escalation"
                
            enqueue(send_workflow_action_email, queue="short", doc=doc, user=user, msg=message, action=action)

