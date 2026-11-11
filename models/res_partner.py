# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

class ResPartner(models.Model):
    _inherit = "res.partner"

    cui = fields.Char(string="CUI")
    pequenio_contribuyente = fields.Boolean(string="Pequeño Contribuyente")