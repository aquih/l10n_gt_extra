# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    tipo_gasto = fields.Selection([('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')], string="Numero Viejo", default="compra")
    numero_viejo = fields.Char(string="Numero Viejo")

    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.numero_viejo = rec.name
        return super(AccountInvoice, self).action_cancel()

class AccountPayment(models.Model):
    _inherit = "account.payment"

    numero_viejo = fields.Char(string="Numero Viejo")

    @api.multi
    def cancel(self):
        for rec in self:
            rec.write({'numero_viejo': rec.name})
        return super(account_payment, self).cancel()

    @api.multi
    def anular(self):
        for rec in self:
            for move in rec.move_line_ids.mapped('move_id'):
                move.button_cancel()

            rec.move_line_ids.remove_move_reconcile()
            rec.move_line_ids.write({ 'debit': 0, 'credit': 0, 'amount_currency': 0 })

            for move in rec.move_line_ids.mapped('move_id'):
                move.post()

class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one('res.partner', string='Dirección')
