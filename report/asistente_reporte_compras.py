# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
import time

class AsistenteReporteCompras(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_compras'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))

    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        data = {
             'ids': active_ids,
             'model': self.env.context.get('active_model', 'ir.ui.menu'),
             'form': self.read()[0]
        }
        return self.env['report'].get_action([], 'l10n_gt_extra.reporte_compras', data=data)
