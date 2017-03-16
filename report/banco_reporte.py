# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import datetime

class banco_reporte(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(banco_reporte, self).__init__(cr, uid, name, context)
        self.totales = {'debito':0, 'credito':0}
        self.localcontext.update( {
            'datetime': datetime,
            'lineas': self.lineas,
            'balance_inicial': self.balance_inicial,
            'totales': self.totales,
        })
        self.lineas = None
        self.context = context
        self.cr = cr

    def lineas(self, datos):

        #
        # Solo ejecutar una vez este metodo
        #
        if self.lineas:
            return self.lineas

        lineas_id = self.pool.get('account.move.line').search(self.cr, self.uid, [('account_id','=',datos.cuenta_bancaria_id.id), ('date','>=',datos.fecha_desde), ('date','<=',datos.fecha_hasta)], order='date', context=self.context)

        lineas = []
        for linea in self.pool.get('account.move.line').browse(self.cr, self.uid, lineas_id, context=self.context):
            detalle = {
                'fecha-iso': linea.date,
                'fecha': datetime.datetime.strptime(linea.date, '%Y-%m-%d').strftime('%d%m%y'),
                'documento': linea.move_id.name if linea.move_id else '',
                'nombre': linea.partner_id.name or '',
                'concepto': (linea.ref if linea.ref else '')+linea.name,
                'debito': linea.debit,
                'credito': linea.credit,
                'balance': 0,
                'tipo': ''
            }

            if linea.amount_currency:
                if linea.amount_currency > 0:
                    detalle['debito'] = linea.amount_currency
                else:
                    detalle['credito'] = -1 * linea.amount_currency

            lineas.append(detalle)

        balance_inicial = self.balance_inicial(datos)
        if balance_inicial['balance_moneda']:
            balance = balance_inicial['balance_moneda']
        elif balance_inicial['balance']:
            balance = balance_inicial['balance']
        else:
            balance = 0

        for linea in lineas:

            balance = balance + linea['debito'] - linea['credito']
            linea['balance'] = balance

            self.totales['debito'] += linea['debito']
            self.totales['credito'] += linea['credito']

        self.lineas = lineas
        return self.lineas

    def balance_inicial(self, datos):
        self.cr.execute('select (sum(debit) - sum(credit)) as balance, sum(amount_currency) as balance_moneda from account_move_line where account_id = %s and date < %s', (datos.cuenta_bancaria_id.id, datos.fecha_desde))
        return self.cr.dictfetchall()[0]

report_sxw.report_sxw('report.banco_reporte', 'l10n_gt_extra.asistente_banco_reporte', 'addons/l10n_gt_extra/report/banco_reporte.rml', parser=banco_reporte, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
