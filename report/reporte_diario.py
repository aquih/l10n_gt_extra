# -*- encoding: utf-8 -*-

from odoo import api, models, fields
import logging

class ReporteDiario(models.AbstractModel):
    _name = 'report.l10n_gt_extra.reporte_diario'

    def retornar_saldo_inicial_todos_anios(self, cuenta, fecha_desde):
        saldo_inicial = 0
        self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
        'from account_move_line l join account_account a on(l.account_id = a.id)'\
        'where a.id = %s and l.date < %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def retornar_saldo_inicial_inicio_anio(self, cuenta, fecha_desde):
        saldo_inicial = 0
        fecha = fields.Date.from_string(fecha_desde)
        self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, sum(l.debit) as debe, sum(l.credit) as haber '\
        'from account_move_line l join account_account a on(l.account_id = a.id)'\
        'where a.id = %s and l.date < %s and l.date >= %s group by a.id, a.code, a.name,l.debit,l.credit', (cuenta,fecha_desde,fecha.strftime('%Y-1-1')))
        for m in self.env.cr.dictfetchall():
            saldo_inicial += m['debe'] - m['haber']
        return saldo_inicial

    def lineas(self, datos):
        totales = {}
        lineas_resumidas = {}
        lineas=[]
        totales['debe'] = 0
        totales['haber'] = 0
        totales['saldo_inicial'] = 0
        totales['saldo_final'] = 0

        account_ids = [x for x in datos['cuentas_id']]
        movimientos = self.env['account.move.line'].search([
            ('account_id','in',account_ids),
            ('date','<=',datos['fecha_hasta']),
            ('date','>=',datos['fecha_desde'])])

        accounts_str = ','.join([str(x) for x in datos['cuentas_id']])
        if datos['agrupado_por_dia']:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, l.date as fecha, t.include_initial_balance as balance_inicial, sum(l.debit) as debe, sum(l.credit) as haber ' \
            	'from account_move_line l join account_account a on(l.account_id = a.id)' \
            	'join account_account_type t on (t.id = a.user_type_id)' \
            	'where a.id in ('+accounts_str+') and l.date >= %s and l.date <= %s group by a.id, a.code, a.name,l.date, t.include_initial_balance ORDER BY a.code',
            (datos['fecha_desde'], datos['fecha_hasta']))

            for r in self.env.cr.dictfetchall():
                totales['debe'] += r['debe']
                totales['haber'] += r['haber']
                linea = {
                    'id': r['id'],
                    'fecha': r['fecha'],
                    'codigo': r['codigo'],
                    'cuenta': r['cuenta'],
                    'saldo_inicial': 0,
                    'debe': r['debe'],
                    'haber': r['haber'],
                    'saldo_final': 0,
                    'balance_inicial': r['balance_inicial']
                }
                lineas.append(linea)

            for l in lineas:
                if not l['balance_inicial']:
                    l['saldo_inicial'] += self.retornar_saldo_inicial_inicio_anio(l['id'], datos['fecha_desde'])
                    l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
                    totales['saldo_inicial'] += l['saldo_inicial']
                    totales['saldo_final'] += l['saldo_final']
                else:
                    l['saldo_inicial'] += self.retornar_saldo_inicial_todos_anios(l['id'], datos['fecha_desde'])
                    l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
                    totales['saldo_inicial'] += l['saldo_inicial']
                    totales['saldo_final'] += l['saldo_final']

            cuentas_agrupadas = {}
            llave = 'fecha'
            for l in lineas:
                if l[llave] not in cuentas_agrupadas:
                    cuentas_agrupadas[l[llave]] = {'fecha': l[llave], 'cuentas': [], 'total_debe': 0, 'total_haber': 0}
                cuentas_agrupadas[l[llave]]['cuentas'].append(l)

            for la in cuentas_agrupadas.values():
                for l in la['cuentas']:
                    la['total_debe'] += l['debe']
                    la['total_haber'] += l['haber']

            lineas = cuentas_agrupadas.values()
        else:
            self.env.cr.execute('select a.id, a.code as codigo, a.name as cuenta, t.include_initial_balance as balance_inicial, sum(l.debit) as debe, sum(l.credit) as haber ' \
            	'from account_move_line l join account_account a on(l.account_id = a.id)' \
            	'join account_account_type t on (t.id = a.user_type_id)' \
            	'where a.id in ('+accounts_str+') and l.date >= %s and l.date <= %s group by a.id, a.code, a.name,t.include_initial_balance ORDER BY a.code',
            (datos['fecha_desde'], datos['fecha_hasta']))

            for r in self.env.cr.dictfetchall():
                totales['debe'] += r['debe']
                totales['haber'] += r['haber']
                linea = {
                    'id': r['id'],
                    'codigo': r['codigo'],
                    'cuenta': r['cuenta'],
                    'saldo_inicial': 0,
                    'debe': r['debe'],
                    'haber': r['haber'],
                    'saldo_final': 0,
                    'balance_inicial': r['balance_inicial']
                }
                lineas.append(linea)

            for l in lineas:
                if not l['balance_inicial']:
                    l['saldo_inicial'] += self.retornar_saldo_inicial_inicio_anio(l['id'], datos['fecha_desde'])
                    l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
                    totales['saldo_inicial'] += l['saldo_inicial']
                    totales['saldo_final'] += l['saldo_final']
                else:
                    l['saldo_inicial'] += self.retornar_saldo_inicial_todos_anios(l['id'], datos['fecha_desde'])
                    l['saldo_final'] += l['saldo_inicial'] + l['debe'] - l['haber']
                    totales['saldo_inicial'] += l['saldo_inicial']
                    totales['saldo_final'] += l['saldo_final']

        return {'lineas': lineas,'totales': totales }

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.get_report_values(docids, data)

    @api.model
    def get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        diario = self.env['account.move.line'].browse(data['form']['cuentas_id'][0])

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'lineas': self.lineas,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
