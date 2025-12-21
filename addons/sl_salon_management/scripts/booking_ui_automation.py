#!/usr/bin/env python3
"""Utility script that mimics the backend approval flow from the salon UI."""

from datetime import datetime, timedelta
import logging

import odoo
from odoo import api, SUPERUSER_ID, fields

_logger = logging.getLogger(__name__)

DSN = [
    "--config",
    "/etc/odoo/odoo.conf",
    "--db_host",
    "db",
    "--db_port",
    "5432",
    "--db_user",
    "odoo",
    "--db_password",
    "Y04wUp$HhT",
    "-d",
    "salonmodule",
]


def _setup_registry():
    odoo.tools.config.parse_config(DSN)
    return odoo.registry("salonmodule")


def _get_booking_vals(env):
    chair = env["salon.chair"].search([], limit=1)
    if not chair:
        raise RuntimeError("No chairs defined in salonmodule")
    service = env["salon.service"].search([], limit=1)
    if not service:
        raise RuntimeError("No services defined in salonmodule")

    start_time = fields.Datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=float(service.time_taken or 1))

    return {
        "name": f"Automation Booking {datetime.utcnow().isoformat()}",
        "time": fields.Datetime.to_string(start_time),
        "chair_id": chair.id,
        "service_ids": [(6, 0, [service.id])],
        "phone": "000000000",
        "email": "automation@example.com",
    }


def run():
    registry = _setup_registry()
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        booking_vals = _get_booking_vals(env)
        booking = env["salon.booking"].create(booking_vals)
        _logger.info("Created booking %s", booking.id)
        booking.action_approve_booking()
        _logger.info("Booking approved state=%s", booking.state)
        order = env["salon.order"].search([("booking_id", "=", booking.id)], limit=1)
        if not order:
            raise RuntimeError("Approval did not create an order")
        _logger.info("Created order %s linked to booking", order.name)
        cr.rollback()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run()
