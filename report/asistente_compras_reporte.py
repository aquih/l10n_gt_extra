# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class asistente_compras_reporte(osv.osv_memory):
    _name = 'l10n_gt_extra.asistente_compras_reporte'
    _columns = {
        'diarios_id': fields.many2many('account.journal', 'compras_diario_rel', 'compras_id', 'diario_id', 'Diarios', required=True),
        'impuesto_id': fields.many2one('account.tax', 'Impuesto', required=True),
        'folio_inicial': fields.integer('Folio inicial', required=True),
        'fecha_desde': fields.date('Fecha inicial', required=True),
        'fecha_hasta': fields.date('Fecha final', required=True),
    }

    _defaults = {
        'folio_inicial': lambda *a: 1,
    }

    def reporte(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.report.xml', 'report_name':'compras_reporte'}
