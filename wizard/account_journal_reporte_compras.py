# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io
import logging

class AsistenteReporteCompras(models.TransientModel):
    _name = 'l10n_gt_extra.reporte_compras.wizard'
    _description = 'Libro de Compras'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuestos_id = fields.Many2many("account.tax", string="Impuestos", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo')
    archivo = fields.Binary('Archivo')

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.reporte_compras.wizard',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_gt_extra.reporte_compras_wizard_report').with_context(landscape=True).report_action(self, data=data)

    def print_report_excel(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuestos_id'] = [i.id for i in w.impuestos_id]
            dict['diarios_id'] =[x.id for x in w.diarios_id]

            res = self.env['report.l10n_gt_extra.reporte_compras'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']

            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte')
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
            formato_numero = libro.add_format({'num_format': '#,##0.00'})

            hoja.write(0, 0, 'Libro de compras y servicios')
            hoja.write(2, 0, 'Número de identificación tributaria')
            hoja.write(2, 1, w.diarios_id[0].company_id.partner_id.vat)
            hoja.write(3, 0, 'Nombre comercial')
            hoja.write(3, 1, w.diarios_id[0].direccion.name if w.diarios_id[0].direccion else w.diarios_id[0].company_id.partner_id.name)
            hoja.write(2, 3, 'Domicilio fiscal')
            hoja.write(2, 4, w.diarios_id[0].direccion.contact_address if w.diarios_id[0].direccion else w.diarios_id[0].company_id.partner_id.contact_address)
            hoja.write(3, 3, 'Registro del')
            hoja.write(3, 4, w.fecha_desde, formato_fecha)
            hoja.write(3, 5, 'al')
            hoja.write(3, 6, w.fecha_hasta, formato_fecha)

            y = 5
            hoja.write(y, 0, 'Tipo')
            hoja.write(y, 1, 'Fecha')
            hoja.write(y, 2, 'Doc')
            hoja.write(y, 3, 'Proveedor')
            hoja.write(y, 4, 'NIT')
            hoja.write(y, 5, 'Bienes local')
            hoja.write(y, 6, 'Bienes local exento')
            hoja.write(y, 7, 'Bienes extranjero')
            hoja.write(y, 8, 'Servicios local')
            hoja.write(y, 9, 'Servicios local exento')
            hoja.write(y, 10, 'Servicios extranjero')
            hoja.write(y, 11, 'Combustibles local')
            hoja.write(y, 12, 'Combustibles local exento')
            hoja.write(y, 13, 'Combustibles extranjero')
            hoja.write(y, 14, 'Pequeños contribuyentes')
            hoja.write(y, 15, 'IVA')
            hoja.write(y, 16, 'Total')

            for linea in lineas:
                y += 1
                hoja.write(y, 0, linea['tipo'])
                hoja.write(y, 1, linea['fecha'], formato_fecha)
                hoja.write(y, 2, linea['numero'])
                hoja.write(y, 3, linea['proveedor']['name'])
                hoja.write(y, 4, linea['proveedor']['vat'])
                hoja.write(y, 5, linea['bien_local'], formato_numero)
                hoja.write(y, 6, linea['bien_local_exento'], formato_numero)
                hoja.write(y, 7, linea['bien_extranjero'] + linea['bien_extranjero_exento'], formato_numero)
                hoja.write(y, 8, linea['servicio_local'], formato_numero)
                hoja.write(y, 9, linea['servicio_local_exento'], formato_numero)
                hoja.write(y, 10, linea['servicio_extranjero'] + linea['servicio_extranjero_exento'], formato_numero)
                hoja.write(y, 11, linea['combustible_local'], formato_numero)
                hoja.write(y, 12, linea['combustible_local_exento'], formato_numero)
                hoja.write(y, 13, linea['combustible_extranjero'] + linea['combustible_extranjero_exento'], formato_numero)
                hoja.write(y, 14, linea['pequeño'] + linea['pequeño_exento'], formato_numero)
                hoja.write(y, 15, linea['iva'], formato_numero)
                hoja.write(y, 16, linea['total'], formato_numero)

            y += 1
            hoja.write(y, 4, 'Totales')
            hoja.write(y, 5, totales['bien_local']['neto'], formato_numero)
            hoja.write(y, 6, totales['bien_local']['exento'], formato_numero)
            hoja.write(y, 7, totales['bien_extranjero']['neto'] + totales['bien_extranjero']['exento'], formato_numero)
            hoja.write(y, 8, totales['servicio_local']['neto'], formato_numero)
            hoja.write(y, 9, totales['servicio_local']['exento'], formato_numero)
            hoja.write(y, 10, totales['servicio_extranjero']['neto'] + totales['servicio_extranjero']['exento'], formato_numero)
            hoja.write(y, 11, totales['combustible_local']['neto'], formato_numero)
            hoja.write(y, 12, totales['combustible_local']['exento'], formato_numero)
            hoja.write(y, 13, totales['combustible_extranjero']['neto'] + totales['combustible_extranjero']['exento'], formato_numero)
            hoja.write(y, 14, totales['pequeño']['neto'] + totales['pequeño']['exento'], formato_numero)
            hoja.write(y, 15, totales['bien_local']['iva'] + totales['bien_extranjero']['iva'] + totales['servicio_local']['iva'] + totales['servicio_extranjero']['iva'] + totales['combustible_local']['iva'] + totales['combustible_extranjero']['iva'] + totales['pequeño']['iva'], formato_numero)
            hoja.write(y, 16, totales['bien_local']['total'] + totales['bien_extranjero']['total'] + totales['servicio_local']['total'] + totales['servicio_extranjero']['total'] + totales['combustible_local']['total'] + totales['combustible_extranjero']['total'] + totales['pequeño']['total'], formato_numero)

            y += 2
            hoja.write(y, 0, 'Cantidad de facturas')
            hoja.write(y, 1, totales['num_facturas'])
            y += 1
            hoja.write(y, 0, 'Total crédito fiscal')
            hoja.write(y, 1, totales['bien_local']['iva'] + totales['bien_extranjero']['iva'] + totales['servicio_local']['iva'] + totales['servicio_extranjero']['iva'] + totales['combustible_local']['iva'] + totales['combustible_extranjero']['iva'] + totales['pequeño']['iva'], formato_numero)

            y += 2
            hoja.write(y, 3, 'Exento')
            hoja.write(y, 4, 'Neto')
            hoja.write(y, 5, 'IVA')
            hoja.write(y, 6, 'Total')
            y += 1
            hoja.write(y, 1, 'Bienes locales')
            hoja.write(y, 3, totales['bien_local']['exento'], formato_numero)
            hoja.write(y, 4, totales['bien_local']['neto'], formato_numero)
            hoja.write(y, 5, totales['bien_local']['iva'], formato_numero)
            hoja.write(y, 6, totales['bien_local']['total'], formato_numero)
            y += 1
            hoja.write(y, 1, 'Servicios locales')
            hoja.write(y, 3, totales['servicio_local']['exento'], formato_numero)
            hoja.write(y, 4, totales['servicio_local']['neto'], formato_numero)
            hoja.write(y, 5, totales['servicio_local']['iva'], formato_numero)
            hoja.write(y, 6, totales['servicio_local']['total'], formato_numero)
            y += 1
            hoja.write(y, 1, 'Bienes extranjeros')
            hoja.write(y, 3, totales['bien_extranjero']['exento'], formato_numero)
            hoja.write(y, 4, totales['bien_extranjero']['neto'], formato_numero)
            hoja.write(y, 5, totales['bien_extranjero']['iva'], formato_numero)
            hoja.write(y, 6, totales['bien_extranjero']['total'], formato_numero)
            y += 1
            hoja.write(y, 1, 'Combustibles locales')
            hoja.write(y, 3, totales['combustible_local']['exento'], formato_numero)
            hoja.write(y, 4, totales['combustible_local']['neto'], formato_numero)
            hoja.write(y, 5, totales['combustible_local']['iva'], formato_numero)
            hoja.write(y, 6, totales['combustible_local']['total'], formato_numero)
            y += 1
            hoja.write(y, 1, 'Servicios extranjeros')
            hoja.write(y, 3, totales['servicio_extranjero']['exento'], formato_numero)
            hoja.write(y, 4, totales['servicio_extranjero']['neto'], formato_numero)
            hoja.write(y, 5, totales['servicio_extranjero']['iva'], formato_numero)
            hoja.write(y, 6, totales['servicio_extranjero']['total'], formato_numero)
            y += 1
            hoja.write(y, 1, 'Combustibles extranjeros')
            hoja.write(y, 3, totales['combustible_extranjero']['exento'], formato_numero)
            hoja.write(y, 4, totales['combustible_extranjero']['neto'], formato_numero)
            hoja.write(y, 5, totales['combustible_extranjero']['iva'], formato_numero)
            hoja.write(y, 6, totales['combustible_extranjero']['total'], formato_numero)
            y += 1
            hoja.write(y, 1, 'Pequeños contribuyentes')
            hoja.write(y, 3, totales['pequeño']['exento'], formato_numero)
            hoja.write(y, 4, totales['pequeño']['neto'], formato_numero)
            hoja.write(y, 5, totales['pequeño']['iva'], formato_numero)
            hoja.write(y, 6, totales['pequeño']['total'], formato_numero)
            y += 1
            hoja.write(y, 1, 'Totales')
            hoja.write(y, 3, totales['bien_local']['exento'] + totales['bien_extranjero']['exento'] + totales['servicio_local']['exento'] + totales['servicio_extranjero']['exento'] + totales['combustible_local']['exento'] + totales['combustible_extranjero']['exento'] + totales['pequeño']['exento'], formato_numero)
            hoja.write(y, 4, totales['bien_local']['neto'] + totales['bien_extranjero']['neto'] + totales['servicio_local']['neto'] + totales['servicio_extranjero']['neto'] + totales['combustible_local']['neto'] + totales['combustible_extranjero']['neto'] + totales['pequeño']['neto'], formato_numero)
            hoja.write(y, 5, totales['bien_local']['iva'] + totales['bien_extranjero']['iva'] + totales['servicio_local']['iva'] + totales['servicio_extranjero']['iva'] + totales['combustible_local']['iva'] + totales['combustible_extranjero']['iva'] + totales['pequeño']['iva'], formato_numero)
            hoja.write(y, 6, totales['bien_local']['total'] + totales['bien_extranjero']['total'] + totales['servicio_local']['total'] + totales['servicio_extranjero']['total'] + totales['combustible_local']['total'] + totales['combustible_extranjero']['total'] + totales['pequeño']['total'], formato_numero)

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_de_compras.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.reporte_compras.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
