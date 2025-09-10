{
    'name': 'estate',
    'summary': 'Real estate management',
    'description': 'Real estate management module from the tutorial',
    'depends': [
        'base',
        'web'
    ],
    'version': '0.9',
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_type_views.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_views.xml',
        'views/estate_menus.xml'
    ],
}
