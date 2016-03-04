# -*- encoding: utf-8 -*-

from openerp.osv import osv
from openerp.osv import fields

class sale_order(osv.osv):
    _inherit = "sale.order"

    def limite_credito(self, cr, uid, ids):
        for order in self.browse(cr, uid, ids):
            limite_credito = order.partner_id.credit_limit

            # limite_credito con valor 0, se asume credito ilimitado o cliente de contado
            if limite_credito == 0:
                return True
            credito_actual = order.partner_id.credit
        if (limite_credito - credito_actual - order.amount_total) < 0:
            raise osv.except_osv('Cliente rebasó crédito autorizado', 'Favor pedir autorización para poder facturar')
            return False
        else:
            return True

sale_order()
