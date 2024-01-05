from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):

    _inherit = "res.company"
    
    @api.model
    def update_gt_taxes(self):
        for company in self.env['res.company'].search([('chart_template', '=', 'gt')]):
            Template = self.env['account.chart.template'].with_company(company)
            Template._load_data({'account.tax': Template._get_gt_extra_account_tax()})
