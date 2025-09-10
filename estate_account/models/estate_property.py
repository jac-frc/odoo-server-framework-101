from odoo import models

class EstateProperty(models.Model):
    _inherit = "estate.property"

    # -- Action methods --
    def action_sold(self):
        res = super().action_sold()
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        for record in self:
            self.env["account.move"].create(
                {
                    "partner_id": record.buyer_id.id,
                    "move_type": "out_invoice",
                    "journal_id": journal.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": prop.name,
                                "quantity": 1,
                                "price_unit": prop.selling_price * 6.0 / 100,
                            }
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Administrative costs",
                                "quantity": 1,
                                "price_unit": 100.0,
                            }
                        )
                    ]
                }
            )
        return res
