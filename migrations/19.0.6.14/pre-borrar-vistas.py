import logging
from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    util.records.remove_view(cr, xml_id="l10n_gt_extra.view_company_form")
    _logger.info("Vistas viejas borradas")
