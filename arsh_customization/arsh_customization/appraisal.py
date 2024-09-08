import frappe
from frappe.utils import flt

from hrms.hr.doctype.appraisal.appraisal import Appraisal


class ArioshAppraisal(Appraisal):

	def calculate_final_score(self):
		kra_weight, feebback_weight, self_weight = frappe.db.get_value("Appraisal Template", 
				self.appraisal_template,["kra_weight, feedback_weight, self_appraisal_weight"])
		
		final_score = (flt(self.total_score) * kra_weight + 
				 flt(self.avg_feedback_score) * feebback_weight + 
				 flt(self.self_score) * self_weight ) / (kra_weight + feebback_weight + self_weight)

		self.final_score = flt(final_score, self.precision("final_score"))

