# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import base64
import xlwt
import StringIO
import logging

class asistente_compras_reporte_excel(osv.osv_memory):
    _name = 'l10n_gt_extra.asistente_compras_reporte_excel'
    _columns = {
        'empresa_id': fields.many2one('res.company', 'Empresa', required=True),
        'diarios_id': fields.many2many('account.journal', 'compras_diario_excel_rel', 'compras_id', 'diario_id', 'Diarios', required=True),
        'impuesto_id': fields.many2one('account.tax.code', 'Impuesto', required=True),
        'base_id': fields.many2one('account.tax.code', 'Base', required=True),
        'folio_inicial': fields.integer('Folio inicial', required=True),
        'periodos_id': fields.many2many('account.period', 'compras_periodo_excel_rel', 'compras_id', 'periodo_id', 'Periodos', required=True),
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
            totales['compra'] = {'exento':0,'neto':0,'iva':0,'total':0}
            totales['servicio'] = {'exento':0,'neto':0,'iva':0,'total':0}
            totales['importacion'] = {'exento':0,'neto':0,'iva':0,'total':0}
            totales['combustible'] = {'exento':0,'neto':0,'iva':0,'total':0}
            totales['pequenio_contribuyente'] = {'exento':0,'neto':0,'iva':0,'total':0}

            journal_ids = [x.id for x in w.diarios_id]
            period_ids = [x.id for x in w.periodos_id]
            facturas = self.pool.get('account.invoice').search(cr, uid, [
                ('state','in',['open','paid']), ('journal_id','in',journal_ids), ('period_id','in',period_ids)
            ], order='date_invoice')

            lineas = []
            for f in self.pool.get('account.invoice').browse(cr, uid, facturas):

                tipo_cambio = 1
                if f.currency_id.id != f.company_id.currency_id.id:
                    total = 0
                    for l in f.move_id.line_id:
                        if l.account_id.id == f.account_id.id:
                            total += l.credit - l.debit
                    tipo_cambio = abs(total / f.amount_total)

                tipo = 'FACT'
                if f.type != 'in_invoice':
                    tipo = 'NC'
                if f.pequenio_contribuyente:
                    tipo += ' PEQ'

                linea = {
                    'estado': f.state,
                    'tipo': tipo,
                    'fecha': f.date_invoice,
                    'numero': f.supplier_invoice_number or f.reference or '',
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

                for l in f.invoice_line:
                    precio = ( l.price_unit * (1-(l.discount or 0.0)/100.0) ) * tipo_cambio
                    if tipo == 'NC':
                        precio = precio * -1

                    r = self.pool.get('account.tax').compute_all(cr, uid, l.invoice_line_tax_id, precio, l.quantity, product=l.product_id, partner=l.invoice_id.partner_id)

                    linea['base'] += r['total']
                    if len(l.invoice_line_tax_id) > 0:
                        linea[f.tipo_gasto] += r['total']
                        for i in r['taxes']:
                            if i['base_code_id'] == w.base_id.id and i['tax_code_id'] == w.impuesto_id.id:
                                linea['iva'] += i['amount']
                            elif i['amount'] > 0:
                                linea[f.tipo_gasto+'_exento'] += i['amount']
                    else:
                        linea[f.tipo_gasto+'_exento'] += r['total']

                linea['total'] = linea[f.tipo_gasto] + linea['iva']
                if f.pequenio_contribuyente:
                    linea['total'] = linea[f.tipo_gasto+'_exento']

                if f.pequenio_contribuyente:
                    totales['pequenio_contribuyente']['exento'] += linea[f.tipo_gasto+'_exento']
                    totales['pequenio_contribuyente']['neto'] += linea[f.tipo_gasto]
                    totales['pequenio_contribuyente']['iva'] += linea['iva']
                    totales['pequenio_contribuyente']['total'] += linea['total']

                totales[f.tipo_gasto]['exento'] += linea[f.tipo_gasto+'_exento']
                totales[f.tipo_gasto]['neto'] += linea[f.tipo_gasto]
                totales[f.tipo_gasto]['iva'] += linea['iva']
                totales[f.tipo_gasto]['total'] += linea['total']

                lineas.append(linea)


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
            hoja.write(y, 3, 'PROVEEDOR')
            hoja.write(y, 4, 'NIT')
            hoja.write(y, 5, 'COMP.')
            hoja.write(y, 6, 'SERV.')
            hoja.write(y, 7, 'COMP. EXE')
            hoja.write(y, 8, 'SERV. EXE')
            hoja.write(y, 9, 'COMB.')
            hoja.write(y, 10, 'COMB. EXE')
            hoja.write(y, 11, 'IMP.')
            hoja.write(y, 12, 'IVA')
            hoja.write(y, 13, 'TOTAL')

            for linea in lineas:
                y += 1
                hoja.write(y, 0, linea['tipo'])
                hoja.write(y, 1, linea['fecha'])
                hoja.write(y, 2, linea['numero'])
                hoja.write(y, 3, linea['proveedor'].name)
                hoja.write(y, 4, linea['proveedor'].vat)
                hoja.write(y, 5, linea['compra'])
                hoja.write(y, 6, linea['servicio'])
                hoja.write(y, 7, linea['compra_exento'])
                hoja.write(y, 8, linea['servicio_exento'])
                hoja.write(y, 9, linea['combustible'])
                hoja.write(y, 10, linea['combustible_exento'])
                hoja.write(y, 11, linea['importacion'])
                hoja.write(y, 12, linea['iva'])
                hoja.write(y, 13, linea['total'])

            y += 2
            hoja.write(y, 3, 'EXENTO')
            hoja.write(y, 4, 'NETO')
            hoja.write(y, 5, 'IVA')
            hoja.write(y, 6, 'TOTAL')
            y += 1
            hoja.write(y, 1, 'COMPRAS')
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
            hoja.write(y, 1, 'IMPORTACION')
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
            'res_model': 'l10n_gt_extra.asistente_compras_reporte_excel',
            'res_id': ids[0],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

asistente_compras_reporte_excel()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
