// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt


frappe.ui.form.on("Timesheet", {
	refresh(frm) {
		frm.trigger("show_timesheet_warnings");
		frm.set_query("designation", "timelogs", function() {
			let designation_list = [];
			designation_list = frappe.call({
				method:"arsh_customization.arsh_customization.timesheet.get_permitted_designation",
				args: {employee:doc.employee, project:doc.project}
			})
			console.log(designation_list);
			return {
				filters: { "designation": ["in", designation_list] }
			};
		});
	},

	show_timesheet_warnings(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.dashboard.clear_headline();

			frm.call("get_timesheet_warnings").then((r) => {
				if (r.message?.length) {
					console.log(r.message);
					frm.dashboard.reset();
					frappe.require("arsh_customization.bundle.js", function () {
					frm.dashboard.add_section(
						frappe.render_template("timesheet_warnings", {
							warnings: r.message || [],
						}),
						__("Timesheet Warnings")
					);
				});
					frm.dashboard.show();
				}
			})
		}
	},

});

frappe.ui.form.on("Timesheet Detail", {

});
