# -*- encoding: utf-8 -*-

from . import models
from . import report
import logging

def _update_gt_taxes(env):
    env['res.company'].update_gt_taxes()