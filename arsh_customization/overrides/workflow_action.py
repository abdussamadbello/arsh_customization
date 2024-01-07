import frappe
from frappe import _
from frappe.workflow.doctype.workflow_action.workflow_action import WorkflowAction
from frappe.workflow.doctype.workflow_action.workflow_action import get_workflow_name, \
    clear_workflow_actions, is_workflow_action_already_created, update_completed_workflow_actions, \
    clear_doctype_notifications, get_next_possible_transitions, get_doc_workflow_state, \
    get_users_next_action_data, create_workflow_actions_for_roles, send_email_alert, \
    send_workflow_action_email
from frappe.utils.background_jobs import enqueue


class CustomWorkflowAction(WorkflowAction):

    def process_workflow_actions(self, doc, state):

        workflow = get_workflow_name(doc.get("doctype"))
        if not workflow:
            return

        if state == "on_trash":
            clear_workflow_actions(doc.get("doctype"), doc.get("name"))
            return

        if is_workflow_action_already_created(doc):
            return

        update_completed_workflow_actions(
            doc, workflow=workflow, workflow_state=get_doc_workflow_state(doc)
        )
        clear_doctype_notifications("Workflow Action")

        next_possible_transitions = get_next_possible_transitions(
            workflow, get_doc_workflow_state(doc), doc
        )

        if not next_possible_transitions:
            return

        user_data_map, roles = get_users_next_action_data(
            next_possible_transitions, doc)

        if not user_data_map:
            return

        create_workflow_actions_for_roles(roles, doc)

        if roles == {'Cost Center Manager'} or roles == {'Expense Approver'}:
            cost_manager = frappe.get_value(
                doc.doctype, doc.name, 'cost_manager')
            user_data_map = user_data_map.get(cost_manager, {})

        if send_email_alert(workflow):
            enqueue(
                send_workflow_action_email, queue="short", users_data=list(user_data_map.values()), doc=doc
            )
