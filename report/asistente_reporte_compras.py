# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io
import logging

class AsistenteReporteCompras(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_compras'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_compras',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_gt_extra.action_reporte_compras').with_context(landscape=True).report_action(self, data=data)

    def print_report_excel(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuesto_id'] = [w.impuesto_id.id, w.impuesto_id.name]
            dict['diarios_id'] =[x.id for x in w.diarios_id]

            res = self.env['report.l10n_gt_extra.reporte_compras'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']

            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte')
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})

            hoja.write(0, 0, 'LIBRO DE COMPRAS Y SERVICIOS')
            hoja.write(2, 0, 'NUMERO DE IDENTIFICACION TRIBUTARIA')
            hoja.write(2, 1, w.diarios_id[0].company_id.partner_id.vat)
            hoja.write(3, 0, 'NOMBRE COMERCIAL')
            hoja.write(3, 1, w.diarios_id[0].company_id.partner_id.name)
            hoja.write(2, 3, 'DOMICILIO FISCAL')
            hoja.write(2, 4, w.diarios_id[0].company_id.partner_id.street)
            hoja.write(3, 3, 'REGISTRO DEL')
            hoja.write(3, 4, w.fecha_desde, formato_fecha)
            hoja.write(3, 5, 'AL')
            hoja.write(3, 6, w.fecha_hasta, formato_fecha)

            y = 5
            hoja.write(y, 0, 'Tipo')
            hoja.write(y, 1, 'Fecha')
            hoja.write(y, 2, 'Doc')
            hoja.write(y, 3, 'Proveedor')
            hoja.write(y, 4, 'NIT')
            hoja.write(y, 5, 'Compras')
            hoja.write(y, 6, 'Compras exento')
            hoja.write(y, 7, 'Servicios')
            hoja.write(y, 8, 'Servicios exento')
            hoja.write(y, 9, 'Combustible')
            hoja.write(y, 10, 'Combustible exento')
            hoja.write(y, 11, 'Importaciones')
            hoja.write(y, 12, 'Pequeños contribuyentes')
            hoja.write(y, 13, 'IVA')
            hoja.write(y, 14, 'Total')

            for linea in lineas:
                y += 1
                hoja.write(y, 0, linea['tipo'])
                hoja.write(y, 1, linea['fecha'])
                hoja.write(y, 2, linea['numero'])
                hoja.write(y, 3, linea['proveedor']['name'])
                hoja.write(y, 4, linea['proveedor']['vat'])
                hoja.write(y, 5, linea['compra'])
                hoja.write(y, 6, linea['compra_exento'])
                hoja.write(y, 7, linea['servicio'])
                hoja.write(y, 8, linea['servicio_exento'])
                hoja.write(y, 9, linea['combustible'])
                hoja.write(y, 10, linea['combustible_exento'])
                hoja.write(y, 11, linea['importacion'] + linea['importacion_exento'])
                hoja.write(y, 12, linea['pequeño'] + linea['pequeño_exento'])
                hoja.write(y, 13, linea['iva'])
                hoja.write(y, 14, linea['total'])

            y += 1
            hoja.write(y, 3, 'Totales')
            hoja.write(y, 5, totales['compra']['neto'])
            hoja.write(y, 6, totales['compra']['exento'])
            hoja.write(y, 7, totales['servicio']['neto'])
            hoja.write(y, 8, totales['servicio']['exento'])
            hoja.write(y, 9, totales['combustible']['neto'])
            hoja.write(y, 10, totales['combustible']['exento'])
            hoja.write(y, 11, totales['importacion']['neto'] + totales['importacion']['exento'])
            hoja.write(y, 12, totales['pequeño']['neto'] + totales['pequeño']['exento'])
            hoja.write(y, 13, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'] + totales['pequeño']['iva'])
            hoja.write(y, 14, totales['compra']['total'] + totales['servicio']['total'] + totales['combustible']['total'] + totales['importacion']['total'] + totales['pequeño']['total'])

            y += 2
            hoja.write(y, 0, 'Cantidad de facturas')
            hoja.write(y, 1, totales['num_facturas'])
            y += 1
            hoja.write(y, 0, 'Total credito fiscal')
            hoja.write(y, 1, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'] + totales['pequeño']['iva'])

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
            hoja.write(y, 1, 'IMPORTACIONES')
            hoja.write(y, 3, totales['importacion']['exento'])
            hoja.write(y, 4, totales['importacion']['neto'])
            hoja.write(y, 5, totales['importacion']['iva'])
            hoja.write(y, 6, totales['importacion']['total'])
            y += 1
            hoja.write(y, 1, 'PEQUEÑOS CONTRIBUYENTES')
            hoja.write(y, 3, totales['pequeño']['exento'])
            hoja.write(y, 4, totales['pequeño']['neto'])
            hoja.write(y, 5, totales['pequeño']['iva'])
            hoja.write(y, 6, totales['pequeño']['total'])
            y += 1
            hoja.write(y, 1, 'TOTALES')
            hoja.write(y, 3, totales['compra']['exento']+totales['servicio']['exento']+totales['combustible']['exento']+totales['importacion']['exento']+totales['pequeño']['exento'])
            hoja.write(y, 4, totales['compra']['neto']+totales['servicio']['neto']+totales['combustible']['neto']+totales['importacion']['neto']+totales['pequeño']['neto'])
            hoja.write(y, 5, totales['compra']['iva']+totales['servicio']['iva']+totales['combustible']['iva']+totales['importacion']['iva']+totales['pequeño']['iva'])
            hoja.write(y, 6, totales['compra']['total']+totales['servicio']['total']+totales['combustible']['total']+totales['importacion']['total']+totales['pequeño']['total'])

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_de_compras.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.asistente_reporte_compras',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
