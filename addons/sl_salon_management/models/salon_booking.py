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
from datetime import datetime, time, timedelta
import logging
import pytz
from odoo import fields, models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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

    @staticmethod
    def _normalize_record_id(value):
        """Return a scalar id when given a record/dict/list/tuple payload."""
        if isinstance(value, dict):
            return value.get('id') or value.get('res_id')
        if isinstance(value, (list, tuple)) and value:
            first = value[0]
            return SalonBooking._normalize_record_id(first)
        if hasattr(value, 'id'):
            return value.id
        return value

    @api.constrains('time', 'chair_id', 'service_ids', 'state')
    def _check_booking_no_overlap(self):
        """Ensure a booking (draft or approved) does not overlap existing orders."""
        for rec in self:
            if not rec.time or rec.state == 'rejected':
                continue
            # compute total service time (in hours)
            total_hours = sum(s.time_taken for s in rec.service_ids) or 0.0
            try:
                end_dt = rec.time + timedelta(hours=float(total_hours))
            except Exception:
                end_dt = None
            if not end_dt:
                continue
            overlap_domain = [
                ('chair_id', '=', rec.chair_id.id),
                ('stage_id', 'not in', [4, 5]),
                ('start_time', '<', end_dt),
                '|',
                ('end_time', '>', rec.time),
                ('end_time', '=', False),
            ]
            approved_order_id = self.env.context.get('_approved_order_id')
            if approved_order_id:
                order_to_skip = approved_order_id.id if hasattr(approved_order_id, 'id') else approved_order_id
                overlap_domain.append(('id', '!=', order_to_skip))
            booking_id = rec.id if rec.id else False
            if booking_id:
                overlap_domain.append(('booking_id', '!=', booking_id))
            overlap = self.env['salon.order'].search(overlap_domain, limit=1)
            if overlap:
                raise ValidationError(
                    rec.env._(
                        "Selected time overlaps with existing order %(name)s"
                    ) % {'name': overlap.name}  # pylint: disable=translation-not-lazy
                )

    @classmethod
    def _extract_service_ids_from_vals(cls, vals):
        """Extract a list of service ids from vals['service_ids'] commands if present."""
        svc_ids = None
        cmds = vals.get('service_ids')
        if cmds:
            # handle common (6, 0, [ids]) command
            for cmd in cmds:
                if isinstance(cmd, (list, tuple)) and len(cmd) >= 3 and cmd[0] == 6:
                    svc_ids = list(cmd[2])
                    break
            # fallback: single id (4, id, _) or (4, id)
            if svc_ids is None:
                ids = []
                for cmd in cmds:
                    if isinstance(cmd, (list, tuple)) and len(cmd) >= 2 and cmd[0] == 4:
                        ids.append(cmd[1])
                if ids:
                    svc_ids = ids
        return svc_ids

    def _validate_overlap_vals(self, time_val, chair_id, service_ids, booking_id=None):
        """Validate overlap using provided values (time, chair, service ids)."""
        if not time_val or not chair_id:
            return
        chair_id = self._normalize_record_id(chair_id)
        if not chair_id:
            return
        total_hours = 0.0
        if service_ids is not None:
            services = self.env['salon.service'].browse(service_ids)
            total_hours = sum(s.time_taken for s in services) or 0.0
        else:
            # No service ids in vals: use minimal check (treat as existent zero-duration)
            total_hours = 0.0
        try:
            end_dt = time_val + timedelta(hours=float(total_hours))
        except Exception:
            end_dt = None
        overlap_domain = [
            ('chair_id', '=', chair_id),
            ('stage_id', 'not in', [4, 5]),
        ]
        normalized_booking_id = None
        if booking_id:
            normalized_booking_id = booking_id.id if hasattr(booking_id, 'id') else booking_id
            overlap_domain.append(('booking_id', '!=', normalized_booking_id))
        if not end_dt:
            # If we cannot compute an end, still check for any order that contains the start time
            overlap_domain += [
                ('start_time', '<=', time_val),
                ('end_time', '>=', time_val),
            ]
        else:
            overlap_domain += [
                ('start_time', '<', end_dt),
                '|',
                ('end_time', '>', time_val),
                ('end_time', '=', False),
            ]
        overlap = self.env['salon.order'].search(overlap_domain, limit=1)
        if overlap:
            raise ValidationError(
                self.env._("Selected time overlaps with existing order %(name)s") % {
                    'name': overlap.name}
            )

    @api.model_create_multi
    def create(self, vals_list):
        # validate each incoming vals dict before creating records
        for vals in vals_list:
            time_val = vals.get('time')
            chair_id = vals.get('chair_id') or vals.get('chair')
            svc_ids = self._extract_service_ids_from_vals(vals)
            # if time is a string, try parse to datetime via fields.Datetime
            if isinstance(time_val, str):
                try:
                    time_val = fields.Datetime.from_string(time_val)
                except Exception:
                    time_val = None
            normalized_chair = self._normalize_record_id(chair_id)
            if normalized_chair:
                vals['chair_id'] = normalized_chair
            if time_val and chair_id:
                self._validate_overlap_vals(time_val, normalized_chair, svc_ids)
        return super().create(vals_list)

    def write(self, vals):
        # validate each record with prospective values
        svc_ids = self._extract_service_ids_from_vals(vals)
        for rec in self:
            time_val = vals.get('time', rec.time)
            chair_id = vals.get('chair_id', rec.chair_id)
            # parse strings
            if isinstance(time_val, str):
                try:
                    time_val = fields.Datetime.from_string(time_val)
                except Exception:
                    time_val = rec.time
            # if service ids not provided in vals, keep existing services
            effective_svc_ids = svc_ids if svc_ids is not None else [s.id for s in rec.service_ids]
            normalized_chair = self._normalize_record_id(chair_id)
            if normalized_chair:
                vals['chair_id'] = normalized_chair
            self._validate_overlap_vals(time_val, normalized_chair, effective_svc_ids, booking_id=rec.id)
        return super().write(vals)

    def action_approve_booking(self):
        """Approve the booking for salon services"""
        lang = 'en_US'
        template = self.env.ref('sl_salon_management.mail_template_salon_approved')
        template.with_context(lang=lang)

        for rec in self:
            # compute total service time (in hours) and check for overlaps
            total_hours = sum(s.time_taken for s in rec.service_ids) or 0.0
            start_dt = rec.time
            if start_dt:
                try:
                    end_dt = start_dt + timedelta(hours=float(total_hours))
                except Exception:
                    end_dt = None
                if end_dt:
                    overlap = self.env['salon.order'].search([
                        ('chair_id', '=', rec.chair_id.id),
                        ('stage_id', 'not in', [4, 5]),
                        ('start_time', '<', end_dt),
                        '|',
                        ('end_time', '>', start_dt),
                        ('end_time', '=', False),
                    ], limit=1)
                    if overlap:
                        raise ValidationError(
                            rec.env._(
                                "Selected time overlaps with existing order %(name)s"
                            ) % {'name': overlap.name}  # pylint: disable=translation-not-lazy
                        )

                salon_order = self.env['salon.order'].create(
                                {'customer_name': rec.name,
                                 'chair_id': rec.chair_id.id,
                                 'start_time': rec.time,
                                 'date': fields.Datetime.now(),
                                     'stage_id': 1,
                                     'booking_identifier': True,
                                     'booking_id': rec.id})
            for service in rec.service_ids:
                self.env['salon.order.line'].create({
                    'service_id': service.id,
                    'time_taken': service.time_taken,
                    'price': service.price,
                    'price_subtotal': service.price,
                    'salon_order_id': salon_order.id,
                })
            rec.with_context(_approved_order_id=salon_order.id).state = "approved"

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

    @api.model
    def web_save(self, *args, **kwargs):
        """Endpoint used by website/web dataset to save booking data.

        Returns a structured dict on validation failure so callers can
        surface a user-friendly message instead of silently succeeding.
        """
        def _extract_payload(src_args, src_kwargs):
            payload = None
            source = None

            for key in ('values', 'specification'):
                if key in src_kwargs:
                    payload = src_kwargs[key]
                    source = f'kwargs[{key}]'
                    break

            if payload is None and len(src_args) >= 3 and isinstance(src_args[2], (list, tuple)):
                payload_args = src_args[2]
                payload_kwargs = src_args[3] if len(src_args) > 3 else {}
                if payload_args:
                    payload = payload_args[0]
                    source = 'call_kw args'
                else:
                    for key in ('values', 'specification'):
                        if key in payload_kwargs:
                            payload = payload_kwargs[key]
                            source = f'call_kw kwargs[{key}]'
                            break
                    if payload is None:
                        payload = payload_kwargs
                        source = 'call_kw kwargs fallback'

            if payload is None and src_args:
                for arg in src_args:
                    if isinstance(arg, (list, tuple, dict)):
                        payload = arg
                        source = 'positional'
                        break

            if payload is None:
                payload = src_kwargs or {}
                source = 'fallback kwargs'

            if isinstance(payload, (list, tuple)):
                dict_entries = [entry for entry in payload if isinstance(entry, dict)]
                if dict_entries:
                    payload = payload if all(isinstance(entry, dict) for entry in payload) else dict_entries

            return payload, source

        incoming, source_info = _extract_payload(args, kwargs)
        _logger.info('web_save called (source=%s) payload=%s; args=%s; kwargs=%s',
                     source_info, incoming, args, kwargs)
        try:
            if isinstance(incoming, list):
                # validate each dict and raise on overlap to surface error
                for vals in incoming:
                    time_val = vals.get('time')
                    chair_id = vals.get('chair_id') or vals.get('chair')
                    svc_ids = self._extract_service_ids_from_vals(vals)
                    if isinstance(time_val, str):
                        try:
                            time_val = fields.Datetime.from_string(time_val)
                        except Exception:
                            time_val = None
                    normalized_chair = self._normalize_record_id(chair_id)
                    if normalized_chair:
                        vals['chair_id'] = normalized_chair
                    if time_val and normalized_chair:
                        # explicitly search for overlap and log details
                        try:
                            self._validate_overlap_vals(time_val, normalized_chair, svc_ids)
                        except ValidationError as e:
                            _logger.warning('Overlap detected in web_save for chair %s at %s: %s', chair_id, time_val, e)
                            raise
                # all validated: create records
                recs = self.create(incoming)
                return {'result': True, 'ids': recs.ids}

            # single record path
            vals = incoming or {}
            time_val = vals.get('time')
            chair_id = vals.get('chair_id') or vals.get('chair')
            svc_ids = self._extract_service_ids_from_vals(vals)
            if isinstance(time_val, str):
                try:
                    time_val = fields.Datetime.from_string(time_val)
                except Exception:
                    time_val = None
            normalized_chair = self._normalize_record_id(chair_id)
            if normalized_chair:
                vals['chair_id'] = normalized_chair
            if time_val and normalized_chair:
                # explicitly search for overlap and log details
                try:
                    self._validate_overlap_vals(time_val, normalized_chair, svc_ids)
                except ValidationError as e:
                    _logger.warning('Overlap detected in web_save for chair %s at %s: %s', chair_id, time_val, e)
                    raise
            rec = self.create([vals])
            return {'result': True, 'ids': rec.ids}
        except ValidationError:
            # Let Odoo handle ValidationError -> RPC returns a proper error
            # message to the web client.
            raise
        except Exception as exc:  # pylint: disable=broad-except
            _logger.exception('Unexpected error in web_save: %s', exc)
            # For unexpected errors raise a ValidationError to surface in UI
            raise ValidationError(self.env._('Server error: %s') % (exc,))
