# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    _columns = {
        'tipo_gasto': fields.selection((('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')), 'Tipo de Gasto', required=True),
        'numero_viejo': fields.char(string='Numero Viejo'),
    }

    def action_cancel(self, cr, uid, ids, context=None):
        for f in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, f.id, {'numero_viejo': f.number}, context=context)
        return super(account_invoice, self).action_cancel(cr, uid, ids, context=context)

    _defaults = {
        'tipo_gasto': lambda *a: 'compra',
    }
