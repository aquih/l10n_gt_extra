# -*- encoding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError
import logging

class ReporteVentas(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_ventas'
    _description = 'Libro de Ventas'

    def columnas_mostrar(self):
        columnas_totales = {'bl', 'ble', 'be', 'sl', 'sle', 'se', 'cl', 'cle', 'ce', 'p'}
        columnas_ocultar = set()

        param = self.env['ir.config_parameter'].sudo().get_param('libro_ventas_columnas_ocultar')
        if param:
            columnas_ocultar = set(param.split(','))

        return columnas_totales - columnas_ocultar

    def lineas(self, datos):
        totales = {}

        totales['num_facturas'] = 0
        totales['bien_local'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['bien_extranjero'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['servicio_local'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['servicio_extranjero'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['combustible_local'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        totales['combustible_extranjero'] = {'exento': 0, 'neto': 0, 'iva': 0, 'total': 0}
        
        journal_ids = [x for x in datos['diarios_id']]
        filtro = [
            ('state','in',['posted','cancel']),
            ('journal_id','in',journal_ids),
            ('date','<=',datos['fecha_hasta']),
            ('date','>=',datos['fecha_desde']),
            ('amount_total','!=',0),
        ]
        
        if 'type' in self.env['account.move'].fields_get():
            filtro.append(('type','in',['out_invoice','out_refund']))
        else:
            filtro.append(('move_type','in',['out_invoice','out_refund']))

        facturas = self.env['account.move'].search(filtro)
        impuestos = self.env['account.tax'].browse(datos['impuestos_id'])

        lineas = []
        for f in facturas:
            totales['num_facturas'] += 1

            tipo = 'FACT'
            tipo_interno_factura = f.type if 'type' in f.fields_get() else f.move_type
            if tipo_interno_factura != 'out_invoice':
                tipo = 'NC'
            if f.nota_debito:
                tipo = 'ND'

            numero = f.name or '-'

            # Por si es un diario de rango de facturas
            if f.journal_id.facturas_por_rangos or f.journal_id.usar_referencia:
                numero = f.ref

            # Por si usa factura electrónica
            if 'firma_fel' in f.fields_get() and f.firma_fel:
                numero = str(f.serie_fel) + '-' + str(f.numero_fel)

            linea = {
                'account_move_id': f.id,
                'estado': f.state,
                'tipo': tipo,
                'fecha': f.date,
                'numero': numero,
                'cliente': f.partner_id,
                'bien_local': 0,
                'bien_local_exento': 0,
                'bien_extranjero': 0,
                'bien_extranjero_exento': 0,
                'servicio_local': 0,
                'servicio_local_exento': 0,
                'servicio_extranjero': 0,
                'servicio_extranjero_exento': 0,
                'combustible_local': 0,
                'combustible_local_exento': 0,
                'combustible_extranjero': 0,
                'combustible_extranjero_exento': 0,
                'base': 0,
                'iva': 0,
                'total': 0
            }

            if f.state == 'cancel':
                lineas.append(linea)
                continue

            for l in f.invoice_line_ids:
                tipo_cambio = 1
                if f.company_id.id != self.env.company.id:
                    tipo_cambio = self.env['res.currency']._get_conversion_rate(f.company_id.currency_id, self.env.company.currency_id)
                elif f.currency_id.id != f.company_id.currency_id.id and l.amount_currency:
                    tipo_cambio = l.balance / l.amount_currency

                precio = ( l.price_unit * ( 1 - ( l.discount or 0.0 ) / 100.0 ) )

                if tipo == 'NC':
                    precio = precio * -1

                # Vieja forma de calcular tipo de producto
                if f.tipo_para_iva == False:
                    tipo_linea = f.tipo_gasto or 'mixto'
                    if tipo_linea == 'mixto':
                        if l.product_id.type != 'service':
                            tipo_linea = 'bien_local'
                        else:
                            tipo_linea = 'servicio_local'
                    elif f.tipo_gasto == 'compra':
                        tipo_linea = 'bien_local'
                    elif f.tipo_gasto == 'servicio':
                        tipo_linea = 'servicio_local'
                    elif f.tipo_gasto == 'importacion':
                        if l.product_id.type != 'service':
                            tipo_linea = 'bien_extranjero'
                        else:
                            tipo_linea = 'servicio_extranjero'
                    elif f.tipo_gasto == 'combustible':
                        tipo_linea = 'combustible_local'

                # Nueva forma de calcular tipo de producto
                else:
                    if l.product_id.type != 'service':
                        tipo_linea = 'bien_local' if f.tipo_para_iva == 'bien_servicio_local' else 'bien_extranjero'
                    else:
                        tipo_linea = 'servicio_local' if f.tipo_para_iva == 'bien_servicio_local' else 'servicio_extranjero'
                    
                    if f.tipo_para_iva == 'combustible_local':
                        tipo_linea = 'combustible_local'
                    elif f.tipo_para_iva == 'combustible_extranjero':
                        tipo_linea = 'combustible_extranjero'

                # Siempre enviar cantidad y precio correctos. Por qué algunos impuestos se calculan por cantidades.
                # También pasar contexto para que tome el tipo de cambio correcto al calcular impuestos.
                r = l.with_context(tasa_de_conversion=1/tipo_cambio).tax_ids.compute_all(precio, currency=f.currency_id, quantity=l.quantity, product=l.product_id, partner=f.partner_id)

                linea['base'] += r['total_excluded'] * tipo_cambio
                totales[tipo_linea]['total'] += r['total_excluded'] * tipo_cambio
                
                # No es exenta si trae el impuesto seleccionado en el wizard
                if any(impuesto in l.tax_ids for impuesto in impuestos):
                    linea[tipo_linea] += r['total_excluded'] * tipo_cambio
                    totales[tipo_linea]['neto'] += r['total_excluded'] * tipo_cambio
                else:
                    linea[tipo_linea+'_exento'] += r['total_excluded'] * tipo_cambio
                    totales[tipo_linea]['exento'] += r['total_excluded'] * tipo_cambio

                for i in r['taxes']:
                    if i['id'] in [impuesto.id for impuesto in impuestos]:
                        linea['iva'] += i['amount'] * tipo_cambio
                        totales[tipo_linea]['iva'] += i['amount'] * tipo_cambio
                        totales[tipo_linea]['total'] += i['amount'] * tipo_cambio
                    elif (i['amount'] > 0 and tipo != 'NC') or (i['amount'] < 0 and tipo == 'NC'):
                        linea[tipo_linea+'_exento'] += i['amount'] * tipo_cambio
                        totales[tipo_linea]['exento'] += i['amount'] * tipo_cambio
                        totales[tipo_linea]['total'] += i['amount'] * tipo_cambio

            linea['total'] += linea['bien_local'] + linea['bien_local_exento'] + linea['bien_extranjero'] + linea['bien_extranjero_exento']
            linea['total'] += linea['servicio_local'] + linea['servicio_local_exento'] + linea['servicio_extranjero'] + linea['servicio_extranjero_exento']
            linea['total'] += linea['combustible_local'] + linea['combustible_local_exento'] + linea['combustible_extranjero'] + linea['combustible_extranjero_exento']
            linea['total'] += linea['iva']

            lineas.append(linea)

        lineas = sorted(lineas, key = lambda i: str(i['fecha']) + str(i['numero']))

        if datos['resumido']:
            lineas_resumidas = {}
            for l in lineas:
                llave = l['tipo']+str(l['fecha'])
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
                l['numero'] = str(l['facturas'][0]) + ' al ' + str(l['facturas'][-1])

            lineas = sorted(lineas_resumidas.values(), key=lambda l: l['tipo']+str(l['fecha']))

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
            'direccion_diario': diario.direccion,
            'current_company_id': self.env.company,
            'columnas_mostrar': self.columnas_mostrar()
        }
