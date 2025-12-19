# -*- encoding: utf-8 -*-

from odoo import models, fields, Command, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.l10n_gt_extra import a_letras
from odoo.release import version_info

import datetime
import logging

class AccountMove(models.Model):
    _inherit = "account.move"

    tipo_gasto = fields.Selection([("mixto", "Mixto"), ("compra", "Compra/Bien"), ("servicio", "Servicio"), ("importacion", "Importación/Exportación"), ("combustible", "Combustible")], string="Tipo de Gasto", default="mixto")
    serie_rango = fields.Char(string="Serie Rango")
    inicial_rango = fields.Integer(string="Inicial Rango")
    final_rango = fields.Integer(string="Final Rango")
    diario_facturas_por_rangos = fields.Boolean(string="Las facturas se ingresan por rango", help="Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción", related="journal_id.facturas_por_rangos")
    nota_debito = fields.Boolean(string="Nota de debito")

    @api.constrains('inicial_rango', 'final_rango')
    def _validar_rango(self):
        for factura in self:
            if factura.diario_facturas_por_rangos:
                if int(factura.final_rango) < int(factura.inicial_rango):
                    raise ValidationError('El número inicial del rango es mayor que el final.')
                cruzados = factura.search([('serie_rango','=',factura.serie_rango), ('inicial_rango','<=',factura.inicial_rango), ('final_rango','>=',factura.inicial_rango)])
                if len(cruzados) > 1:
                    raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
                cruzados = self.search([('serie_rango','=',factura.serie_rango), ('inicial_rango','<=',factura.final_rango), ('final_rango','>=',factura.final_rango)])
                if len(cruzados) > 1:
                    raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
                cruzados = self.search([('serie_rango','=',factura.serie_rango), ('inicial_rango','>=',factura.inicial_rango), ('inicial_rango','<=',factura.final_rango)])
                if len(cruzados) > 1:
                    raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')

                self.name = "{}-{} al {}-{}".format(factura.serie_rango, factura.inicial_rango, factura.serie_rango, factura.final_rango)

    def write(self, vals):
        return super(AccountMove, self.with_context(moneda_impuesto_id=self.currency_id)).write(vals)

    def _compute_tax_totals(self):
        return super(AccountMove, self.with_context(moneda_impuesto_id=self.currency_id))._compute_tax_totals()

    def agregar_linea_impuesto_global(self):
        tipo_impuesto = self.env.context.get('tipo_impuesto')
        nombre_linea = self.env.context.get('nombre_linea')

        impuesto = self.env.ref(f'account.{self.env.company.id}_impuestos_plantilla_{tipo_impuesto}_retencion_global', raise_if_not_found=True)

        for factura in self:            
            factura.write({ 'invoice_line_ids': [ Command.create({ 'name': nombre_linea, 'quantity': factura.amount_total, 'price_unit': 0, 'tax_ids': [ Command.set([impuesto.id]) ] }) ] })

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_totals(self):
        return super(AccountMoveLine, self.with_context(moneda_impuesto_id=self.move_id.currency_id))._compute_totals()

class AccountPayment(models.Model):
    _inherit = "account.payment"

    descripcion = fields.Char(string="Descripción")
    nombre_impreso = fields.Char(string="Nombre Impreso")
    no_negociable = fields.Boolean(string="No Negociable", default=True)

    def a_letras(self, monto):
        return a_letras.num_a_letras(monto)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
    codigo_establecimiento = fields.Integer(string='Código de establecimiento')
    facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción')
    usar_referencia = fields.Boolean(string='Usar referencia para libro de ventas', help='El número de la factua se ingresa en Referencia/Descripción')

class AccountTax(models.Model):
    _inherit = "account.tax"

    moneda_id = fields.Many2one('res.currency', string='Moneda a Convertir')

    def _eval_tax_amount_formula(self, raw_base, evaluation_context):
        tasa = 1

        if self.moneda_id:
            tasa = self.env['res.currency']._get_conversion_rate(self.env.company.currency_id, self.moneda_id)
        elif self.env.context.get('moneda_impuesto_id'):
            tasa = self.env['res.currency']._get_conversion_rate(self.env.company.currency_id, self.env.context.get('moneda_impuesto_id'))

        if evaluation_context['product']:
            evaluation_context['product']['tasa_de_conversion'] = tasa
        return super(AccountTax, self)._eval_tax_amount_formula(raw_base, evaluation_context)
