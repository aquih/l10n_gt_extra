# -*- encoding: utf-8 -*-

from openerp.report import report_sxw
import time
import datetime

class partida(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(partida, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'datetime': datetime,
            'lineas': self.lineas,
            'totales': self.totales,
        }),
        self.totales = {'debito':0, 'credito':0}
        self.context = context
        self.cr = cr

    def lineas(self, datos):
        for l in datos.line_id:
            self.totales['debito'] += l.debit
            self.totales['credito'] += l.credit
        return sorted(datos.line_id, key=lambda x: x.debit, reverse=True)

    def totales(self):
        return self.totales

report_sxw.report_sxw('report.partida', 'account.move', 'addons/l10n_gt_extra/report/partida.rml', parser=partida, header=False)
