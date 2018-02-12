# -*- encoding: utf-8 -*-

from odoo import api, models
import logging

class ReportePartida(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_partida'

    @api.model
    def get_report_values(self, docids, data=None):
        model = 'account.move'
        docs = self.env[model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
