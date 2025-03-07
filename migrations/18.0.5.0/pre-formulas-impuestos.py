import logging
from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    def migrate(cr, version):
    cr.execute("update account_tax set python_compute = 'base * 0.005' where id in (select res_id from ir_model_data where name = '1_impuestos_plantilla_timbre_prensa')")
    cr.execute("update account_tax set python_compute = '(base > 30000) and (30000 * -0.05 + (base - 30000) * -0.07) or base * -0.05' where id in (select res_id from ir_model_data where name = '1_impuestos_plantilla_isr_retencion')")
    _logger.info("Formulas de impuestos")