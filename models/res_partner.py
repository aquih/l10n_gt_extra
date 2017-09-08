# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains('vat')
    def _validar_nit(self):
        if self.vat == 'CF' or self.vat == 'C/F' or not self.vat:
            return True

        if self.country_id and self.country_id.id != 91:
            return True

        nit = self.vat.replace('-','')
        verificador = nit[-1]
        if verificador.upper() == 'K':
            verificador = '10'
        secuencia = nit[:-1]

        total = 0
        i = 2
        for c in secuencia[::-1]:
            total += int(c) * i
            i += 1

        resultante = ( 11 - ( total % 11 ) ) % 11

        if str(resultante) == verificador:
            return True
        else:
            raise ValidationError("El NIT no es correcto (según lineamientos de la SAT)")

    @api.constrains('vat')
    def _validar_duplicado(self):
        if not self.parent_id and self.vat and self.vat != 'CF' and self.vat != 'C/F':
            repetidos = self.search([('vat','=',self.vat), ('id','!=',self.id)])
            if len(repetidos) > 0:
                raise ValidationError("El NIT ya existe")
        return True

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res1 = super(ResPartner, self).name_search(name, args, operator=operator, limit=limit)

        records = self.search([('vat', 'ilike', name)], limit=limit)
        res2 = records.name_get()

        return res1+res2

    pequenio_contribuyente = fields.Boolean(string="Pequeño Contribuyente")
