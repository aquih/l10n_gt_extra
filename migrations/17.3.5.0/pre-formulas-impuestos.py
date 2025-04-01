import logging
from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    def migrate(cr, version):
    cr.execute("update account_tax set formula = 'base/1.12 * 0.005', price_include_override = 'tax_excluded' where id in (select res_id from ir_model_data where name like '%impuestos_plantilla_timbre_prensa')")
    cr.execute("update account_tax set formula = '(base/1.12 > 30000) and (30000 * -0.05 + (base/1.12 - 30000) * -0.07) or base/1.12 * -0.05', price_include_override = 'tax_excluded' where id in (select res_id from ir_model_data where name like '%impuestos_plantilla_isr_retencion')")
    cr.execute("update account_tax set price_include_override = 'tax_included' where id in (select res_id from ir_model_data where name like '%impuestos_plantilla_idp_disel')")
    cr.execute("update account_tax set price_include_override = 'tax_included' where id in (select res_id from ir_model_data where name like '%impuestos_plantilla_idp_regular')")
    cr.execute("update account_tax set price_include_override = 'tax_included' where id in (select res_id from ir_model_data where name like '%impuestos_plantilla_idp_super')")
    cr.execute("update account_tax set price_include_override = 'tax_excluded' where id in (select res_id from ir_model_data where name like '%impuestos_plantilla_isr_factura_especial')")
    cr.execute("update account_tax set price_include_override = 'tax_excluded' where id in (select res_id from ir_model_data where name like '%impuestos_plantilla_iva_especial')")
    _logger.info("Formulas y precios incluidos de impuestos")
