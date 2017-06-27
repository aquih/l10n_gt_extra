# -*- encoding: utf-8 -*-

from odoo import api, models
import logging

class ReporteCompras(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_compras'

    def lineas(self, datos):
        logging.warn(datos)
        totales = {}

        totales['compra'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['servicio'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['importacion'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['combustible'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['pequenio_contribuyente'] = {'exento':0,'neto':0,'iva':0,'total':0}

        journal_ids = [x for x in datos['diarios_id']]
        facturas = self.env['account.invoice'].search([
            ('state','in',['open','paid']),
            ('journal_id','in',journal_ids),
            ('date','<=',datos['fecha_hasta']),
            ('date','>=',datos['fecha_desde']),
        ], order='date_invoice')

        lineas = []
        for f in facturas:

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                total = 0
                for l in f.move_id.line_ids:
                    if l.account_id.id == f.account_id.id:
                        total += l.credit - l.debit
                tipo_cambio = abs(total / f.amount_total)

            tipo = 'FACT'
            if f.type != 'in_invoice':
                tipo = 'NC'
            if f.partner_id.pequenio_contribuyente:
                tipo += ' PEQ'

            linea = {
                'estado': f.state,
                'tipo': tipo,
                'fecha': f.date_invoice,
                'numero': f.reference or '',
                'proveedor': f.partner_id,
                'compra': 0,
                'compra_exento': 0,
                'servicio': 0,
                'servicio_exento': 0,
                'combustible': 0,
                'combustible_exento': 0,
                'importacion': 0,
                'importacion_exento': 0,
                'base': 0,
                'iva': 0,
                'total': 0
            }

            for l in f.invoice_line_ids:
                precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1

                r = l.invoice_line_tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id, partner=f.partner_id)

                linea['base'] += r['base']
                if len(l.invoice_line_tax_ids) > 0:
                    linea[f.tipo_gasto] += r['base']
                    for i in r['taxes']:
                        if i['id'] == datos['impuesto_id'][0]:
                            linea['iva'] += i['amount']
                        elif i['amount'] > 0:
                            linea[f.tipo_gasto+'_exento'] += i['amount']
                else:
                    linea[f.tipo_gasto+'_exento'] += r['base']

            linea['total'] = linea[f.tipo_gasto] + linea['iva']

            if f.partner_id.pequenio_contribuyente:
                totales['pequenio_contribuyente']['exento'] += linea[f.tipo_gasto+'_exento']
                totales['pequenio_contribuyente']['neto'] += linea[f.tipo_gasto]
                totales['pequenio_contribuyente']['iva'] += linea['iva']
                totales['pequenio_contribuyente']['total'] += linea['total']

            totales[f.tipo_gasto]['exento'] += linea[f.tipo_gasto+'_exento']
            totales[f.tipo_gasto]['neto'] += linea[f.tipo_gasto]
            totales[f.tipo_gasto]['iva'] += linea['iva']
            totales[f.tipo_gasto]['total'] += linea['total']

            lineas.append(linea)

        return { 'lineas': lineas, 'totales': totales }

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
        }
        return self.env['report'].render('l10n_gt_extra.reporte_compras', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
