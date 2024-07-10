# Copyright (c) 2024, Optisol and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe import _, _dict
from frappe.utils import flt, formatdate

from erpnext.controllers.trends import get_period_date_ranges, get_period_month_ranges


def execute(filters=None):
	if not filters:
		filters = {}

	# projects = ["PROJ-0007", "PROJ-0008","PROJ-0009"]
	columns = [
		{
			"label": _("Project"),
			"fieldtype": "Link",
			"fieldname": "project",
			"options": ("Project"),
			"width": 150,
		},
		{
			"label": _("Task"),
			"fieldname": "task",
			"fieldtype": "Link",
			"options": "Task",
			"width": 300,
		},
		{
			"label": _("Designation"),
			"fieldname": "desination",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 150,
		},
		{
			"label": _("Budget"),
			"fieldname": "budget",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Actual"),
			"fieldname": "actual",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Variance"),
			"fieldname": "variance",
			"fieldtype": "Float",
			"width": 150,
		},
	]
	projects = []
	if filters.get("project"):
		projects = filters.get("project")
	
	data = []
	if projects:
		budget_record= get_budget_record(projects)
		if budget_record:
			data = get_actual_hours(budget_record)

	chart = get_chart_data(filters, columns, data)

	return columns, data, None, chart


def get_chart_data(filters, columns, data):
	pass
	# if not data:
	# 	return None

	# labels = []
	# for year in fiscal_year:
	# 	for from_date, to_date in get_period_date_ranges(filters["period"], year[0]):
	# 		if filters["period"] == "Yearly":
	# 			labels.append(year[0])
	# 		else:
	# 			if group_months:
	# 				label = (
	# 					formatdate(from_date, format_string="MMM")
	# 					+ "-"
	# 					+ formatdate(to_date, format_string="MMM")
	# 				)
	# 				labels.append(label)
	# 			else:
	# 				label = formatdate(from_date, format_string="MMM")
	# 				labels.append(label)

	# no_of_columns = len(labels)

	# budget_values, actual_values = [0] * no_of_columns, [0] * no_of_columns
	# for d in data:
	# 	values = d[2:]
	# 	index = 0

	# 	for i in range(no_of_columns):
	# 		budget_values[i] += values[index]
	# 		actual_values[i] += values[index + 1]
	# 		index += 3

	# return {
	# 	"data": {
	# 		"labels": labels,
	# 		"datasets": [
	# 			{"name": _("Budget"), "chartType": "bar", "values": budget_values},
	# 			{"name": _("Actual Expense"), "chartType": "bar", "values": actual_values},
	# 		],
	# 	},
	# 	"type": "bar",
	# }

def get_budget_record(args:list) -> list:
	budget_record = frappe.db.get_all("Task Budget",
		filters={
			"docstatus":1, 
			"parent_project":["in", args]},
		fields=["parent_project", "task", "designation", "manhour"])
	processed_data = []
	seen =[]
	for item in budget_record:
		record= list(item.values()) 
		key= record[:3]  # Create a list of value of first 3 key-value pairs
		if not key in seen:
			seen.append(key)
			processed_data.append(record)
			continue
		for index, data in enumerate(processed_data):
			if  key != data[:3]:
				continue
			processed_data[index][3] += record[3]
			
	return processed_data

def get_actual_hours(budget_record):

	budget_variance = budget_record.copy()
	for index, item in enumerate(budget_record):
		actual_hours = 0
		hours_log = frappe.db.get_all("Timesheet Detail",
				filters={"project": item[0], "task":item[1], "designation":item[2], "docstatus":1,},
				fields=["hours"], pluck="hours")
		if hours_log:
			for hours in hours_log:
				actual_hours += flt(hours)
		budget_variance[index] += [actual_hours, item[3] - actual_hours]

	return budget_variance
			

	