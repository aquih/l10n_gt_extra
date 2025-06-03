import logging
from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    util.records.remove_view(cr, xml_id="l10n_gt_extra.l10n_gt_view_move_form")
    util.records.remove_view(cr, xml_id="l10n_gt_extra.l10n_gt_view_account_payment_form")
    util.records.remove_view(cr, xml_id="l10n_gt_extra.l10n_gt_view_account_journal_form")
    util.records.remove_view(cr, xml_id="l10n_gt_extra.product_template_form_view")
    util.records.remove_view(cr, xml_id="l10n_gt_extra.l10n_gt_extra_product_variant_easy_edit_view")
    util.records.remove_view(cr, xml_id="l10n_gt_extra.l10n_gt_view_res_partner_form")
    util.records.remove_view(cr, xml_id="l10n_gt_extra.l10n_gt_view_partner_form")
    util.records.remove_view(cr, xml_id="l10n_gt_extra.l10n_gt_extra_product_template_tree_view")
    _logger.info("Vistas viejas borradas")
