# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class asistente_compras_reporte(osv.osv_memory):
    _name = 'l10n_gt_extra.asistente_compras_reporte'
    _columns = {
        'empresa_id': fields.many2one('res.company', 'Empresa', required=True),
        'diarios_id': fields.many2many('account.journal', 'compras_diario_rel', 'compras_id', 'diario_id', 'Diarios', required=True),
        'impuesto_id': fields.many2one('account.tax.code', 'Impuesto', required=True),
        'base_id': fields.many2one('account.tax.code', 'Base', required=True),
        'folio_inicial': fields.integer('Folio inicial', required=True),
        'periodos_id': fields.many2many('account.period', 'compras_periodo_rel', 'compras_id', 'periodo_id', 'Periodos', required=True),
    }

    def _revisar_diario(self, cr, uid, context):
        if 'active_id' in context:
            return context['active_id']
        else:
            return None

    def _default_empresa_id(self, cr, uid, context={}):
        usuario = self.pool.get('res.users').browse(cr,uid,uid)
        return usuario.company_id.id

    _defaults = {
        'empresa_id': _default_empresa_id,
        'folio_inicial': lambda *a: 1,
    }

    def reporte(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.report.xml', 'report_name':'compras_reporte'}

asistente_compras_reporte()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
