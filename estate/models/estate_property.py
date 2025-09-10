from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError

from dateutil.relativedelta import relativedelta

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "A real estate property"
    _order = "id desc"
    _sql_constraints = [
        ('positive_prices_only', 'CHECK(selling_price >= 0 AND expected_price >= 0)', 'All prices must be non-negative real numbers.',),
        ('positive_integers_only', 'CHECK(garden_area >= 0 AND bedrooms >= 0 AND living_area >= 0 AND facades >= 0)', 'All numbers must be non-negative integers.',)
    ]

    # Methods used to return default values
    def _default_date_availability(self):
        return fields.Date.context_today(self) + relativedelta(months=3)
    
    # Basic
    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(string="Active", default=True)
    postcode = fields.Char()
    date_availability = fields.Date(string="Date Availability", copy=False, default=(lambda self: self._default_date_availability()))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float()
    bedrooms = fields.Integer(String='Bedrooms', default=1)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        string='Garden Direction',
        selection=[
            ('north', 'North',), 
            ('south', 'South',),
            ('east', 'East',),
            ('west', 'West',),
        ],
        help="The orientation of the garden."
    )
    state = fields.Selection(
        string='Lifecycle status',
        selection=[
            ('new', 'New',),
            ('offer_received', 'Offer Received',),
            ('offer_accepted', 'Offer Accepted',),
            ('sold', 'Sold',),
            ('canceled', 'Cancelled',),
        ],
        help="The lifecycle status of this object.",
        default='new',
        required=True,
        copy=False
    )

    # Relational Fields
    property_type_id = fields.Many2one("estate.property.type", string="Type")
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    buyer_id = fields.Many2one('res.partner', string='Buyer', readonly=True, copy=False)
    tag_ids = fields.Many2many("estate.property.tag", strings="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")

    # Computed Fields
    total_area = fields.Integer("Total Area", compute="_compute_total_area", help="Total area is computed by summing the living area and the garden area")
    best_price = fields.Float("Best Offer", compute="_compute_best_price", help="Best offer received")

    # -- Computed methods --
    @api.depends("garden_area", "living_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            the_set = record.offer_ids.mapped('price')
            if len(the_set) > 0:
                record.best_price = max(the_set)
            else:
                record.best_price = 0.0

    # -- Constraints and Onchanges
    @api.onchange("garden")
    def _onchange_garden(self):
        for record in self:
            if record.garden:
                record.garden_area = 10
                record.garden_orientation = 'north'
            else:
                record.garden_area = None # Should these really be (0, False) instead?
                record.garden_orientation = None
                return {
                    'warning': {
                        'title': "Warning (\"Jim Says\")",
                        'message': "None set for .garden_orientation"
                    }
                }
    
    @api.constrains("expected_price", "selling_price")
    def _check_price_difference(self):
        for record in self:
            if (
                not float_is_zero(record.selling_price, precision_rounding=0.01)
                and float_compare(record.selling_price, record.expected_price * 90.0 / 100.0, precision_rounding=0.01) < 0
            ):
                raise ValidationError("The selling price must be at least ninety percent of the expected price! What is this, a charity?")

    # -- CRUD methods --
    def unlink(self):
        if not set(self.mapped("state")) <= {"new", "cancelled"}:
            raise UserError("Only new and canceled properties may be deleted.")
        return super().unlink()

    # -- Action Methods --
    def action_sold(self):
        if 'canceled' in self.mapped('state'):
            raise UserError('Canceled properties may not be sold.')
        return self.write({'state': 'sold'})
    
    def action_cancel(self):
        if 'sold' in self.mapped('state'):
            raise UserError('Sold properties may not be cancelled.')
        return self.write({'state': 'canceled'})
