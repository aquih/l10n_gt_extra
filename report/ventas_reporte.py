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

    def lineas_viejo(self, datos):

        if self.temp_lineas:
            return self.temp_lineas

        self.totales['compra'] = {'neto':0,'iva':0,'total':0}
        self.totales['servicio'] = {'neto':0,'iva':0,'total':0}
        self.totales['importacion'] = {'neto':0,'iva':0,'total':0}
        self.totales['combustible'] = {'neto':0,'iva':0,'total':0}
        self.totales['exento'] = {'neto':0,'iva':0,'total':0}
        self.totales['nd'] = {'neto':0,'iva':0,'total':0}
        self.totales['nc'] = {'neto':0,'iva':0,'total':0}

        self.cr.execute("select \
                invoice.id, \
                invoice.date_invoice as date_invoice, \
                invoice.journal_id as journal_id, \
                invoice.tipo_gasto as tipo_gasto, \
                coalesce(invoice.number, invoice.internal_number) as number, \
                invoice.type as type, \
                partner.name as name, \
                partner.vat as vat, \
                invoice.state, \
                case when invoice.state <> 'cancel' then coalesce(invoice.amount_untaxed, 0) else 0 end as amount_untaxed, \
                case when invoice.state <> 'cancel' then sum(case when line.tax_code_id = %s then line.credit else 0 end) - sum(case when line.tax_code_id = %s then line.debit else 0 end) else 0 end as total_impuesto, \
                case when invoice.state <> 'cancel' then sum(case when line.tax_code_id = %s then line.credit else 0 end) - sum(case when line.tax_code_id = %s then line.debit else 0 end) else 0 end as total_base, \
                case when invoice.state <> 'cancel' then sum(case when line.account_id = invoice.account_id then line.debit else 0 end) - sum(case when line.account_id = invoice.account_id then line.credit else 0 end) else 0 end as total_factura \
            from account_invoice invoice join res_partner partner on(invoice.partner_id = partner.id) \
                left join account_move_line line on(invoice.move_id = line.move_id) \
            where invoice.state in ('open','paid', 'cancel') and \
                invoice.journal_id in ("+','.join([str(d.id) for d in datos.diarios_id])+") and \
                invoice.period_id in ("+','.join([str(p.id) for p in datos.periodos_id])+") \
            group by invoice.id, invoice.date_invoice, invoice.journal_id, invoice.tipo_gasto, coalesce(invoice.number, invoice.internal_number), invoice.type, partner.name, partner.vat, invoice.state, invoice.amount_untaxed, invoice.state \
            order by type, date_invoice, number",
            (datos.impuesto_id.id, datos.impuesto_id.id, datos.base_id.id, datos.base_id.id))

        lineas = self.cr.dictfetchall()

        for l in lineas:

            l['mixto_producto'] = 0;
            l['mixto_iva_producto'] = 0;
            l['mixto_servicio'] = 0;
            l['mixto_iva_servicio'] = 0;

            if l['tipo_gasto'] == 'mixto':
                fact = self.pool.get('account.invoice').browse(self.cr, self.uid, l['id'])

                for line in fact.invoice_line:
                    if line.product_id.type == 'product':
                        l['mixto_producto'] += line.price_subtotal
                    else:
                        l['mixto_servicio'] += line.price_subtotal

            tipo_doc = 'FACT'
            if l['type'] == 'out_refund':
                if l['amount_untaxed'] >= 0:
                    tipo_doc = 'NC'
                else:
                    tipo_doc = 'ND'

            l['tipo_doc'] = tipo_doc

            if l['total_impuesto'] == 0:
                l['tipo_gasto'] = 'exento'
                l['total_base'] = l['total_factura']

            if tipo_doc == 'FACT':
                if l['tipo_gasto'] != 'mixto':
                    self.totales[l['tipo_gasto']]['neto'] += l['total_base']
                    self.totales[l['tipo_gasto']]['iva'] += l['total_impuesto']
                    self.totales[l['tipo_gasto']]['total'] += l['total_base']+l['total_impuesto']
                else:
                    iva_producto = ( l['mixto_producto'] / l['total_base'] ) * l['total_impuesto']
                    iva_servicio = ( l['mixto_servicio'] / l['total_base'] ) * l['total_impuesto']
                    self.totales['compra']['neto'] += l['mixto_producto']
                    self.totales['compra']['iva'] += iva_producto
                    self.totales['compra']['total'] += l['mixto_producto']+iva_producto
                    self.totales['servicio']['neto'] += l['mixto_servicio']
                    self.totales['servicio']['iva'] += iva_servicio
                    self.totales['servicio']['total'] += l['mixto_servicio']+iva_servicio
            elif tipo_doc == 'NC':
                self.totales['nc']['neto'] += l['total_base']
                self.totales['nc']['iva'] += l['total_impuesto']
                self.totales['nc']['total'] += l['total_base']+l['total_impuesto']
            else:
                self.totales['nd']['neto'] += l['total_base']
                self.totales['nd']['iva'] += l['total_impuesto']
                self.totales['nd']['total'] += l['total_base']+l['total_impuesto']

        if datos.resumido:
            lineas_resumidas = {}
            for l in lineas:
                l['state'] = 'open'
                l['tipo_gasto'] = 'compra'
                llave = l['tipo_doc']+l['date_invoice']
                if llave not in lineas_resumidas:
                    lineas_resumidas[llave] = dict(l)
                    lineas_resumidas[llave]['name'] = 'Varios'
                    lineas_resumidas[llave]['vat'] = 'Varios'
                    lineas_resumidas[llave]['facturas'] = [l['number']]
                else:
                    lineas_resumidas[llave]['total_base'] += l['total_base']
                    lineas_resumidas[llave]['total_impuesto'] += l['total_impuesto']
                    lineas_resumidas[llave]['facturas'].append(l['number'])

            for l in lineas_resumidas.values():
                l['number'] = l['facturas'][0] + ' al ' + l['facturas'][-1]
                logging.warn(l['tipo_doc']+l['date_invoice'])

            logging.warn(sorted(lineas_resumidas.values(), key=lambda l: l['tipo_doc']+l['date_invoice']))

            # lineas = lineas_resumidas.values()
            lineas = sorted(lineas_resumidas.values(), key=lambda l: l['tipo_doc']+l['date_invoice'])

        self.temp_lineas = lineas
        return lineas

    def lineas(self, datos):

        if self.temp_lineas:
            return self.temp_lineas

        self.totales['num_facturas'] = 0
        self.totales['compra'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['servicio'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['importacion'] = {'exento':0,'neto':0,'iva':0,'total':0}
        self.totales['combustible'] = {'exento':0,'neto':0,'iva':0,'total':0}

        journal_ids = [x.id for x in datos.diarios_id]
        period_ids = [x.id for x in datos.periodos_id]
        facturas = self.pool.get('account.invoice').search(self.cr, self.uid, [
            ('state','in',['open','paid','cancel']), ('journal_id','in',journal_ids), ('period_id','in',period_ids)
        ], order='date_invoice, number')

        lineas = []
        for f in self.pool.get('account.invoice').browse(self.cr, self.uid, facturas):
            self.totales['num_facturas'] += 1

            tipo_cambio = 1
            if f.currency_id.id != f.company_id.currency_id.id:
                total = 0
                for l in f.move_id.line_id:
                    if l.account_id.id == f.account_id.id:
                        total += l.debit - l.credit
                tipo_cambio = abs(total / f.amount_total)

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
                'numero': f.number or f.internal_number,
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

            for l in f.invoice_line:
                precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                if tipo == 'NC':
                    precio = precio * -1

                tipo_linea = f.tipo_gasto
                if f.tipo_gasto == 'mixto':
                    if l.product_id.type == 'product':
                        tipo_linea = 'compra'
                    else:
                        tipo_linea = 'servicio'

                r = self.pool.get('account.tax').compute_all(self.cr, self.uid, l.invoice_line_tax_id, precio, l.quantity, product=l.product_id, partner=l.invoice_id.partner_id)

                linea['base'] += r['total']
                self.totales[tipo_linea]['total'] += r['total']
                if len(l.invoice_line_tax_id) > 0:
                    linea[tipo_linea] += r['total']
                    self.totales[tipo_linea]['neto'] += r['total']
                    for i in r['taxes']:
                        if i['base_code_id'] == datos.base_id.id and i['tax_code_id'] == datos.impuesto_id.id:
                            linea['iva'] += i['amount']
                            self.totales[tipo_linea]['iva'] += i['amount']
                            self.totales[tipo_linea]['total'] += i['amount']
                        elif i['amount'] > 0:
                            linea[tipo_linea+'_exento'] += i['amount']
                            self.totales[tipo_linea]['exento'] += r['total']
                else:
                    linea[tipo_linea+'_exento'] += r['total']
                    self.totales[tipo_linea]['exento'] += r['total']


            linea['total'] = linea['compra']+linea['servicio']+linea['combustible']+linea['importacion']+linea['iva']

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
                facturas = sorted(l['facturas'])
                l['numero'] = facturas[0] + ' al ' + facturas[-1]

            lineas = sorted(lineas_resumidas.values(), key=lambda l: l['tipo']+l['fecha'])

        self.temp_lineas = lineas
        return lineas


report_sxw.report_sxw('report.ventas_reporte', 'l10n_gt_extra.asistente_ventas_reporte', 'addons/l10n_gt_extra/report/ventas_reporte.rml', parser=ventas_reporte, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
