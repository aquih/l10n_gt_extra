# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import base64
import xlwt
import StringIO
import logging

class asistente_ventas_reporte_excel(osv.osv_memory):
    _name = 'l10n_gt_extra.asistente_ventas_reporte_excel'
    _columns = {
        'empresa_id': fields.many2one('res.company', 'Empresa', required=True),
        'diarios_id': fields.many2many('account.journal', 'ventas_diario_excel_rel', 'ventas_id', 'diario_id', 'Diarios', required=True),
        'impuesto_id': fields.many2one('account.tax.code', 'Impuesto', required=True),
        'base_id': fields.many2one('account.tax.code', 'Base', required=True),
        'folio_inicial': fields.integer('Folio inicial', required=True),
        'resumido': fields.boolean('Resumido'),
        'periodos_id': fields.many2many('account.period', 'ventas_periodo_excel_rel', 'ventas_id', 'periodo_id', 'Periodos', required=True),
        'archivo': fields.binary('Archivo'),
    }

    def _revisar_diario(self, cr, uid, context):
        if 'active_id' in context:
            return context['active_id']
        else:
            return None

    def _default_empresa_id(self, cr, uid, context={}):
        usuario = self.pool.get('res.users').browse(cr,uid,uid)
        return usuario.company_id.id

    _defaults = {
        'empresa_id': _default_empresa_id,
        'folio_inicial': lambda *a: 1,
    }

    def reporte(self, cr, uid, ids, context=None):
        logging.warn('PRUEBA....')
        for w in self.browse(cr, uid, ids):
            libro = xlwt.Workbook()
            hoja = libro.add_sheet('reporte')

            xlwt.add_palette_colour("custom_colour", 0x21)
            libro.set_colour_RGB(0x21, 200, 200, 200)
            estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')

            totales = {}
            totales['num_facturas'] = 0
            totales['compra'] = {'exento':0,'neto':0,'iva':0,'total':0}
            totales['servicio'] = {'exento':0,'neto':0,'iva':0,'total':0}
            totales['importacion'] = {'exento':0,'neto':0,'iva':0,'total':0}
            totales['combustible'] = {'exento':0,'neto':0,'iva':0,'total':0}

            journal_ids = [x.id for x in w.diarios_id]
            period_ids = [x.id for x in w.periodos_id]
            facturas = self.pool.get('account.invoice').search(cr, uid, [
                ('state','in',['open','paid','cancel']), ('journal_id','in',journal_ids), ('period_id','in',period_ids)
            ], order='date_invoice, number')

            lineas = []
            for f in self.pool.get('account.invoice').browse(cr, uid, facturas):
                totales['num_facturas'] += 1

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

                    r = self.pool.get('account.tax').compute_all(cr, uid, l.invoice_line_tax_id, precio, l.quantity, product=l.product_id, partner=l.invoice_id.partner_id)

                    linea['base'] += r['total']
                    totales[tipo_linea]['total'] += r['total']
                    if len(l.invoice_line_tax_id) > 0:
                        linea[tipo_linea] += r['total']
                        totales[tipo_linea]['neto'] += r['total']
                        for i in r['taxes']:
                            if i['base_code_id'] == w.base_id.id and i['tax_code_id'] == w.impuesto_id.id:
                                linea['iva'] += i['amount']
                                totales[tipo_linea]['iva'] += i['amount']
                                totales[tipo_linea]['total'] += i['amount']
                            elif i['amount'] > 0:
                                linea[tipo_linea+'_exento'] += i['amount']
                                totales[tipo_linea]['exento'] += r['total']
                    else:
                        linea[tipo_linea+'_exento'] += r['total']
                        totales[tipo_linea]['exento'] += r['total']


                linea['total'] = linea['compra']+linea['servicio']+linea['combustible']+linea['importacion']+linea['iva']
                lineas.append(linea)

            if w.resumido:
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

            hoja.write(0, 0, 'NUMERO DE IDENTIFICACION TRIBUTARIA')
            hoja.write(0, 1, w.diarios_id[0].company_id.partner_id.vat)
            hoja.write(1, 0, 'LIBRO DE VENTAS Y SERVICIOS')
            hoja.write(2, 0, 'NOMBRE COMERCIAL')
            hoja.write(2, 1, w.diarios_id[0].company_id.partner_id.name)
            hoja.write(3, 0, 'DOMICILIO FISCAL')
            hoja.write(3, 1, w.diarios_id[0].company_id.partner_id.street)

            y = 5
            hoja.write(y, 0, 'TIPO')
            hoja.write(y, 1, 'FECHA')
            hoja.write(y, 2, 'NO. DOC')
            hoja.write(y, 3, 'CLIENTE')
            hoja.write(y, 4, 'NIT')
            hoja.write(y, 5, 'EXENTO')
            hoja.write(y, 6, 'BIEN')
            hoja.write(y, 7, 'SERVICIO')
            hoja.write(y, 8, 'IVA')
            hoja.write(y, 9, 'TOTAL')

            for linea in lineas:
                y += 1
                hoja.write(y, 0, linea['tipo'])
                hoja.write(y, 1, linea['fecha'])
                hoja.write(y, 2, linea['numero'])
                hoja.write(y, 3, linea['cliente'])
                hoja.write(y, 4, linea['nit'])
                hoja.write(y, 5, linea['compra_exento']+linea['servicio_exento']+linea['combustible_exento']+linea['importacion_exento'])
                hoja.write(y, 6, linea['compra']+linea['combustible']+linea['importacion'])
                hoja.write(y, 7, linea['servicio'])
                hoja.write(y, 8, linea['iva'])
                hoja.write(y, 9, linea['total'])

            
            y += 2
            hoja.write(y, 3, 'EXENTO')
            hoja.write(y, 4, 'NETO')
            hoja.write(y, 5, 'IVA')
            hoja.write(y, 6, 'TOTAL')
            y += 1
            hoja.write(y, 1, 'BIENES')
            hoja.write(y, 3, totales['compra']['exento'])
            hoja.write(y, 4, totales['compra']['neto'])
            hoja.write(y, 5, totales['compra']['iva'])
            hoja.write(y, 6, totales['compra']['total'])
            y += 1
            hoja.write(y, 1, 'SERVICIOS')
            hoja.write(y, 3, totales['servicio']['exento'])
            hoja.write(y, 4, totales['servicio']['neto'])
            hoja.write(y, 5, totales['servicio']['iva'])
            hoja.write(y, 6, totales['servicio']['total'])
            y += 1
            hoja.write(y, 1, 'COMBUSTIBLES')
            hoja.write(y, 3, totales['combustible']['exento'])
            hoja.write(y, 4, totales['combustible']['neto'])
            hoja.write(y, 5, totales['combustible']['iva'])
            hoja.write(y, 6, totales['combustible']['total'])
            y += 1
            hoja.write(y, 1, 'EXPORTACIONES')
            hoja.write(y, 3, 0)
            hoja.write(y, 4, totales['importacion']['neto'])
            hoja.write(y, 5, totales['importacion']['iva'])
            hoja.write(y, 6, totales['importacion']['total'])
            y += 1
            hoja.write(y, 1, 'TOTALES')
            hoja.write(y, 3, totales['compra']['exento']+totales['servicio']['exento']+totales['combustible']['exento']+0)
            hoja.write(y, 4, totales['compra']['neto']+totales['servicio']['neto']+totales['combustible']['neto']+totales['importacion']['neto'])
            hoja.write(y, 5, totales['compra']['iva']+totales['servicio']['iva']+totales['combustible']['iva']+totales['importacion']['iva'])
            hoja.write(y, 6, totales['compra']['total']+totales['servicio']['total']+totales['combustible']['total']+totales['importacion']['total'])
            
            f = StringIO.StringIO()
            libro.save(f)
            datos = base64.b64encode(f.getvalue())
            self.write(cr, uid, ids, {'archivo':datos})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.asistente_ventas_reporte_excel',
            'res_id': ids[0],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

asistente_ventas_reporte_excel()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
