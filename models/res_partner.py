# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

class ResPartner(models.Model):
    _inherit = "res.partner"

    cui = fields.Char(string="CUI")
    pequenio_contribuyente = fields.Boolean(string="Pequeño Contribuyente")

    def check_vat_gt(self, vat):
        if vat == 'CF' or vat == 'C/F' or not vat:
            return True

        # Si es un CUI no validarlo
        if len(vat) > 9:
            return True

        nit = vat.replace('-','')
        verificador = nit[-1]
        if verificador == 'K':
            verificador = '10'
        secuencia = nit[:-1]

        total = 0
        i = 2
        for c in secuencia[::-1]:
            total += int(c) * i
            i += 1

        resultante = ( 11 - ( total % 11 ) ) % 11

        if str(resultante) != verificador:
            return False
            
        return True
