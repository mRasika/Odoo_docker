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
"""Website controllers for SL Salon Management addon."""

import json
from datetime import datetime, time, timedelta
import pytz
from odoo import fields, http
from odoo.http import request


class SalonBookingWeb(http.Controller):
    """Route to do salon website operations."""

    @http.route(route='/page/salon_details', type='json', auth='public',
                website=True, csrf=False)
    def salon_details(self, **kwargs):
        name = kwargs.get('name')
        date = kwargs.get('date')
        salon_time = kwargs.get('salon_time')
        phone = kwargs.get('phone')
        email = kwargs.get('email')
        chair = kwargs.get('chair')
        number = kwargs.get('number')
        list_service = kwargs.get('list_service') or []
        # normalize ids that may come as strings from the form
        try:
            chair = int(chair) if chair is not None else None
        except Exception:
            chair = None
        service_lists = []
        for service in list_service:
            try:
                service_lists.append(int(service.get('item')))
            except Exception:
                pass
        dates_time = (date or '') + " " + (salon_time or '') + ":00"
        user_tz = request.env.user.tz or 'UTC'
        if isinstance(user_tz, bool):
            user_tz = 'UTC'
        local_tz = pytz.timezone(user_tz)
        date_and_time = (local_tz.localize(
            datetime.strptime(str(dates_time), '%Y-%m-%d %H:%M:%S')).
                         astimezone(pytz.UTC).replace(tzinfo=None))
        # compute total service time (hours) for requested services
        services = request.env['salon.service'].search([('id', 'in', service_lists)]) if service_lists else request.env['salon.service'].browse([])
        total_hours = sum(s.time_taken for s in services) or 0.0
        try:
            requested_end = date_and_time + timedelta(hours=float(total_hours))
        except Exception:
            requested_end = None

        # check overlap with existing salon.order (active stages)
        if requested_end and chair:
            conflicting_order = request.env['salon.order'].search([
                ('chair_id', '=', chair),
                ('stage_id', 'not in', [4, 5]),
                ('start_time', '<', requested_end),
            ], limit=10)
            for o in conflicting_order:
                # compute other end time
                if o.end_time:
                    other_end = o.end_time
                else:
                    try:
                        other_end = o.start_time + timedelta(hours=float(o.time_taken_total or 0.0))
                    except Exception:
                        other_end = o.start_time
                if o.start_time and (date_and_time < other_end and requested_end > o.start_time):
                    return json.dumps({'result': False, 'error': 'Selected time conflicts with an existing order.'})

            # check overlap with existing bookings (non-rejected)
            candidate_bookings = request.env['salon.booking'].search([
                ('chair_id', '=', chair),
                ('state', '!=', 'rejected'),
            ])
            for b in candidate_bookings:
                if not b.time:
                    continue
                b_services = b.service_ids
                b_total = sum(s.time_taken for s in b_services) or 0.0
                try:
                    b_end = b.time + timedelta(hours=float(b_total))
                except Exception:
                    b_end = b.time
                if date_and_time < b_end and (requested_end or date_and_time) > b.time:
                    return json.dumps({'result': False, 'error': 'Selected time conflicts with an existing booking.'})

        a = request.env['salon.booking'].create({
            'name': name,
            'phone': phone,
            'time': date_and_time,
            'email': email,
            'chair_id': chair,
            'service_ids': [(6, 0, service_lists or [salon.id for salon in services])],
        })

        return json.dumps({'result': True})

    @http.route('/page/salon_check_date', type='json', auth="public",
                website=True)
    def salon_check(self, **kwargs):
        year, month, day = map(int, kwargs['check_date'].split('-'))
        user_tz = request.env.user.tz or 'UTC'
        if isinstance(user_tz, bool):
            user_tz = 'UTC'  # Ensure it's a string
        local_tz = pytz.timezone(user_tz)
        date_start = local_tz.localize(
            datetime(year, month, day, hour=0, minute=0, second=0)).astimezone(
            pytz.UTC).replace(tzinfo=None)
        date_end = (local_tz.
                    localize(datetime(year, month, day, hour=23, minute=59,
                                      second=59)).astimezone(pytz.UTC).
                    replace(tzinfo=None))
        order_obj = request.env['salon.order'].search(
            [('chair_id.active_booking_chairs', '=', True),
             ('stage_id', 'in', [1, 2, 3]), ('start_time', '>=', date_start),
             ('start_time', '<=', date_end)])
        order_details = {}
        for order in order_obj:
            data = {
                'number': order.id,
                'start_time_only': fields.Datetime.to_string(pytz.UTC.localize(
                    order.start_time).astimezone(local_tz).replace(tzinfo=None))[11:16],
                'end_time_only': fields.Datetime.to_string(pytz.UTC.localize(
                    order.end_time).astimezone(local_tz).replace(tzinfo=None))[11:16],
            }
            if order.chair_id.id not in order_details:
                order_details[order.chair_id.id] = {
                    'name': order.chair_id.name,
                    'orders': [data],
                }
            else:
                order_details[order.chair_id.id]['orders'].append(data)
        return order_details

    @http.route('/page/sl_salon_management/salon_booking_thank_you',
                type='http', auth="public", website=True, csrf=False)
    def return_thank_you(self, **post):
        return request.render('sl_salon_management.salon_booking_thank_you', {})

    @http.route('/salon_booking_form', type='http',
                auth="public", website=True)
    def chair_info(self, **post):
        """Route function that render while clicking Booking menu from website.
           Returns data to booking website"""
        salon_service_obj = request.env['salon.service'].search([])
        salon_working_hours_obj = request.env['salon.working.hours'].search([])
        salon_holiday_obj = request.env['salon.holiday'].search(
            [('holiday', '=', True)])
        date_check = datetime.today().date()
        user_tz = request.env.user.tz or 'UTC'
        if isinstance(user_tz, bool):
            user_tz = 'UTC'  # Ensure it's a string
        local_tz = pytz.timezone(user_tz)
        date_start = local_tz.localize(datetime.combine(date_check, time(hour=0, minute=0, second=0))).astimezone(
            pytz.UTC).replace(tzinfo=None)
        date_end = (local_tz.localize(
            datetime.combine(date_check, time(hour=23, minute=59, second=59))).
                    astimezone(pytz.UTC).replace(tzinfo=None))
        # chair_obj =
        order_obj = request.env['salon.order'].search(
            [('chair_id.active_booking_chairs', '=', True),
             ('stage_id', 'in', [1, 2, 3]), ('start_time', '>=', date_start),
             ('start_time', '<=', date_end)])
        return request.render(
            'sl_salon_management.salon_booking_form', {
                'chair_details': request.env['salon.chair'].search([]),
                'order_details': order_obj,
                'salon_services': salon_service_obj,
                'date_search': date_check,
                'holiday': salon_holiday_obj,
                'working_time': salon_working_hours_obj}
        )


class SalonOrders(http.Controller):
    """Returns the chairs for dashboard"""

    @http.route(route='/salon/chairs', type="json", auth="public")
    def get_salon_chair(self, products_per_slide=3):
        """Function to returns the chairs for dashboard"""
        chairs = []
        number_of_orders = {}
        for chair in request.env['salon.chair'].sudo().search([]):
            number_of_orders.update({
                chair.id: len(request.env['salon.order'].search(
                    [("chair_id", "=", chair.id),
                     ("stage_id", "in", [2, 3])]))})
            chairs.append({'name': chair.name,
                           'id': chair.id,
                           'orders': number_of_orders[chair.id]})
        return chairs
