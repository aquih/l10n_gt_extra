# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
import time

class AsistenteReporteInventario(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_inventario'

    def _default_cuenta(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')
        else:
            return self.env['account.account'].search([]).ids

    cuentas_id = fields.Many2many("account.account", string="Diario", required=True, default=_default_cuenta)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))

    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        data = {
             'ids': active_ids,
             'model': self.env.context.get('active_model', 'ir.ui.menu'),
             'form': self.read()[0]
        }
        return self.env['report'].get_action([], 'l10n_gt_extra.reporte_inventario', data=data)
