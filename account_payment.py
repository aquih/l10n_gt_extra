# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class account_payment(osv.osv):
    _inherit = "account.payment"

    _columns = {
        'numero_viejo': fields.char(string='Numero Viejo'),
    }

    def cancel(self, cr, uid, ids, context=None):
        for p in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, p.id, {'numero_viejo': p.name}, context=context)
        return super(account_payment, self).cancel(cr, uid, ids, context=context)
