from odoo import fields, models

class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Real estate tag'
    _sql_constraints = [
        ('check_name','UNIQUE(name)','The Tag Name must be unique.'),
    ]
    _order = "name"
    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    color = fields.Integer("Color Index")
