# -*- coding: utf-8 -*-
"""Tests covering the salon booking web_save entry point."""
from odoo import fields
from odoo.tests.common import TransactionCase


class TestSalonBookingWebSave(TransactionCase):
    """Ensure web_save selects the correct payload and normalizes chair ids."""

    def setUp(self):
        super().setUp()
        self.chair = self.env['salon.chair'].create({'name': 'Payload Chair'})
        self.service = self.env['salon.service'].create({
            'name': 'Payload Service',
            'currency_id': self.env.company.currency_id.id,
            'price': 42.0,
            'time_taken': 1.0,
        })

    def test_web_save_prefers_positional_payload(self):
        """web_save should use the booking dict passed in positional args."""
        booking_vals = {
            'name': 'Web Save Payload Booking',
            # pass chair as a dict to ensure normalization still works
            'chair_id': {'res_id': self.chair.id},
            'time': fields.Datetime.now(),
            'service_ids': [(6, 0, [self.service.id])],
        }
        metadata = {
            'state': {},
            'name': {},
            'phone': {},
            'service_ids': {'fields': {'display_name': {}}},
            'time': {},
            'email': {},
            'chair_id': {'fields': {'display_name': {}}},
            'language_id': {'fields': {}},
            'company_id': {'fields': {}},
        }
        result = self.env['salon.booking'].web_save(
            [],
            booking_vals,
            specification=metadata,
        )
        self.assertTrue(result.get('result'), 'web_save reported failure')
        booking = self.env['salon.booking'].browse(result['ids'])
        self.assertEqual(booking.chair_id, self.chair)
        self.assertEqual(booking.service_ids.ids, [self.service.id])
        self.assertEqual(booking.name, booking_vals['name'])
