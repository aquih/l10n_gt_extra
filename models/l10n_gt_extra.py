# -*- encoding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID

class L10nGtExtraImpuestos(models.Model):
    _name = "l10n_gt_extra.impuestos"
    _rec_name = "nombre"

    nombre = fields.Char('Nombre')
    active = fields.Boolean('Activo')
    tipo = fields.Selection([('compra', 'Compra'),('venta', 'Venta')])
    rangos_ids = fields.One2many('l10n_gt_extra.impuestos.rangos','impuesto_id',string='Rangos')

class L10nGtExtraImpuestosRangos(models.Model):
    _name = "l10n_gt_extra.impuestos.rangos"

    rango_inicial = fields.Float('Rango inicial')
    rango_final = fields.Float('Rango final')
    impuestos_ids = fields.Many2many('account.tax','impuestos_rangos_rel',string='Impuestos')
    impuesto_id = fields.Many2one('l10n_gt_extra.impuestos','Impuesto global')
