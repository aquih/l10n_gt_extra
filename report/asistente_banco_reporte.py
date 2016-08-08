# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
import time

class asistente_banco_reporte(osv.osv_memory):
    _name = 'l10n_gt_extra.asistente_banco_reporte'
    _rec_name = 'cuenta_bancaria_id'
    _columns = {
        'cuenta_bancaria_id': fields.many2one('account.account', 'Cuenta', required=True),
        'fecha_desde': fields.date('Fecha inicial', required=True),
        'fecha_hasta': fields.date('Fecha final', required=True),
    }

    def _revisar_cuenta(self, cr, uid, context):
        if 'active_id' in context:
            return context['active_id']
        else:
            return None

    _defaults = {
        'cuenta_bancaria_id': _revisar_cuenta,
        'fecha_desde': lambda *a: time.strftime('%Y-%m-01'),
        'fecha_hasta': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def reporte(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.report.xml', 'report_name':'banco_reporte'}
