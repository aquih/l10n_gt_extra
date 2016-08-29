# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import time
import datetime

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
            order by type, number",
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

            # lineas = lineas_resumidas.values()
            lineas = sorted(lineas_resumidas.values(), key=lambda x: l['tipo_doc']+l['date_invoice'])

        self.temp_lineas = lineas
        return lineas

report_sxw.report_sxw('report.ventas_reporte', 'l10n_gt_extra.asistente_ventas_reporte', 'addons/l10n_gt_extra/report/ventas_reporte.rml', parser=ventas_reporte, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
