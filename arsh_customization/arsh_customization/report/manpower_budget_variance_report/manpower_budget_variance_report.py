# Copyright (c) 2024, Optisol and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe import _
from frappe.utils import flt, cint

from erpnext.controllers.trends import get_period_date_ranges, get_period_month_ranges


def execute(filters=None):
	if not filters:
		filters = {}
	else:
		projects = filters.get("project") or []
		group_by = filters.get("group_by")

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
			"width": 200,
		},
		{
			"label": _("Designation"),
			"fieldname": "desination",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 300,
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
	
	data = []
	if projects:
		budget_record= get_budget_record(projects)
		if budget_record:
			data = get_actual_hours(budget_record)

	chart = get_chart_data(filters, columns, data)

	if group_by:
		grouped_data = group_data(data, cint(group_by))
		return columns, grouped_data, None, chart

	return columns, data, None, chart

def get_chart_data(filters, columns, data):

	if not data:
		return None

	labels = filters.get("project")

	no_of_columns = len(labels)

	budget_values, actual_values = [0] * no_of_columns, [0] * no_of_columns
	for d in data:
		for i in range(no_of_columns):
			if d[0] == labels[i]:
				budget_values[i] += d[3]
				actual_values[i] += d[4]
				
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Budget"), "chartType": "bar", "values": budget_values},
				{"name": _("Actual"), "chartType": "bar", "values": actual_values},
			],
		},
		"type": "bar",
	}

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

def group_data(data, group_by):
  if group_by not in (0, 1, 2):
    return

  # Sort data by the chosen field
  data.sort(key=lambda row: row[group_by])

  # Track current group and total
  current_group = None
  group_total = [0, 0, 0]
  result = []

  for row in data:
    # Check for group change and add total if needed
    if row[group_by] != current_group:
      if current_group is not None:
        result.append([None, None, f"Subtotal - {current_group}"] + group_total)
      current_group = row[group_by]
      group_total = [0, 0, 0]

    # Add current row, update total, and calculate each subtotal of the last 3 fields
    result.append(row)
    group_total = [a + b for a, b in zip (group_total, row[-3:])]

  # Add final group total if needed
  if current_group is not None:
    result.append([None, None, f"Subtotal - {current_group}"] + group_total)

  return result