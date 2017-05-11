# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import time
import datetime
import logging

class compras_reporte(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(compras_reporte, self).__init__(cr, uid, name, context=context)
        self.totales = {}
        self.folioActual = -1
        self.lineasGuardadas = []
        self.localcontext.update( {
            'time': time,
            'datetime': datetime,
            'lineas': self.lineas,
            'totales': self.totales,
            'folio': self.folio,
        })
        self.context = context
        self.cr = cr
        self.uid = uid

    def folio(self, datos):
        if self.folioActual < 0:
            if datos[0].folio_inicial <= 0:
                self.folioActual = 1
            else:
                self.folioActual = datos[0].folio_inicial
        else:
            self.folioActual += 1

        return self.folioActual

    def lineas(self, datos):

        if len(self.lineasGuardadas) > 0:
            return self.lineasGuardadas

        self.totales['compra'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['servicio'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['importacion'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['combustible'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['pequenio_contribuyente'] = {'exento':0,'neto':0,'iva':0,'total':0}

        journal_ids = [x.id for x in datos.diarios_id]
        facturas = self.pool.get('account.invoice').search(self.cr, self.uid, [
            ('state','in',['open','paid']),
            ('journal_id','in',journal_ids),
            ('date','<=',datos.fecha_hasta),
            ('date','>=',datos.fecha_desde),
        ], order='date_invoice')
        logging.warn(facturas)

        lineas = []
        for f in self.pool.get('account.invoice').browse(self.cr, self.uid, facturas):

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

                tax_ids = [x.id for x in l.invoice_line_tax_ids]
                r = self.pool.get('account.tax').compute_all(self.cr, self.uid, tax_ids, precio, currency_id=f.currency_id.id, quantity=l.quantity, product_id=l.product_id.id, partner_id=f.partner_id.id)

                linea['base'] += r['base']
                if len(l.invoice_line_tax_ids) > 0:
                    linea[f.tipo_gasto] += r['base']
                    for i in r['taxes']:
                        if i['id'] == datos.impuesto_id.id:
                            linea['iva'] += i['amount']
                        elif i['amount'] > 0:
                            linea[f.tipo_gasto+'_exento'] += i['amount']
                else:
                    linea[f.tipo_gasto+'_exento'] += r['base']

            linea['total'] = linea[f.tipo_gasto] + linea['iva']

            if f.partner_id.pequenio_contribuyente:
                self.totales['pequenio_contribuyente']['exento'] += linea[f.tipo_gasto+'_exento']
                self.totales['pequenio_contribuyente']['neto'] += linea[f.tipo_gasto]
                self.totales['pequenio_contribuyente']['iva'] += linea['iva']
                self.totales['pequenio_contribuyente']['total'] += linea['total']

            self.totales[f.tipo_gasto]['exento'] += linea[f.tipo_gasto+'_exento']
            self.totales[f.tipo_gasto]['neto'] += linea[f.tipo_gasto]
            self.totales[f.tipo_gasto]['iva'] += linea['iva']
            self.totales[f.tipo_gasto]['total'] += linea['total']

            lineas.append(linea)

        self.lineasGuardadas = lineas

        return lineas

report_sxw.report_sxw('report.compras_reporte', 'l10n_gt_extra.asistente_compras_reporte', 'addons/l10n_gt_extra/report/compras_reporte.rml', parser=compras_reporte, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
