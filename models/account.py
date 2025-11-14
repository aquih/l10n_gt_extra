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

    def agregar_linea_isr(self):
        quetzal = self.env.ref('base.GTQ', raise_if_not_found=True)

        for factura in self:
            total_sin_impuestos = factura.amount_untaxed
            if factura.currency_id != quetzal:
                total_sin_impuestos = factura.currency_id._convert(total_sin_impuestos, quetzal, company=factura.company_id, date=factura.invoice_date, round=False)

            result = 0
            if total_sin_impuestos > 30000:
                result += 30000 * 0.05
                result += (total_sin_impuestos - 30000) * 0.07
            else:
                result += total_sin_impuestos * 0.05

            impuesto = self.env.ref(f'account.{self.env.company.id}_impuestos_plantilla_isr_retencion_global', raise_if_not_found=True)

            if factura.currency_id != quetzal:
                result = quetzal._convert(result, factura.currency_id, company=factura.company_id, date=factura.invoice_date, round=True)

            if result != 0:
                factura.write({ 'invoice_line_ids': [ Command.create({ 'name': 'Retención ISR', 'quantity': result, 'price_unit': 0, 'tax_ids': [ Command.set([impuesto.id]) ] }) ] })

    def agregar_linea_iva(self):
        quetzal = self.env.ref('base.GTQ', raise_if_not_found=True)

        for factura in self:
            total_con_impuestos = factura.amount_untaxed
            if factura.currency_id != quetzal:
                total_con_impuestos = factura.currency_id._convert(total_con_impuestos, quetzal, company=factura.company_id, date=factura.invoice_date, round=False)

            result = 0
            if total_con_impuestos >= 2500:
                result = total_con_impuestos * 0.12 * 0.8

            impuesto = self.env.ref(f'account.{self.env.company.id}_impuestos_plantilla_iva_retencion_global', raise_if_not_found=True)

            if factura.currency_id != quetzal:
                result = quetzal._convert(result, factura.currency_id, company=factura.company_id, date=factura.invoice_date, round=True)

            if result != 0:
                factura.write({ 'invoice_line_ids': [ Command.create({ 'name': 'Retención IVA', 'quantity': result, 'price_unit': 0, 'tax_ids': [ Command.set([impuesto.id]) ] }) ] })

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

    @api.model
    def _eval_tax_amount_formula(self, raw_base, evaluation_context):
        result = super()._eval_tax_amount_formula(raw_base, evaluation_context)
        if self.moneda_id:
            result *= self.moneda_id._get_conversion_rate(self.moneda_id, self.env.company.currency_id)
        return result