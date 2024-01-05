from odoo import models
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('gt', 'account.tax')
    def _get_gt_extra_account_tax(self):
        additional = self._parse_csv('gt', 'account.tax', module='l10n_gt_extra')
        self._deref_account_tags('gt', additional)
        return additional