from odoo import fields, models

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'The real estate type'
    _order = "sequence,name"
    _sql_constraints = [
        ('check_name','UNIQUE(name)','The Type Name must be unique.'),
    ]

    # Basic fields
    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order listings")
    description = fields.Text(string='Description')

    # Relational fields (for the inline view)
    property_ids = fields.One2many("estate.property", "property_type_id", strings="Types")

    # Computed (for stat button)
    offer_count = fields.Integer(string="Offers Count", compute="_compute_offer")
    offer_ids = fields.Many2many("estate.property.offer", string="Offers", compute="_compute_offer")

    # -- Compute methods --
    def _compute_offer(self):
        # I believe this exercise was at or after where I gave up in Chapter 12 due to time constraints
        # Here is the complex solution from the solutions repo
        data = self.env["estate.property.offer"].read_group(
            [
                ("property_id.state", "!=", "canceled"),
                ("property_type_id", "!=", False)
            ],
            [
                "ids:array_agg(id)", "property_type_id"
            ],
            [
                "property_type_id"
            ]
        )
        mapped_count = {d["property_type_id"][0]: d["property_type_id_count"] for d in data}
        mapped_ids = {d["property_type_id"][0]: d["ids"] for d in data}
        for prop_type in self:
            prop_type.offer_count = mapped_count.get(prop_type.id, 0)
            prop_type.offer_ids = mapped_ids.get(prop_type.id, [])

    # -- Action Methods --
    def action_view_offers(self):
        res = self.env.ref("estate.estate_property_offer_action").read()[0]
        res["domain"] = [("id", "in", self.offer_ids.ids)]
        return res
