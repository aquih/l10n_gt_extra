# -*- encoding: utf-8 -*-

from . import models
from . import report

def _update_gt_taxes(env):
    for company in env['res.company'].search([('chart_template', '=', 'gt')]):
        company.update_gt_taxes()
