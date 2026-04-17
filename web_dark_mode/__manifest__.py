{
    "name": "Dark Mode",
    "summary": "Modo oscuro para los modulos de Wigo Fast en Odoo",
    "license": "AGPL-3",
    "version": "19.0.1.0.0",
    "website": "https://wigo-fast.com",
    "author": "Desarrolladores de Wigo Fast",
    "depends": ["web"],
    "excludes": ["web_enterprise"],
    "installable": True,
    "assets": {
        "web.dark_mode_assets_common": [
            ("prepend", "web_dark_mode/static/src/scss/primary_variables.dark.scss"),
            ("prepend", "web_dark_mode/static/src/scss/secondary_variables.dark.scss"),
        ],
        "web.dark_mode_assets_backend": [
            ("prepend", "web_dark_mode/static/src/scss/primary_variables.dark.scss"),
            ("prepend", "web_dark_mode/static/src/scss/secondary_variables.dark.scss"),
            ("prepend", "web_dark_mode/static/src/scss/bootstrap_overridden.dark.scss"),
            ("prepend", "web_dark_mode/static/src/scss/bs_functions_overrides.dark.scss"),
        ],
        "web.assets_backend": [
            "web_dark_mode/static/src/js/switch_item.esm.js",
        ],
        "web.assets_backend_lazy_dark": [
            ("include", "web.assets_variables_dark"),
            ("include", "web.assets_backend_helpers_dark"),
        ],
        "web.assets_variables_dark": [
            (
                "before",
                "web/static/src/scss/primary_variables.scss",
                "web_dark_mode/static/src/scss/primary_variables.dark.scss",
            ),
            (
                "before",
                "web/static/src/scss/secondary_variables.scss",
                "web_dark_mode/static/src/scss/secondary_variables.dark.scss",
            ),
            (
                "before",
                "web/static/src/**/*.variables.scss",
                "web_dark_mode/static/src/**/*.variables.dark.scss",
            ),
        ],
        "web.assets_backend_helpers_dark": [
            (
                "before",
                "web/static/src/scss/bootstrap_overridden.scss",
                "web_dark_mode/static/src/scss/bootstrap_overridden.dark.scss",
            ),
            (
                "after",
                "web/static/lib/bootstrap/scss/_functions.scss",
                "web_dark_mode/static/src/scss/bs_functions_overrides.dark.scss",
            ),
        ],
        "web.assets_web_dark": [
            ("include", "web.assets_variables_dark"),
            ("include", "web.assets_backend_helpers_dark"),
            "web_dark_mode/static/src/**/*.dark.scss",
        ],
    },
    "data": [
        "views/res_users_views.xml",
    ],
}
