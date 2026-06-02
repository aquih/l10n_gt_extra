# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io
import logging

class AsistenteReporteVentas(models.TransientModel):
    _name = 'l10n_gt_extra.reporte_ventas.wizard'
    _description = 'Libro de Ventas'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuestos_id = fields.Many2many("account.tax", string="Impuestos", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    resumido = fields.Boolean(string="Resumido")
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo')
    archivo = fields.Binary('Archivo')

    def generar_libro(self, archivo, datos_wizard, datos_lineas):
        libro = xlsxwriter.Workbook(archivo)
        hoja = libro.add_worksheet('Reporte')

        formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
        formato_numero = libro.add_format({'num_format': '#,##0.00'})

        lineas = datos_lineas['lineas']
        totales = datos_lineas['totales']

        columnas_mostrar = self.env['report.l10n_gt_extra.reporte_ventas'].columnas_mostrar()
        diario = self.diarios_id[0]

        hoja.write(0, 0, 'Libro de ventas y servicios')
        hoja.write(2, 0, 'Número de identificación tributaria')
        hoja.write(2, 1, self.env.company.partner_id.vat)
        hoja.write(3, 0, 'Nombre comercial')
        hoja.write(3, 1, diario.direccion.name if diario.direccion else diario.company_id.partner_id.name)
        hoja.write(2, 3, 'Domicilio fiscal')
        hoja.write(2, 4, diario.direccion._display_address(without_company=True) if diario.direccion else diario.company_id.partner_id._display_address(without_company=True))
        hoja.write(3, 3, 'Registro del')
        hoja.write(3, 4, self.fecha_desde, formato_fecha)
        hoja.write(3, 5, 'al')
        hoja.write(3, 6, self.fecha_hasta, formato_fecha)

        y = 5
        hoja.write(y, 0, 'Tipo')
        hoja.write(y, 1, 'Fecha')
        hoja.write(y, 2, 'Doc')
        hoja.write(y, 3, 'Cliente')
        hoja.write(y, 4, 'NIT')
        x = 5
        if 'bl' in columnas_mostrar:
            hoja.write(y, x, 'Bienes local')
            x += 1
        if 'ble' in columnas_mostrar:
            hoja.write(y, x, 'Bienes local exento')
            x += 1
        if 'be' in columnas_mostrar:
            hoja.write(y, x, 'Bienes extranjero')
            x += 1
        if 'bee' in columnas_mostrar:
            hoja.write(y, x, 'Bienes extranjero exento')
            x += 1
        if 'sl' in columnas_mostrar:
            hoja.write(y, x, 'Servicios local')
            x += 1
        if 'sle' in columnas_mostrar:
            hoja.write(y, x, 'Servicios local exento')
            x += 1
        if 'se' in columnas_mostrar:
            hoja.write(y, x, 'Servicios extranjero')
            x += 1
        if 'see' in columnas_mostrar:
            hoja.write(y, x, 'Servicios extranjero exento')
            x += 1
        if 'cl' in columnas_mostrar:
            hoja.write(y, x, 'Combustibles local')
            x += 1
        if 'cle' in columnas_mostrar:
            hoja.write(y, x, 'Combustibles local exento')
            x += 1
        if 'ce' in columnas_mostrar:
            hoja.write(y, x, 'Combustibles extranjero')
            x += 1
        if 'cee' in columnas_mostrar:
            hoja.write(y, x, 'Combustibles extranjero exento')
            x += 1
        hoja.write(y, x, 'IVA')
        hoja.write(y, x+1, 'Total')
        for linea in lineas:
            y += 1
            hoja.write(y, 0, linea['tipo'])
            hoja.write(y, 1, linea['fecha'], formato_fecha)
            hoja.write(y, 2, linea['numero'])
            hoja.write(y, 3, linea['cliente'].name)
            hoja.write(y, 4, linea['cliente'].vat or linea['cliente'].cui)
            x = 5
            if 'bl' in columnas_mostrar:
                hoja.write(y, x, linea['bien_local'], formato_numero)
                x += 1
            if 'ble' in columnas_mostrar:
                hoja.write(y, x, linea['bien_local_exento'], formato_numero)
                x += 1
            if 'be' in columnas_mostrar:
                hoja.write(y, x, linea['bien_extranjero'], formato_numero)
                x += 1
            if 'bee' in columnas_mostrar:
                hoja.write(y, x, linea['bien_extranjero_exento'], formato_numero)
                x += 1
            if 'sl' in columnas_mostrar:
                hoja.write(y, x, linea['servicio_local'], formato_numero)
                x += 1
            if 'sle' in columnas_mostrar:
                hoja.write(y, x, linea['servicio_local_exento'], formato_numero)
                x += 1
            if 'se' in columnas_mostrar:
                hoja.write(y, x, linea['servicio_extranjero'], formato_numero)
                x += 1
            if 'see' in columnas_mostrar:
                hoja.write(y, x, linea['servicio_extranjero_exento'], formato_numero)
                x += 1
            if 'cl' in columnas_mostrar:
                hoja.write(y, x, linea['combustible_local'], formato_numero)
                x += 1
            if 'cle' in columnas_mostrar:
                hoja.write(y, x, linea['combustible_local_exento'], formato_numero)
                x += 1
            if 'ce' in columnas_mostrar:
                hoja.write(y, x, linea['combustible_extranjero'], formato_numero)
                x += 1
            if 'cee' in columnas_mostrar:
                hoja.write(y, x, linea['combustible_extranjero_exento'], formato_numero)
                x += 1
            hoja.write(y, x, linea['iva'], formato_numero)
            hoja.write(y, x+1, linea['total'], formato_numero)

        y += 1
        hoja.write(y, 4, 'Totales')
        x = 5
        if 'bl' in columnas_mostrar:
            hoja.write(y, x, totales['bien_local']['neto'], formato_numero)
            x += 1
        if 'ble' in columnas_mostrar:
            hoja.write(y, x, totales['bien_local']['exento'], formato_numero)
            x += 1
        if 'be' in columnas_mostrar:
            hoja.write(y, x, totales['bien_extranjero']['neto'], formato_numero)
            x += 1
        if 'bee' in columnas_mostrar:
            hoja.write(y, x, totales['bien_extranjero']['exento'], formato_numero)
            x += 1
        if 'sl' in columnas_mostrar:
            hoja.write(y, x, totales['servicio_local']['neto'], formato_numero)
            x += 1
        if 'sle' in columnas_mostrar:
            hoja.write(y, x, totales['servicio_local']['exento'], formato_numero)
            x += 1
        if 'se' in columnas_mostrar:
            hoja.write(y, x, totales['servicio_extranjero']['neto'], formato_numero)
            x += 1
        if 'see' in columnas_mostrar:
            hoja.write(y, x, totales['servicio_extranjero']['exento'], formato_numero)
            x += 1
        if 'cl' in columnas_mostrar:
            hoja.write(y, x, totales['combustible_local']['neto'], formato_numero)
            x += 1
        if 'cle' in columnas_mostrar:
            hoja.write(y, x, totales['combustible_local']['exento'], formato_numero)
            x += 1
        if 'ce' in columnas_mostrar:
            hoja.write(y, x, totales['combustible_extranjero']['neto'], formato_numero)
            x += 1
        if 'cee' in columnas_mostrar:
            hoja.write(y, x, totales['combustible_extranjero']['exento'], formato_numero)
            x += 1
        hoja.write(y, x, totales['bien_local']['iva'] + totales['bien_extranjero']['iva'] + totales['servicio_local']['iva'] + totales['servicio_extranjero']['iva'] + totales['combustible_local']['iva'] + totales['combustible_extranjero']['iva'], formato_numero)
        hoja.write(y, x+1, totales['bien_local']['total'] + totales['bien_extranjero']['total'] + totales['servicio_local']['total'] + totales['servicio_extranjero']['total'] + totales['combustible_local']['total'] + totales['combustible_extranjero']['total'], formato_numero)

        y += 2
        hoja.write(y, 0, 'Cantidad de facturas')
        hoja.write(y, 1, totales['num_facturas'])
        y += 1
        hoja.write(y, 0, 'Total débito fiscal')
        hoja.write(y, 1, totales['bien_local']['iva'] + totales['bien_extranjero']['iva'] + totales['servicio_local']['iva'] + totales['servicio_extranjero']['iva'] + totales['combustible_local']['iva'] + totales['combustible_extranjero']['iva'], formato_numero)

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
        hoja.write(y, 1, 'Combustibles locales')
        hoja.write(y, 3, totales['combustible_local']['exento'], formato_numero)
        hoja.write(y, 4, totales['combustible_local']['neto'], formato_numero)
        hoja.write(y, 5, totales['combustible_local']['iva'], formato_numero)
        hoja.write(y, 6, totales['combustible_local']['total'], formato_numero)
        y += 1
        hoja.write(y, 1, 'Bienes extranjeros')
        hoja.write(y, 3, totales['bien_extranjero']['exento'], formato_numero)
        hoja.write(y, 4, totales['bien_extranjero']['neto'], formato_numero)
        hoja.write(y, 5, totales['bien_extranjero']['iva'], formato_numero)
        hoja.write(y, 6, totales['bien_extranjero']['total'], formato_numero)
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
        hoja.write(y, 1, 'Totales')
        hoja.write(y, 3, totales['bien_local']['exento'] + totales['bien_extranjero']['exento'] + totales['servicio_local']['exento'] + totales['servicio_extranjero']['exento'] + totales['combustible_local']['exento'] + totales['combustible_extranjero']['exento'], formato_numero)
        hoja.write(y, 4, totales['bien_local']['neto'] + totales['bien_extranjero']['neto'] + totales['servicio_local']['neto'] + totales['servicio_extranjero']['neto'] + totales['combustible_local']['neto'] + totales['combustible_extranjero']['neto'], formato_numero)
        hoja.write(y, 5, totales['bien_local']['iva'] + totales['bien_extranjero']['iva'] + totales['servicio_local']['iva'] + totales['servicio_extranjero']['iva'] + totales['combustible_local']['iva'] + totales['combustible_extranjero']['iva'], formato_numero)
        hoja.write(y, 6, totales['bien_local']['total'] + totales['bien_extranjero']['total'] + totales['servicio_local']['total'] + totales['servicio_extranjero']['total'] + totales['combustible_local']['total'] + totales['combustible_extranjero']['total'], formato_numero)

        return libro

    def print_report(self):
        datos_wizard = {
             'ids': [],
             'model': 'l10n_gt_extra.reporte_ventas.wizard',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_gt_extra.ventas_reporte_wizard_report').with_context(landscape=True).report_action(self, data=datos_wizard)

    def print_report_excel(self):
        for w in self:
            datos_wizard = w.read()[0]
            datos_lineas = self.env['report.l10n_gt_extra.reporte_ventas'].lineas(datos_wizard)

            archivo = io.BytesIO()
            libro = w.generar_libro(archivo, datos_wizard, datos_lineas)
            libro.close()

            datos = base64.b64encode(archivo.getvalue())
            w.write({'archivo':datos, 'name':'libro_de_ventas.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.reporte_ventas.wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
