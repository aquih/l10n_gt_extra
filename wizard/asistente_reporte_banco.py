# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io

class AsistenteReporteBanco(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_banco'
    _description = 'Reporte de Bancos'

    def _default_cuenta(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            return self.env.context.get('active_ids')[0]
        else:
            return None

    cuenta_bancaria_id = fields.Many2one("account.account", string="Cuenta", required=True, default=_default_cuenta)
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime("%Y-%m-01"))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime("%Y-%m-%d"))
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo')

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_banco',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_gt_extra.action_reporte_banco').report_action(self, data=data)

    def print_report_excel(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['cuenta_bancaria_id'] = [w.cuenta_bancaria_id.id, w.cuenta_bancaria_id.name]
            lineas = self.env['report.l10n_gt_extra.reporte_banco'].lineas(dict)
            balance_inicial = self.env['report.l10n_gt_extra.reporte_banco'].balance_inicial(dict)

            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte')
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
            formato_numero = libro.add_format({'num_format': '#,##0.00'})

            hoja.write(0, 0, self.env.company.name + ': Libro de banco')
            hoja.write(2, 0, 'Cuenta:')
            hoja.write(2, 1, w.cuenta_bancaria_id.display_name)
            hoja.write(3, 0, 'Fecha inicial')
            hoja.write(3, 1, w.fecha_desde, formato_fecha)
            hoja.write(4, 0, 'Fecha final')
            hoja.write(4, 1, w.fecha_hasta, formato_fecha)

            y = 6
            hoja.write(y, 0, 'Fecha')
            hoja.write(y, 1, 'Doc')
            hoja.write(y, 2, 'Nombre')
            hoja.write(y, 3, 'Concepto')
            hoja.write(y, 4, 'Credito')
            hoja.write(y, 5, 'Debito')
            hoja.write(y, 6, 'Balance')

            y += 1
            hoja.write(y, 2, 'Saldo inicial')
            if balance_inicial['usar_balance_moneda']:
                hoja.write(y, 6, balance_inicial['balance_moneda'], formato_numero)
            else:
                hoja.write(y, 6, balance_inicial['balance'], formato_numero)

            for linea in lineas:
                y += 1
                hoja.write(y, 0, linea['fecha'])
                hoja.write(y, 1, linea['documento'])
                hoja.write(y, 2, linea['nombre'])
                hoja.write(y, 3, linea['concepto'])
                hoja.write(y, 4, linea['debito'], formato_numero)
                hoja.write(y, 5, linea['credito'], formato_numero)
                hoja.write(y, 6, linea['balance'], formato_numero)

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_de_banco.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.asistente_reporte_banco',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
