# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    tipo_gasto = fields.Selection([('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')], string="Tipo de Gasto", default="compra")
    numero_viejo = fields.Char(string="Numero Viejo")
    serie_rango = fields.Char(string="Serie Rango")
    inicial_rango = fields.Integer(string="Inicial Rango")
    final_rango = fields.Integer(string="Final Rango")
    diario_facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción', related="journal_id.facturas_por_rangos")

    @api.constrains('reference')
    def _validar_factura_proveedor(self):
        if self.reference:
            facturas = self.search([('reference','=',self.reference), ('partner_id','=',self.partner_id.id), ('type','=','in_invoice')])
            if len(facturas) > 1:
                raise ValidationError("Ya existe una factura con ese mismo numero.")

    @api.constrains('inicial_rango', 'final_rango')
    def _validar_rango(self):
        if self.diario_facturas_por_rangos:
            if int(self.final_rango) < int(self.inicial_rango):
                raise ValidationError('El número inicial del rango es mayor que el final.')
            cruzados = self.search([('serie_rango','=',self.serie_rango), ('inicial_rango','<=',self.inicial_rango), ('final_rango','>=',self.inicial_rango)])
            if len(cruzados) > 1:
                raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
            cruzados = self.search([('serie_rango','=',self.serie_rango), ('inicial_rango','<=',self.final_rango), ('final_rango','>=',self.final_rango)])
            if len(cruzados) > 1:
                raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')
            cruzados = self.search([('serie_rango','=',self.serie_rango), ('inicial_rango','>=',self.inicial_rango), ('inicial_rango','<=',self.final_rango)])
            if len(cruzados) > 1:
                raise ValidationError('Ya existe otra factura con esta serie y en el mismo rango')

            self.name = "{}-{} al {}-{}".format(self.serie_rango, self.inicial_rango, self.serie_rango, self.final_rango)

    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.numero_viejo = rec.number
        return super(AccountInvoice, self).action_cancel()

class AccountPayment(models.Model):
    _inherit = "account.payment"

    numero_viejo = fields.Char(string="Numero Viejo")
    nombre_impreso = fields.Char(string="Nombre Impreso")
    no_negociable = fields.Boolean(string="No Negociable", default=True)
    anulado = fields.Boolean('Anulado')

    @api.multi
    def cancel(self):
        for rec in self:
            rec.write({'numero_viejo': rec.name})
        return super(AccountPayment, self).cancel()

    @api.multi
    def anular(self):
        for rec in self:
            for move in rec.move_line_ids.mapped('move_id'):
                move.button_cancel()

            rec.move_line_ids.remove_move_reconcile()
            rec.move_line_ids.write({ 'debit': 0, 'credit': 0, 'amount_currency': 0 })

            for move in rec.move_line_ids.mapped('move_id'):
                move.post()
            rec.anulado = True

class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
    facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción')
