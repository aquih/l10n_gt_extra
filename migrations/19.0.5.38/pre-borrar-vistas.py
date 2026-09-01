import logging
from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    util.records.remove_view(cr, xml_id="l10n_gt_extra.asistente_reporte_banco")
    util.records.remove_record(cr, "l10n_gt_extra.window_reporte_banco")
    util.records.remove_record(cr, "l10n_gt_extra.action_reporte_banco")
    util.records.remove_record(cr, "l10n_gt_extra.menu_asistente_reporte_banco")

    util.records.remove_view(cr, xml_id="l10n_gt_extra.asistente_compras_reporte")
    util.records.remove_record(cr, "l10n_gt_extra.window_reporte_compras")
    util.records.remove_record(cr, "l10n_gt_extra.action_reporte_compras")
    util.records.remove_record(cr, "l10n_gt_extra.menu_asistente_reporte_compras")

    util.records.remove_view(cr, xml_id="l10n_gt_extra.asistente_reporte_diario")
    util.records.remove_record(cr, "l10n_gt_extra.window_reporte_diario")
    util.records.remove_record(cr, "l10n_gt_extra.action_reporte_diario")
    util.records.remove_record(cr, "l10n_gt_extra.menu_asistente_reporte_diario")

    util.records.remove_view(cr, xml_id="l10n_gt_extra.asistente_reporte_inventario")
    util.records.remove_record(cr, "l10n_gt_extra.window_reporte_inventario")
    util.records.remove_record(cr, "l10n_gt_extra.action_reporte_inventario")
    util.records.remove_record(cr, "l10n_gt_extra.menu_asistente_reporte_inventario")

    util.records.remove_view(cr, xml_id="l10n_gt_extra.asistente_reporte_mayor")
    util.records.remove_record(cr, "l10n_gt_extra.window_reporte_mayor")
    util.records.remove_record(cr, "l10n_gt_extra.action_reporte_mayor")
    util.records.remove_record(cr, "l10n_gt_extra.menu_asistente_reporte_mayor")
    
    util.records.remove_view(cr, xml_id="l10n_gt_extra.asistente_ventas_reporte")
    util.records.remove_record(cr, "l10n_gt_extra.window_reporte_ventas")
    util.records.remove_record(cr, "l10n_gt_extra.action_reporte_ventas")
    util.records.remove_record(cr, "l10n_gt_extra.menu_asistente_reporte_ventas")
    _logger.info("Vistas viejas borradas")
