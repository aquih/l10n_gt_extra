# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class asistente_diario_reporte(osv.osv_memory):
    _name = 'l10n_gt_extra.asistente_diario_reporte'
    _columns = {
        'folio_inicial': fields.integer('Folio inicial', required=True),
        'diarios_id': fields.many2many('account.journal', 'diario_diario_rel', 'reporte_id', 'diario_id', 'Diarios'),
        'fecha_desde': fields.date('Fecha inicial', required=True),
        'fecha_hasta': fields.date('Fecha final', required=True),
        'tipo': fields.selection([ ('diario','Diario'), ('mayor','Mayor') ], string='Tipo', required=True),
    }

    _defaults = {
        'folio_inicial': lambda *a: 1,
    }

    def reporte(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.report.xml', 'report_name':'diario_reporte'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
