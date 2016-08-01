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
        diarios = {}

        for diario in datos.diarios_id:

            diarios[diario.id] = {'diario': diario.name, 'lineas': []}

            self.cr.execute("\
                select l.period_id as number, l.ref as descr, j.code as doc, l.date, a.code, a.name, a.code||' '||a.name as full_name, l.debit as debit, l.credit as credit \
                from account_move_line l join account_move m on(l.move_id = m.id) \
                    join account_account a on(l.account_id = a.id) \
                    join account_journal j on(l.journal_id = j.id) \
                where m.state = 'posted' and l.journal_id = "+str(diario.id)+" and l.period_id in ("+periodos_id+") \
                order by l.date, a.code")

            lineas = self.cr.dictfetchall()
            lineas_agrupadas = {}

            llave = 'date'
            if datos.tipo == 'mayor':
                llave = 'full_name'

            for l in lineas:

                if l[llave] not in lineas_agrupadas:
                    lineas_agrupadas[l[llave]] = {'llave': l[llave], 'lineas_detalladas': [], 'total_debe': 0, 'total_haber': 0}
                lineas_agrupadas[l[llave]]['lineas_detalladas'].append(l)

            for la in lineas_agrupadas.values():
                for l in la['lineas_detalladas']:
                    la['total_debe'] += l['debit']
                    la['total_haber'] += l['credit']

            diarios[diario.id]['lineas'] = sorted(lineas_agrupadas.values(), key=lambda x: x['llave'])

        for diario in datos.diarios_resumidos_id:

            diarios[diario.id] = {'diario': diario.name, 'lineas': []}

            self.cr.execute("\
                select l.period_id as number, j.name as descr, j.code as doc, l.date, a.code, a.name, a.code||' '||a.name as full_name, sum(l.debit) as debit, sum(l.credit) as credit \
                from account_move_line l join account_move m on(l.move_id = m.id) \
                    join account_account a on(l.account_id = a.id) \
                    join account_journal j on(l.journal_id = j.id) \
                where m.state = 'posted' and l.journal_id = "+str(diario.id)+" and l.period_id in ("+periodos_id+")\
                group by l.period_id, j.name, j.code, l.date, a.code, a.name order by l.date, a.code")

            lineas = self.cr.dictfetchall()
            lineas_agrupadas = {}

            llave = 'date'
            if datos.tipo == 'mayor':
                llave = 'full_name'

            for l in lineas:

                if l[llave] not in lineas_agrupadas:
                    lineas_agrupadas[l[llave]] = {'llave': l[llave], 'lineas_detalladas': [], 'total_debe': 0, 'total_haber': 0}
                lineas_agrupadas[l[llave]]['lineas_detalladas'].append(l)

            for la in lineas_agrupadas.values():
                for l in la['lineas_detalladas']:
                    la['total_debe'] += l['debit']
                    la['total_haber'] += l['credit']

            diarios[diario.id]['lineas'] = sorted(lineas_agrupadas.values(), key=lambda x: x['llave'])

        return diarios.values()

    def totales(self):
        return self.totales

report_sxw.report_sxw('report.diario_reporte', 'l10n_gt_extra.asistente_diario_reporte', 'addons/l10n_gt_extra/report/diario_reporte.rml', parser=diario_reporte, header=False)
