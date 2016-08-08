# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import datetime

class banco_reporte(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(banco_reporte, self).__init__(cr, uid, name, context)
        self.totales = {'debito':0, 'credito':0}
        self.localcontext.update( {
            'datetime': datetime,
            'lineas': self.agrupar_lineas,
            'balance_inicial': self.balance_inicial,
            'totales': self.totales,
        })
        self.lineas = None
        self.context = context
        self.cr = cr

    def agrupar_lineas(self, datos):
        #
        # Solo ejecutar una vez este metodo
        #
        if self.lineas:
            return self.lineas

        self.cr.execute('select id from account_move_line where account_id = %s and date between %s and %s', (datos.cuenta_bancaria_id.id, datos.fecha_desde, datos.fecha_hasta))
        lineas_id = [x[0] for x in self.cr.fetchall()]

        lineas = []
        for linea in self.pool.get('account.move.line').browse(self.cr, self.uid, lineas_id):
            detalle = {
                'fecha-iso': linea.date,
                'fecha': datetime.datetime.strptime(linea.date, '%Y-%m-%d').strftime('%d%m%y'),
                'documento': linea.move_id.name if linea.move_id else '',
                'nombre': linea.partner_id.name or '',
                'concepto': (linea.ref if linea.ref else '')+linea.name,
                'debito': linea.debit,
                'credito': linea.credit,
                'tipo': ''
            }

            lineas.append(detalle)

        balance = self.balance_inicial(datos)['balance']
        for linea in lineas:

            balance = linea['balance'] + linea['debito'] - linea['credito']
            linea['balance'] = balance

            self.totales['debito'] += linea['debito']
            self.totales['credito'] += linea['credito']

        self.lineas = lineas
        return self.lineas

    def balance_inicial(self, datos):
        self.cr.execute('select (sum(debit) - sum(credit)) as balance from account_move_line where account_id = %s and date < %s', (datos.cuenta_bancaria_id.id, datos.fecha_desde))
        return self.cr.dictfetchall()[0]

report_sxw.report_sxw('report.banco_reporte', 'l10n_gt_extra.asistente_banco_reporte', 'addons/l10n_gt_extra/report/banco_reporte.rml', parser=banco_reporte, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
