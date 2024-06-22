// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt


frappe.ui.form.on("Timesheet", {
	refresh: function (frm) {
		frm.trigger("show_timesheet_warnings");
	},

	show_timesheet_warnings(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.dashboard.clear_headline();

			frm.call("get_timesheet_warnings").then((r) => {
				if (r.message?.length) {
					frappe.require("arsh_customization.bundle.js")
					frm.dashboard.reset();
					frm.dashboard.add_section(
						frappe.render_template("timesheet_warnings", {
							warnings: r.message || [],
						}),
						__("Timesheet Warnings")
					);
					frm.dashboard.show();
				}
			})
		}
	},

});
