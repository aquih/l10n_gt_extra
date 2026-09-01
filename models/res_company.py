from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = "res.company"
    
    def cargar_impuestos(self):
        for company in self:
            Template = self.env['account.chart.template'].with_company(company)
            impuestos = Template._get_gt_extra_account_tax()
            Template._load_data({'account.tax': impuestos})

    def cargar_impuestos_globales(self):
        for company in self:
            Template = self.env['account.chart.template'].with_company(company)
            impuestos = Template._get_gt_extra_account_tax()
            impuestos_globales = {k: impuestos[k] for k in ['impuestos_plantilla_iva_retencion_global', 'impuestos_plantilla_isr_retencion_global'] if k in impuestos}
            Template._load_data({'account.tax': impuestos_globales})
