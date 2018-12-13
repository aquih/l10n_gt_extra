# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
import logging

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def impuesto_global(self):
        impuestos = self.env['l10n_gt_extra.impuestos'].search([['active','=',True],['tipo','=','compra']])
        impuestos_globales = []
        impuesto_linea = []
        for rango in impuestos.rangos_ids:
            if self.amount_total <= rango.rango_final and self.amount_total >= rango.rango_inicial:
                impuestos_globales = rango.impuestos_ids
        for linea in self.order_line:
            impuesto_linea = linea.taxes_id.ids
            for impuesto in impuestos_globales:
                impuesto_linea.append(impuesto.id)
            linea.taxes_id = [(6, 0, impuesto_linea)]
        return True
