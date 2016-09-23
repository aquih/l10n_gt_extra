# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import time
import datetime
import logging

class ventas_reporte(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ventas_reporte, self).__init__(cr, uid, name, context)
        self.totales = {}
        self.folioActual = -1
        self.temp_lineas = []
        self.localcontext.update( {
            'time': time,
            'datetime': datetime,
            'lineas': self.lineas,
            'totales': self.totales,
            'folio': self.folio,
        })
        self.context = context
        self.cr = cr

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

        if self.temp_lineas:
            return self.temp_lineas

        self.totales['compra'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['servicio'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['importacion'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['combustible'] = {'exento':0,'neto':0,'iva':0,'total':0}

        journal_ids = [x.id for x in datos.diarios_id]
        facturas = self.pool.get('account.invoice').search(self.cr, self.uid, [
            ('state','in',['open','paid','cancel']),
            ('journal_id','in',journal_ids),
            ('date_invoice','<=',datos.fecha_hasta),
            ('date_invoice','>=',datos.fecha_desde),
        ], order='date_invoice')

        lineas = []
        for f in self.pool.get('account.invoice').browse(self.cr, self.uid, facturas):

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                total = 0
                for l in f.move_id.line_ids:
                    if l.account_id.id == f.account_id.id:
                        total += l.debit - l.credit
                tipo_cambio = total / f.amount_total

            tipo = 'FACT'
            if f.type == 'out_refund':
                if f.amount_untaxed >= 0:
                    tipo = 'NC'
                else:
                    tipo = 'ND'

            linea = {
                'estado': f.state,
                'tipo': tipo,
                'fecha': f.date_invoice,
                'numero': f.number or '',
                'cliente': f.partner_id.name,
                'nit': f.partner_id.vat,
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

            if f.state == 'cancel':
                lineas.append(linea)
                continue

            for l in f.invoice_line_ids:
                precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1

                tipo_linea = f.tipo_gasto
                if f.tipo_gasto == 'mixto':
                    if l.product_id.type == 'product':
                        tipo_linea = 'compra'
                    else:
                        tipo_linea = 'servicio'

                tax_ids = [x.id for x in l.invoice_line_tax_ids]
                r = self.pool.get('account.tax').compute_all(self.cr, self.uid, tax_ids, precio, currency_id=f.currency_id.id, quantity=l.quantity, product_id=l.product_id.id, partner_id=f.partner_id.id)

                linea['base'] += r['total_included']
                if len(l.invoice_line_tax_ids) > 0:
                    linea[tipo_linea] += r['total_included']
                    for i in r['taxes']:
                        if i['id'] == datos.impuesto_id.id:
                            linea['iva'] += i['amount']
                        elif i['amount'] > 0:
                            linea[f.tipo_gasto+'_exento'] += i['amount']
                else:
                    linea[tipo_linea+'_exento'] += r['total_included']

            linea['total'] = linea['compra']+linea['servicio']+linea['combustible']+linea['importacion']+linea['iva']

            self.totales['compra']['exento'] += linea['compra'+'_exento']
            self.totales['compra']['neto'] += linea['compra']
            if linea['compra'] != 0:
                self.totales['compra']['iva'] += linea['iva']
                self.totales['compra']['total'] += linea['total']

            self.totales['servicio']['exento'] += linea['servicio'+'_exento']
            self.totales['servicio']['neto'] += linea['servicio']
            if linea['servicio'] != 0:
                self.totales['servicio']['iva'] += linea['iva']
                self.totales['servicio']['total'] += linea['total']

            self.totales['combustible']['exento'] += linea['combustible'+'_exento']
            self.totales['combustible']['neto'] += linea['combustible']
            if linea['combustible'] != 0:
                self.totales['combustible']['iva'] += linea['iva']
                self.totales['combustible']['total'] += linea['total']

            self.totales['importacion']['exento'] += linea['importacion'+'_exento']
            self.totales['importacion']['neto'] += linea['importacion']
            if linea['importacion'] != 0:
                self.totales['importacion']['iva'] += linea['iva']
                self.totales['importacion']['total'] += linea['total']

            lineas.append(linea)

        if datos.resumido:
            lineas_resumidas = {}
            for l in lineas:
                llave = l['tipo']+l['fecha']
                if llave not in lineas_resumidas:
                    lineas_resumidas[llave] = dict(l)
                    lineas_resumidas[llave]['estado'] = 'open'
                    lineas_resumidas[llave]['cliente'] = 'Varios'
                    lineas_resumidas[llave]['nit'] = 'Varios'
                    lineas_resumidas[llave]['facturas'] = [l['numero']]
                else:
                    lineas_resumidas[llave]['compra'] += l['compra']
                    lineas_resumidas[llave]['compra_exento'] += l['compra_exento']
                    lineas_resumidas[llave]['servicio'] += l['servicio']
                    lineas_resumidas[llave]['servicio_exento'] += l['servicio_exento']
                    lineas_resumidas[llave]['combustible'] += l['combustible']
                    lineas_resumidas[llave]['combustible_exento'] += l['combustible_exento']
                    lineas_resumidas[llave]['importacion'] += l['importacion']
                    lineas_resumidas[llave]['importacion_exento'] += l['importacion_exento']
                    lineas_resumidas[llave]['base'] += l['base']
                    lineas_resumidas[llave]['iva'] += l['iva']
                    lineas_resumidas[llave]['total'] += l['total']
                    lineas_resumidas[llave]['facturas'].append(l['numero'])

            for l in lineas_resumidas.values():
                l['numero'] = l['facturas'][0] + ' al ' + l['facturas'][-1]

            lineas = sorted(lineas_resumidas.values(), key=lambda l: l['tipo']+l['fecha'])

        self.temp_lineas = lineas
        return lineas


report_sxw.report_sxw('report.ventas_reporte', 'l10n_gt_extra.asistente_ventas_reporte', 'addons/l10n_gt_extra/report/ventas_reporte.rml', parser=ventas_reporte, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
