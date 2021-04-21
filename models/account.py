# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
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

    def suma_impuesto(self,impuestos_ids):
        suma_monto = 0
        for impuesto in impuestos_ids:
            suma_monto += impuesto.amount
        return suma_monto

    def impuesto_global(self):
        impuestos = self.env['l10n_gt_extra.impuestos'].search([['active','=',True],['tipo','=','compra']])
        impuestos_valores = []
        diferencia  = 0
        suma_impuesto = 0
        impuesto_total = 0
        rango_final_anterior = 0
        for rango in impuestos.rangos_ids:
            if self.amount_untaxed > rango.rango_final and diferencia == 0:
                diferencia = self.amount_untaxed - rango.rango_final
                impuesto_individual = rango.rango_final * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
            elif self.amount_untaxed <= rango.rango_final and diferencia == 0 and rango_final_anterior == 0:
                impuesto_individual = self.amount_untaxed * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                rango_final_anterior = rango.rango_final
                impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
            elif diferencia > 0:
                impuesto_individual = diferencia * (self.suma_impuesto(rango.impuestos_ids) / 100)
                suma_impuesto += impuesto_individual
                impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
        impuesto_total = 0
        self.update({'amount_tax': suma_impuesto, 'amount_total': impuesto_total + self.amount_untaxed})
        account_invoice_tax = self.env['account.invoice.tax']

        for impuesto in impuestos_valores:
            account_invoice_tax.create({'invoice_id': self.id,'tax_id':impuesto['impuesto_id'],'name': impuesto['nombre'],'account_id': impuesto['account_id'],'amount':impuesto['total'] })
        return True

    #@api.constrains('ref')
    #def _validar_factura_proveedor(self):
    #    for factura in self:
    #        facturas = self.search([('ref','=',factura.ref), ('partner_id','=',factura.partner_id.id), ('type','=','in_invoice')])
    #        if len(facturas) > 1:
    #            raise ValidationError("Ya existe una factura con ese mismo numero.")

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

class AccountPayment(models.Model):
    _inherit = "account.payment"

    descripcion = fields.Char(string="Descripción")
    numero_viejo = fields.Char(string="Numero Viejo")
    nombre_impreso = fields.Char(string="Nombre Impreso")
    no_negociable = fields.Boolean(string="No Negociable", default=True)
    anulado = fields.Boolean('Anulado')
    fecha_anulacion = fields.Date('Fecha anulación')

    def cancel(self):
        for rec in self:
            rec.write({'numero_viejo': rec.name})
        return super(AccountPayment, self).cancel()

    def anular(self):
        for rec in self:
            move = self.env['account.move']
            
            if 'move_line_ids' in rec.fields_get():
                move += rec.move_line_ids.mapped('move_id')
            else:
                move += rec.move_id
            
            move.button_cancel()

            move.line_ids.remove_move_reconcile()
            move.line_ids.write({ 'debit': 0, 'credit': 0, 'amount_currency': 0 })
            
            move.post()

            rec.anulado = True
            rec.fecha_anulacion = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d')

class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
    codigo_establecimiento = fields.Integer(string='Código de establecimiento')
    facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción')
    usar_referencia = fields.Boolean(string='Usar referencia para libro de ventas', help='El número de la factua se ingresa en Referencia/Descripción')
