import logging
from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    util.remove_field(cr, 'l10n_gt_extra.impuestos', 'tipo')
    _logger.info("Campos borrados")