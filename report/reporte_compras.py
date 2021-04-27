# -*- encoding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError
import logging

class ReporteCompras(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_compras'

    def lineas(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        totales['compra'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['servicio'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['combustible'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['importacion'] = {'exento':0,'neto':0,'iva':0,'total':0}
        totales['pequeño'] = {'exento':0,'neto':0,'iva':0,'total':0}

        journal_ids = [x for x in datos['diarios_id']]
        filtro = [
            ('state','in',['posted']),
            ('journal_id','in',journal_ids),
            ('date','<=',datos['fecha_hasta']),
            ('date','>=',datos['fecha_desde']),
        ]
        
        if 'type' in self.env['account.move'].fields_get():
            filtro.append(('type','in',['in_invoice','in_refund']))
        else:
            filtro.append(('move_type','in',['in_invoice','in_refund']))
        
        facturas = self.env['account.move'].search(filtro)

        lineas = []
        for f in facturas:
            totales['num_facturas'] += 1

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                total = 0
                for l in f.line_ids:
                    if l.account_id.reconcile:
                        total += l.debit - l.credit
                if f.amount_total != 0:
                    tipo_cambio = abs(total / f.amount_total)

            tipo = 'FACT'
            tipo_interno_factura = f.type if 'type' in f.fields_get() else f.move_type
            if tipo_interno_factura != 'in_invoice':
                tipo = 'NC'
            if f.nota_debito:
                tipo = 'ND'
            if f.partner_id.pequenio_contribuyente:
                tipo += ' PEQ'
           
            numero = f.ref or ''
            
            # Por si usa factura electrónica
            if 'firma_fel' in f.fields_get() and f.firma_fel:
                numero = str(f.serie_fel) + '-' + str(f.numero_fel)

            linea = {
                'estado': f.state,
                'tipo': tipo,
                'fecha': f.date,
                'numero': numero,
                'proveedor': f.partner_id,
                'compra': 0,
                'compra_exento': 0,
                'servicio': 0,
                'servicio_exento': 0,
                'combustible': 0,
                'combustible_exento': 0,
                'importacion': 0,
                'importacion_exento': 0,
                'pequeño': 0,
                'pequeño_exento': 0,
                'base': 0,
                'iva': 0,
                'total': 0
            }

            for l in f.invoice_line_ids:
                precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1

                tipo_linea = f.tipo_gasto or 'mixto'
                if tipo_linea == 'mixto':
                    if l.product_id.type == 'product':
                        tipo_linea = 'compra'
                    else:
                        tipo_linea = 'servicio'

                if f.partner_id.pequenio_contribuyente:
                    tipo_linea = 'pequeño'

                r = l.tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id, partner=f.partner_id)

                linea['base'] += r['total_excluded']
                totales[tipo_linea]['total'] += r['total_excluded']
                if len(l.tax_ids) > 0:
                    linea[tipo_linea] += r['total_excluded']
                    totales[tipo_linea]['neto'] += r['total_excluded']
                    for i in r['taxes']:
                        if i['id'] == datos['impuesto_id'][0]:
                            linea['iva'] += i['amount']
                            totales[tipo_linea]['iva'] += i['amount']
                            totales[tipo_linea]['total'] += i['amount']
                        elif i['amount'] > 0:
                            linea[tipo_linea+'_exento'] += i['amount']
                            totales[tipo_linea]['exento'] += i['amount']
                else:
                    linea[tipo_linea+'_exento'] += r['total_excluded']
                    totales[tipo_linea]['exento'] += r['total_excluded']

                linea['total'] += precio * l.quantity

            lineas.append(linea)
            
        lineas = sorted(lineas, key = lambda i: str(i['fecha']) + str(i['numero']))

        return { 'lineas': lineas, 'totales': totales }

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        if len(data['form']['diarios_id']) == 0:
            raise UserError("Por favor ingrese al menos un diario.")

        diario = self.env['account.journal'].browse(data['form']['diarios_id'][0])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
            'direccion': diario.direccion and diario.direccion.street,
            'current_company_id': self.env.company,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
