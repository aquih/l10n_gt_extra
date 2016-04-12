# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import datetime
import logging

class diario_reporte(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(diario_reporte, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'datetime': datetime,
            'lineas': self.lineas,
            'folio': self.folio,
        }),
        self.folioActual = -1
        self.context = context
        self.cr = cr

    def folio(self, datos):

        if self.folioActual < 0:
            if datos[0].folio_inicial <= 0:
                self.folioActual = 1
            else:
                self.folioActual = datos[0].folio_inicial
        else:
            self.folioActual += 1

        return self.folioActual

    def lineas(self, datos):
        periodos_id = ','.join([str(x.id) for x in datos.periodos_id])
        diarios_id = ','.join([str(x.id) for x in datos.diarios_id])
        self.cr.execute("\
            select l.date, a.code, a.name, sum(l.debit) as debit, sum(l.credit) as credit \
            from account_move_line l join account_move m on(l.move_id = m.id) \
                join account_account a on(l.account_id = a.id) \
            where m.state = 'posted' and l.journal_id in ("+diarios_id+") and l.period_id in ("+periodos_id+")\
            group by l.date, a.code, a.name order by l.date, a.code")

        lineas = self.cr.dictfetchall()
        lineas_fecha = {}

        for l in lineas:
            if l['date'] not in lineas_fecha:
                lineas_fecha[l['date']] = {'fecha': l['date'], 'lineas': []}

            l['inicial'] = 0
            l['final'] = l['inicial']+l['debit']-l['credit']

            lineas_fecha[l['date']]['lineas'].append(l)

        return lineas_fecha.values()

    def totales(self):
        return self.totales

report_sxw.report_sxw('report.diario_reporte', 'l10n_gt_extra.asistente_diario_reporte', 'addons/l10n_gt_extra/report/diario_reporte.rml', parser=diario_reporte, header=False)
