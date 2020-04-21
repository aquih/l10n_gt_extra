# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

class ResPartner(models.Model):
    _inherit = "res.partner"

    cui = fields.Char(string="CUI")
    no_validar_nit = fields.Boolean(string="No validar NIT")
    pequenio_contribuyente = fields.Boolean(string="Pequeño Contribuyente")

    @api.constrains('vat')
    def _validar_nit(self):
        for p in self:
            if p.vat == 'CF' or p.vat == 'C/F' or not p.vat:
                return True

            if p.country_id and p.country_id.code != 'GT':
                return True

            if p.no_validar_nit:
                return True

            # No validar NIT si el partner fue creado desde un sitio web, para evitar errores
            if 'website_id' in p.env.context:
                return True

            nit = p.vat.replace('-','')
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
                raise ValidationError("El NIT " + p.vat + " no es correcto (según lineamientos de la SAT)")

    @api.constrains('vat')
    def _validar_duplicado(self):
        for p in self:
            # No validar NIT si el partner fue creado desde un sitio web, para evitar errores
            if 'website_id' in p.env.context:
                return True

            if not p.parent_id and p.vat and p.vat != 'CF' and p.vat != 'C/F' and not p.no_validar_nit:
                repetidos = p.search([('vat','=',p.vat), ('id','!=',p.id), ('parent_id','=',False)])
                if len(repetidos) > 0:
                    raise ValidationError("El NIT " + p.vat + " ya existe")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res1 = super(ResPartner, self).name_search(name, args, operator=operator, limit=limit)

        records = self.search([('vat', 'ilike', name)], limit=limit)
        res2 = records.name_get()

        return res1+res2
