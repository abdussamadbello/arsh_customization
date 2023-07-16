app_name = "arsh_customization"
app_title = "Arsh Customization"
app_publisher = "Optisol"
app_description = "ARSH customization"
app_email = "optisol.ltd@gmail.com"
app_license = "MIT"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/arsh_customization/css/arsh_customization.css"
# app_include_js = "/assets/arsh_customization/js/arsh_customization.js"

# include js, css files in header of web template
# web_include_css = "/assets/arsh_customization/css/arsh_customization.css"
# web_include_js = "/assets/arsh_customization/js/arsh_customization.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "arsh_customization/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "arsh_customization.utils.jinja_methods",
#	"filters": "arsh_customization.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "arsh_customization.install.before_install"
# after_install = "arsh_customization.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "arsh_customization.uninstall.before_uninstall"
# after_uninstall = "arsh_customization.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "arsh_customization.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	# "ToDo": "custom_app.overrides.CustomToDo"
    "Salary Slip": "arsh_customization.overrides.salary_slip.TotalExemptionAmount",
    "Attendance Request": "arsh_customization.overrides.attendance.ArioshAttendanceRequest"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"arsh_customization.tasks.all"
#	],
#	"daily": [
#		"arsh_customization.tasks.daily"
#	],
#	"hourly": [
#		"arsh_customization.tasks.hourly"
#	],
#	"weekly": [
#		"arsh_customization.tasks.weekly"
#	],
#	"monthly": [
#		"arsh_customization.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "arsh_customization.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "arsh_customization.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "arsh_customization.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["arsh_customization.utils.before_request"]
# after_request = ["arsh_customization.utils.after_request"]

# Job Events
# ----------
# before_job = ["arsh_customization.utils.before_job"]
# after_job = ["arsh_customization.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"arsh_customization.auth.validate"
# ]
