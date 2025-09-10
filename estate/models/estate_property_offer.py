from odoo import api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Offers"
    _order = "price desc"
    _sql_constraints = [
        ("check_price", "CHECK(price > 0)", "The price must be strictly positive")
    ]

    # Basic fields
    price = fields.Float(string="Price")
    validity = fields.Integer(default=7)
    create_date = fields.Date(default=fields.Date.today(), readonly=True)

    # Special fields
    state = fields.Selection([('accepted', 'Accepted',), ('refused', 'Refused',)], string='Status', copy=False)

    # Relational fields
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    property_id = fields.Many2one('estate.property', string='Property', required=True)

    # For the stat button:
    property_type_id = fields.Many2one(
        "estate.property.type", related="property_id.property_type_id", string="Property Type", store=True
    )

    # Computed fields
    date_deadline = fields.Date(string="Deadline", compute="_compute_date_deadline", inverse="_inverse_date_deadline")

    # -- Compute methods --
    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for record in self:
            date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = date + relativedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            date = record.create_date.date() if record.create_date else fields.Date.today()
            record.validity = (record.date_deadline - date).days

    # -- CRUD methods --
    
    # Devstral-2507 adapted this one from the technical-training-solutions
    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if values.get("property_id") and values.get("price"):
                prop = self.env["estate.property"].browse(values["property_id"])
                if prop.offer_ids:
                    max_offer = max(prop.mapped("offer_ids.price"))
                    if float_compare(values["price"], max_offer, precision_rounding=0.01) <= 0:
                        raise UserError("The offer must be higher than %.2f" % max_offer)
                prop.state = "offer_received"
        return super().create(values_list)

    # -- Action Methods --
    def action_accept(self):
        if "accepted" in self.mapped("property_id.offer_ids.state"):
            raise UserError("An offer has already been accepted.")
        self.write(
            {
                "state": "accepted"
            }
        )
        return self.mapped("property_id").write(
            {
                "state": "offer_accepted",
                "selling_price": self.price,
                "buyer_id": self.partner_id.id
            }
        )

    def action_refuse(self):
        return self.write(
            {
                "state": "refused"
            }
        )

#    def _action_offer(self, new_status):
#        if new_status == 'accepted':
#            self.ensure_one() # Do not allow more than one record to flow down this path
#            if int(self.estate_property.state) < 3: # This is our first hint that the property is SOLD, an Offer was ACCEPTED
#                self.status = new_status
#                self.estate_property.selling_price = self.price
#                self.estate_property.state = '3'
#                self.estate_property.buyer = self.partner
#            elif int(self.estate_property.state) == 3: # The SOLD button was pressed in the Form View, so no buyer is associated yet
#                if not self.estate_property.buyer:
#                    self.status = new_status
#                    self.estate_property.selling_price = self.price
#                    self.estate_property.state = '3'
#                    self.estate_property.buyer = self.partner    
#                else:
#                    raise UserError(f"The buyer is already {self.estate_property.buyer}")
#            else:
#                raise UserError("The property has already been SOLD.")
#        elif new_status == 'refused':
#            for record in self: # Allow the bulk refusal of records
#                if record.status != 'accepted':
#                    record.status = new_status
#
