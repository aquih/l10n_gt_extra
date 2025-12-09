from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = "product.template"
    
    tasa_de_conversion = fields.Float(string="Tasa de conversion")
