// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Entry", {

	refresh: function(frm) {
		if(frm.doc.status != 'Submitted') {
			frm.add_custom_button(__('Withhold All Taxes'), function(){
				let allocated = 0;
				let exch = frm.doc.paid_from_account_currency == "NGN" ? 1 : frm.doc.source_exchange_rate
				for(let row of frm.doc.references) {
					allocated += row.allocated_amount
				}
				let payment_type = frm.doc.payment_type  == "Receive" ? 1 
								  : frm.doc.payment_type  == "Pay" ? -1 :  0;
				if (allocated > frm.doc.paid_amount){
					let vatAmount = (0.06976744186 * payment_type * allocated * exch).toFixed(2);
					let whtAmount = (0.05 * payment_type * (allocated * exch - payment_type * vatAmount)).toFixed(2);
					let ncdAmount = (0.01 * payment_type * (allocated * exch - payment_type * vatAmount)).toFixed(2);
					let taxes = [{
						account: '1520 - VAT - Optimum',
						cost_center: frm.doc.cost_center,
						amount: vatAmount},
						{account: '1521 - WHT - Optimum',
						cost_center: frm.doc.cost_center,
						amount: whtAmount},
						{account: '5293 - NCD Tax Expense - Optimum',
						cost_center: frm.doc.cost_center,
						amount: ncdAmount},                  
					];
					frm.doc.deductions = []
					for (let row of taxes){
						frm.add_child('deductions',row)
						frappe.msgprint(`${row.amount} added to ${row.account} Account`);
					}
					frm.refresh_field('deductions');
				}
			}, __("Apply Deductions"));
		  
			frm.add_custom_button(__('Withhold VAT'), function(){
				let allocated = 0;
				for(let row of frm.doc.references) {
					allocated += row.allocated_amount;
				}
				let payment_type = frm.doc.payment_type  == "Receive" ? 1 
								  : frm.doc.payment_type  == "Pay" ? -1 :  0;
				if (allocated > frm.doc.paid_amount){
					let vatAmount = (0.06976744186 * payment_type * allocated * exch).toFixed(2);
					let taxes = 
					frm.doc.deductions = [];
					frm.add_child('deductions',{
						account: '159010 - Input VAT Recoverable - ARSH',
						cost_center: frm.doc.cost_center,
						amount: vatAmount}
					);
					frappe.msgprint('VAT withheld to account "159010 - Input VAT Recoverable - ARSH" ');
					}
					frm.refresh_field('deductions');
			}, __("Apply Deductions"));
			}
		frm.set_query("reference_doctype", "references", function() {
			let doctypes = [];

			if (frm.doc.party_type == "Customer") {
				doctypes = ["Sales Order", "Sales Invoice", "Journal Entry", "Dunning"];
			} else if (frm.doc.party_type == "Supplier") {
				doctypes = ["Purchase Order", "Purchase Invoice", "Journal Entry"];
			} else if (frm.doc.party_type == "Employee") {
				doctypes = ["Employee Advance", "Expense Claim", "Journal Entry"];
			} else {
				doctypes = ["Journal Entry"];
			}

			return {
				filters: { "name": ["in", doctypes] }
			};
		});

		frm.set_query("reference_name", "references", function(doc, cdt, cdn) {
			const child = locals[cdt][cdn];
			const filters = {"docstatus": 1, "company": doc.company};
			const party_type_doctypes = ["Sales Invoice", "Sales Order", "Purchase Invoice",
				"Purchase Order", "Expense Claim", "Dunning", "Employee Advance"];

			if (in_list(party_type_doctypes, child.reference_doctype)) {
				filters[doc.party_type.toLowerCase()] = doc.party;
			}

			if (child.reference_doctype == "Expense Claim") {
				filters["docstatus"] = 1;
				filters["is_paid"] = 0;
			}

			return {
				filters: filters
			};
		});
	},

})

frappe.ui.form.on("Payment Entry Reference", {
	reference_name: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.reference_name && row.reference_doctype) {
			return frappe.call({
				method: "arsh_customization.arsh_customization.employee_advance.get_payment_reference_details",
				args: {
					reference_doctype: row.reference_doctype,
					reference_name: row.reference_name,
					party_account_currency: (frm.doc.payment_type == "Receive") ?
						frm.doc.paid_from_account_currency : frm.doc.paid_to_account_currency
				},
				callback: function(r, rt) {
					if (r.message) {
						$.each(r.message, function(field, value) {
							frappe.model.set_value(cdt, cdn, field, value);
						})

						let allocated_amount = frm.doc.unallocated_amount > row.outstanding_amount ?
							row.outstanding_amount : frm.doc.unallocated_amount;

						frappe.model.set_value(cdt, cdn, "allocated_amount", allocated_amount);
						frm.refresh_fields();
					}
				}
			})
		}
	},
})