# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import logging

class res_partner(osv.osv):
    _inherit = "res.partner"

    def _validar_nit(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)

        if obj.vat == 'CF' or not obj.vat:
            return True

        if obj.country_id and obj.country_id.id != 91:
            return True

        nit = obj.vat.replace('-','')
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
            return False

    def _validar_duplicado(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if not obj.parent_id:
            repetidos = self.search(cr, uid, [('vat','=',obj.vat), ('id','!=',obj.id)],context=context)
            if len(repetidos) > 0:
                return False
        return True

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        res1 = super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

        ids = self.search(cr, uid, [('vat', 'ilike', name)], limit=limit, context=context)
        res2 = self.name_get(cr, uid, ids, context)

        return res1+res2

    _columns = {
        'pequenio_contribuyente': fields.boolean('Pequeño contribuyente'),
    }

    _constraints = [
    #    (_validar_duplicado, 'El NIT ya existe.', ['vat']),
    #    (_validar_nit, 'El NIT no es correcto', ['vat']),
    ]
