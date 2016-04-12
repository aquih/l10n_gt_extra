# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import time
import datetime

class banco_reporte(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(banco_reporte, self).__init__(cr, uid, name, context)
        self.totales = {'debito':0, 'credito':0}
        self.localcontext.update( {
            'time': time,
            'datetime': datetime,
            'lineas': self.agrupar_lineas,
            'balance_final': self.balance_final,
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

        self.cr.execute('select id from account_move_line where account_id = %s and date between %s and %s and move_id in ( select id from account_move where date between %s and %s )', (datos.cuenta_bancaria_id.id, datos.fecha_desde, datos.fecha_hasta, datos.fecha_desde, datos.fecha_hasta))
        lineas_id = [x[0] for x in self.cr.fetchall()]

        lineas = []

        for linea_id in lineas_id:

            linea = self.pool.get('account.move.line').browse(self.cr, self.uid, linea_id)

            detalle = {'fecha-iso':linea.date, 'fecha':datetime.datetime.strptime(linea.date, '%Y-%m-%d').strftime('%d%m%y'), 'documento':  linea.move_id.name if linea.move_id else '', 'nombre':linea.partner_id.name or '', 'concepto':(linea.ref if linea.ref else '')+linea.name, 'debito':linea.debit, 'credito':linea.credit, 'tipo':''}

            lineas.append(detalle)

        lineas.sort(reverse=True, key=lambda x:x['fecha-iso']+x['documento'])

        #
        # El balance de cada linea, el total de cheque y agregarle partida, si
        # es necesaria.
        #
        balance = self.balance_final(datos)['balance']
        for i in range(len(lineas)):

            if i > 0:
                balance = lineas[i-1]['balance'] + (-lineas[i-1]['debito'] + lineas[i-1]['credito'])
            lineas[i]['balance'] = balance


        #
        # Calcular los totales solo una vez.
        #
        for linea in lineas:
            self.totales['debito'] += linea['debito']
            self.totales['credito'] += linea['credito']

        lineas.sort(key=lambda x:x['fecha-iso']+x['documento'])
        self.lineas = lineas

        return self.lineas

    def balance_final(self, datos):
        ctx = self.context.copy()

        ctx['fiscalyear'] = ','.join([str(x.id) for x in datos.ejercicios_fiscales])
        ctx['date_from'] = '2000-01-01'
        ctx['date_to'] = datos.fecha_hasta

        cuenta = self.pool.get('account.account').read(self.cr, self.uid, datos.cuenta_bancaria_id.id, ['type','code','name','debit','credit','balance','parent_id'], ctx)

        return cuenta

report_sxw.report_sxw('report.banco_reporte', 'l10n_gt_extra.asistente_banco_reporte', 'addons/l10n_gt_extra/report/banco_reporte.rml', parser=banco_reporte, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
