# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.release import version_info
from odoo.exceptions import UserError, ValidationError
import time

class AsistenteReporteInventario(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_inventario'
    _description = 'Reporte de Inventario'
    
    def _default_cuenta(self):
        if version_info[0] in [13, 14, 15]:
            if len(self.env.context.get('active_ids', [])) > 0:
                return self.env.context.get('active_ids')
            else:
                return self.env['account.account'].search([]).ids
        else:
            return []

    cuentas_id = fields.Many2many("account.account", string="Diario", required=True, default=_default_cuenta)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))

    def print_report(self):
        if not self.cuentas_id:
            raise UserError('Debe ingresar las cuentas que serán utilizadas en el reporte')

        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_inventario',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_gt_extra.action_reporte_inventario').report_action(self, data=data)
