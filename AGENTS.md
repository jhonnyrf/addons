# AGENTS.md

## Modules

| Module | Purpose |
|--------|---------|
| `wigo_ftth` | FTTH/GPON network topology, ONUs, work orders, technical sheet |
| `wigo_planes` | Internet plans (fiber/wireless/cable), promotions, referrals |
| `customer_contract` | Customer contracts with auto-sequencing |
| `wigo_crm` | CRM customization |
| `crm_service_cancellation` | Service cancellation from CRM (leads) |
| `wigo_cobranza` | Payment status, collection, mora/suspension flow |
| `wigo_helpdesk` | Support tickets with SLA |
| `contactos_ext` | Contact extensions |
| `web_dark_mode` | Dark mode UI |

## Development

- **Format**: Standard Odoo 19 (`__manifest__.py`, `models/`, `views/`, `wizard/`, `security/`)
- **CSS**: Add in manifest `'assets.web.assets_backend'` — NOT `'assets.xml'`
- **Data loading**: Use absolute paths in manifest `'data/'` list
- **Dependencies**: Declare in `'depends'` key
- **No separate `__init__.py`** for views; define directly in XML
- **Post-init hooks**: Use `'post_init_hook'` key (e.g., `wigo_helpdesk`)

## Commands

```bash
# Start Odoo server (from Odoo root)
./odoo-bin -d wigo_db -u wigo_ftth --test-enabled

# Upgrade single module
./odoo-bin -d wigo_db -u wigo_ftth
```

## Conventions

- Manifest encoding: `# -*- coding: utf-8 -*-`
- Python model: `class FtthTopology(models.Model)` → `_name = 'ftth.topology'`
- View IDs: `<record id="view_..." model="ir.ui.view">`
- XML menus: `<menuitem id="menu_...">`
- Security: XML `security.xml` + CSV `ir.model.access.csv`
- Wizard actions: `<record model="ir.actions.act_window" id="action_...">`

## Dependencies Chain

```
wigo_planes → base, mail, contacts
customer_contract → base, mail, wigo_planes, crm
wigo_crm → base, crm, wigo_planes, customer_contract
wigo_ftth → base, mail, contacts, crm, wigo_crm, wigo_planes, hr
wigo_cobranza → base, mail, wigo_ftth, wigo_planes, customer_contract, wigo_crm
wigo_helpdesk → base, mail, web, hr, customer_contract, wigo_ftth
crm_service_cancellation → crm, wigo_crm, customer_contract, wigo_ftth, wigo_cobranza
```