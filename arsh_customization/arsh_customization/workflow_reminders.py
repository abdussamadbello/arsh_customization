import frappe
from frappe import _
from datetime import datetime
from frappe.utils.background_jobs import enqueue
from frappe.workflow.doctype.workflow_action.workflow_action import (
     get_link_to_form, get_workflow_name,)
from frappe.utils.user import get_users_with_role

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
          
def get_supervisor(action_party) -> str:
    supervisor = []
    for party in action_party:
        supervisor_id = frappe.db.get_value("Employee", {"user_id":party}, "reports_to")
        if not supervisor_id:
            continue
        supervisor.append(frappe.db.get_value("Employee",supervisor_id, "user_id"))
    return supervisor

def send_email(doc, email_data:dict):
    common_args = get_common_email_args(doc)
    message = common_args.pop("message", None)
    if email_data.get("action") == "escalation":
         message = email_data.get("message")
    email_args = {
        "recipients": email_data.get("action_party"),
        "args": {"actions": [{"action_name": "Approve", "action_link": "Approve_Link"},
                             {"action_name": "Reject", "action_link": "Reject_Link"}],
                "message": message},
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

def get_email_template(doc):
	"""Returns next_action_email_template
	for workflow state (if available) based on doc current workflow state
	"""
	workflow_name = get_workflow_name(doc.get("doctype"))
	doc_state = doc.get("workflow_state")
	template_name = frappe.db.get_value(
		"Workflow Document State",
		{"parent": workflow_name, "state": doc_state},
		"next_action_email_template",
	)
	if not template_name:
		return
	return frappe.get_doc("Email Template", template_name)

if __name__ == "__main__":
    doc_list = frappe.db.get_list("Workflow",
                    {"is_active":1},"document_type", pluck="document_type")
    
    for doc_type in doc_list:
        overdue_list = get_overdue_doc(doc_type)
        if overdue_list == [] or None :
            continue
        for item in overdue_list:
            time_elapsed = datetime.now() - item.modified
            if time_elapsed.total_seconds()/3600 < 10 or time_elapsed.days > 7:
                continue
            doc = frappe.get_doc(doc_type, item.name)
            if time_elapsed.days < 2 and time_elapsed.seconds > 36_000:
                action_party = get_action_party(doc)
                email_data = {"action_party": action_party, "message": None, "action": "reminder"}
                enqueue(send_email, queue="short", doc=doc, email_data=email_data)
            else:
                message = f"""This is a reminder that  {frappe.bold(doc.doctype)} - '{doc.name}' is awaiting {action_party}'s action since {doc.modified.strftime('%Y-%m-%d %H:%M:%S')}.
                Please take necessary action to progress the document."""
                action_party = get_action_party(doc)
                supervisor = get_supervisor(action_party)
                email_data = {"action_party": supervisor, "message": message, "action": "escalation"}
                enqueue(send_email, queue="short", doc=doc, email_data=email_data)

