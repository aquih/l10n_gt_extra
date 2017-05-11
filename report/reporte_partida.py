# -*- encoding: utf-8 -*-

from odoo import api, models

class ReportePartida(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_partida'

    @api.model
    def render_html(self, docids, data=None):
        self.model = 'account.move'
        docs = self.env[self.model].browse(docids)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
        }
        return self.env['report'].render('l10n_gt_extra.reporte_partida', docargs)
