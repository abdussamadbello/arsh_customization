frappe.ui.form.on('Employee Advance', {
	refresh: function(frm) {
		frm.set_query("cost_center", function() {

			return {
				filters: {is_group: 0}
			};
		});
	},

	exchange_rate: function(frm) {
	    if(frm.doc.employee && frm.doc.exchange_rate !== 0){
	        frm.trigger('get_pending_amount');
	    }
	},

	get_pending_amount: function(frm) {
		frappe.call({
			method: "arsh_customization.arsh_customization.employee_advance.get_pending_amount",
			args: {
				"employee": frm.doc.employee,
				"posting_date": frm.doc.posting_date,
				"exchange_rate": frm.doc.exchange_rate,
			},
			callback: function(r) {
				frm.set_value("pending_amount", r.message);
			}
		});
	},

});
