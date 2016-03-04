# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
import time

class asistente_banco_reporte(osv.osv_memory):
    _name = 'l10n_gt_extra.asistente_banco_reporte'
    _rec_name = 'cuenta_bancaria_id'
    _columns = {
        'cuenta_bancaria_id': fields.many2one('account.account', 'Cuenta', required=True),
        'ejercicios_fiscales': fields.many2many('account.fiscalyear', 'banco_anio_rel', 'banco_id', 'anio_id', 'Saldo incluyendo ejercicios fiscales'),
        'fecha_desde': fields.date('Fecha inicial', required=True),
        'fecha_hasta': fields.date('Fecha final', required=True),
        'saldo': fields.float('Saldo', digits_compute=dp.get_precision('Account')),
    }

    def _revisar_cuenta(self, cr, uid, context):
        if 'active_id' in context:
            return context['active_id']
        else:
            return None

    def calcular(self, cr, uid, ids, context=None):
        for banco_reporte in self.browse(cr, uid, ids):

            ctx = context.copy()

            ctx['fiscalyear'] = ','.join([str(x.id) for x in banco_reporte.ejercicios_fiscales])
            ctx['date_from'] = '2000-01-01'
            ctx['date_to'] = banco_reporte.fecha_hasta

            cuenta = self.pool.get('account.account').read(cr, uid, banco_reporte.cuenta_bancaria_id.id, ['type','code','name','debit','credit','balance','parent_id'], ctx)

            self.write(cr, uid, [banco_reporte.id], {'saldo': cuenta['balance']}, context=context)

        return True

    _defaults = {
        'cuenta_bancaria_id': _revisar_cuenta,
        'fecha_desde': lambda *a: time.strftime('%Y-%m-01'),
        'fecha_hasta': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def reporte(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.report.xml', 'report_name':'banco_reporte'}
asistente_banco_reporte()
