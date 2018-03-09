# -*- encoding: utf-8 -*-

from odoo import api, models, fields

class ReporteDiario(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_diario'

    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde):
        saldo_inicial = 0
        movimientos_cuentas_todos_anios = self.env['account.move.line'].search([
            ('account_id','=',cuenta.id),
            ('date','<',fecha_desde)])
        for m in movimientos_cuentas_todos_anios:
            saldo_inicial += m.debit - m.credit
        return saldo_inicial

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde):
        saldo_inicial = 0
        fecha = fields.Date.from_string(fecha_desde)
        movimientos_cuentas_anio_actual = self.env['account.move.line'].search([
            ('account_id','=',cuenta.id),
            ('date','>=',fecha.strftime('%Y-1-1')),
            ('date','<',fecha_desde)])
        for m in movimientos_cuentas_anio_actual:
            saldo_inicial += m.debit - m.credit
        return saldo_inicial

    def lineas(self, datos):
        totales = {}
        lineas_resumidas = {}
        
        totales['debe'] = 0
        totales['haber'] = 0
        totales['saldo_inicial'] = 0
        totales['saldo_final'] = 0

        account_ids = [x for x in datos['cuentas_id']]
        movimientos = self.env['account.move.line'].search([
            ('account_id','in',account_ids),
            ('date','<=',datos['fecha_hasta']),
            ('date','>=',datos['fecha_desde'])])

        for m in movimientos:
            totales['debe'] += m.debit
            totales['haber'] += m.credit
            llave = m.account_id.id
            if llave not in lineas_resumidas:
                lineas_resumidas[llave] = {
                    'codigo': m.account_id.code,
                    'cuenta': m.account_id,
                    'fecha': m.date,
                    'saldo_inicial': 0,
                    'debe': m.debit,
                    'haber': m.credit,
                    'saldo_final': 0
                }
            else:
                lineas_resumidas[llave]['debe'] += m.debit
                lineas_resumidas[llave]['haber'] += m.credit

        for l in lineas_resumidas.values():
            if l['cuenta'].user_type_id.include_initial_balance:
                print l['cuenta']
                l['saldo_inicial'] += self.retornar_saldo_inicial_inicio_anio(l['cuenta'],datos['fecha_desde'])
                l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
                totales['saldo_inicial'] += l['saldo_inicial'] 
                totales['saldo_final'] += l['saldo_final']
            else:
                l['saldo_inicial'] += self.retornar_saldo_inicial_todos_anios(l['cuenta'],datos['fecha_desde'])
                l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
                totales['saldo_inicial'] += l['saldo_inicial']
                totales['saldo_final'] += l['saldo_final']

        return {'lineas': lineas_resumidas.values(),'totales': totales }

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        diario = self.env['account.move.line'].browse(data['form']['cuentas_id'][0])

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
        }
        return self.env['report'].render('l10n_gt_extra.reporte_diario', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
