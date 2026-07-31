# -*- encoding: utf-8 -*-

from odoo import api, models
import logging

class ReportePartida(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_partida'
    _description = 'Partida'

    def analiticas(self, distribucion):
        nombres = ''
        if distribucion:
            llaves = [k for k in distribucion.keys()]

            cuentas_ids = []
            for llave in llaves:
                for cuenta_id in llave.split(','):
                    cuentas_ids.append(int(cuenta_id))
            
            nombres = ', '.join(self.env['account.analytic.account'].browse(cuentas_ids).mapped('display_name'))
        return nombres

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = 'account.move'
        docs = self.env[model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'current_company_id': self.env.company,
            'analiticas': self.analiticas,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
