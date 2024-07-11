// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Manpower Budget Variance Report"] = {
	filters: get_filters(),
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname.includes(__("variance"))) {
			if (data[column.fieldname] <= 0) {
				value = "<span style='color:red; background-color:pink;'>" + value + "</span>";
			} else if (data[column.fieldname] > 0) {
				value = "<span style='color:green; background-color:greenyellow;'>" + value + "</span>";
			}
		}

		return value;
	},
};
function get_filters() {

	let filters = [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Project", txt,filters={"status":"Open"})
			},
		},
		{
			fieldname: "group_by",
			label: __("Group by"),
			fieldtype: "Select",
			options: [
				"",
				{
					label: __("Group by Project"),
					value: 0,
				},
				{
					label: __("Group by Task"),
					value: 1,
				},
				{
					label: __("Group by Designation"),
					value: 2,
				},
			],
		},
	];

	return filters;
}
