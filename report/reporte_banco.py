# -*- encoding: utf-8 -*-

import time
from odoo import api, models

class ReporteBanco(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_banco'

    def lineas(self, datos):
        lineas = []
        for linea in self.env['account.move.line'].search([('account_id','=',datos['cuenta_bancaria_id'][0]), ('date','>=',datos['fecha_desde']), ('date','<=',datos['fecha_hasta'])], order='date'):
            detalle = {
                'fecha': linea.date,
                'documento': linea.move_id.name if linea.move_id else '',
                'nombre': linea.partner_id.name or '',
                'concepto': (linea.ref if linea.ref else '')+linea.name,
                'debito': linea.debit,
                'credito': linea.credit,
                'balance': 0,
                'tipo': '',
                'moneda': linea.company_id.currency_id,
            }

            if linea.amount_currency:
                detalle['moneda'] = linea.currency_id
                if linea.amount_currency > 0:
                    detalle['debito'] = linea.amount_currency
                else:
                    detalle['credito'] = -1 * linea.amount_currency

            lineas.append(detalle)

        balance_inicial = self.balance_inicial(datos)
        if balance_inicial['balance_moneda']:
            balance = balance_inicial['balance_moneda']
        elif balance_inicial['balance']:
            balance = balance_inicial['balance']
        else:
            balance = 0

        for linea in lineas:

            balance = balance + linea['debito'] - linea['credito']
            linea['balance'] = balance

        return lineas

    def balance_inicial(self, datos):
        self.env.cr.execute('select (sum(debit) - sum(credit)) as balance, sum(amount_currency) as balance_moneda from account_move_line where account_id = %s and date < %s', (datos['cuenta_bancaria_id'][0], datos['fecha_desde']))
        return self.env.cr.dictfetchall()[0]

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas(data['form']),
            'balance_inicial': self.balance_inicial(data['form']),
        }
        return self.env['report'].render('l10n_gt_extra.reporte_banco', docargs)
