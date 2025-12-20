# -*- coding: utf-8 -*-
################################################################################
#
#    Skylabs Company.
#    Copyright (C) 2025-TODAY SkyLabs Company(<https://www.skylabs.app>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.skylabs.app>.
#
################################################################################
from datetime import datetime, time
import pytz
from odoo import fields, models

"""Models for salon booking and related helpers."""


class SalonBooking(models.Model):
    """Creates 'salon booking' to create salon bookings"""
    _name = 'salon.booking'
    _description = 'Salon Booking'

    name = fields.Char(string="Name", required=True, help="Name of customer")
    state = fields.Selection(string="State", default="draft",
                             selection=[('draft', 'Draft'),
                                        ('approved', 'Approved'),
                                        ('rejected', 'Rejected')],
                             help="State of the booking")
    time = fields.Datetime(string="Date", required=True,
                           help="Start time of the order")
    phone = fields.Char(string="Phone", help="Phone number of customer.")
    email = fields.Char(string="E-Mail", help="Email of employee")
    service_ids = fields.Many2many(comodel_name='salon.service',
                                   string="Services",
                                   help="Salon services")
    chair_id = fields.Many2one('salon.chair', string="Chair",
                               required=True, help="Select the chair for "
                                                   "booking")
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="Default company")
    language_id = fields.Many2one(comodel_name='res.lang', string='Language',
                                  default=lambda self: self.env[
                                      'res.lang'].browse(1),
                                  help="Default language")
    filtered_order_ids = fields.Many2many(comodel_name='salon.order',
                                          string="Salon Orders",
                                          compute="_compute_filtered_order_ids",
                                          help="Orders for each salon")

    def _compute_filtered_order_ids(self):
        """Computes the filtered_order_ids field"""
        for rec in self:
            # determine date in user's timezone
            if rec.time:
                local_dt = fields.Datetime.context_timestamp(rec, rec.time)
                date_only = local_dt.date()
            else:
                date_only = fields.Date.context_today(rec)

            user_tz = pytz.timezone(rec.env.user.tz or 'UTC')
            local_start = user_tz.localize(datetime.combine(date_only, time(0, 0, 0)))
            local_end = user_tz.localize(datetime.combine(date_only, time(23, 59, 59)))
            date_start = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
            date_end = local_end.astimezone(pytz.UTC).replace(tzinfo=None)

            salon_orders = self.env['salon.order'].search([
                ('chair_id', '=', rec.chair_id.id),
                ('start_time', '>=', date_start),
                ('start_time', '<=', date_end),
            ])
            rec.filtered_order_ids = [(6, 0, salon_orders.ids)]

    def action_approve_booking(self):
        """Approve the booking for salon services"""
        salon_order = self.env['salon.order'].create(
                        {'customer_name': self.name,
                         'chair_id': self.chair_id.id,
                         'start_time': self.time,
                         'date': fields.Datetime.now(),
                         'stage_id': 1,
                         'booking_identifier': True})
        for service in self.service_ids:
            self.env['salon.order.line'].create({
                'service_id': service.id,
                'time_taken': service.time_taken,
                'price': service.price,
                'price_subtotal': service.price,
                'salon_order_id': salon_order.id,
            })

        lang = 'en_US'

        template = self.env.ref('sl_salon_management.mail_template_salon_approved')
        template.with_context(lang=lang)

        self.state = "approved"

    def action_reject_booking(self):
        """Reject booking for salon services"""
        self.env['mail.template'].browse(self.env.ref(
            'sl_salon_management.mail_template_salon_rejected')
                                         .id).send_mail(self.id,
                                                        force_send=True)
        self.state = "rejected"

    def get_booking_count(self):
        """Gets the count of salon bookings, recent works, salon orders, salon
            clients.
            Returns: Count of each one."""
        return {
            'bookings': self.env['salon.booking'].search_count(
                [('state', '=', 'approved')]),
            'sales': self.env['salon.order'].search_count(
                [('stage_id', 'in', [3, 4])]),
            'orders': self.env['salon.order'].search_count([]),
            'clients': self.env['res.partner'].search_count(
                [('partner_salon', '=', True)]),
            'chairs': self.env['salon.chair'].search([])
        }
