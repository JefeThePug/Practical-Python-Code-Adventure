from flask import session

from app.appctx import get_app


def register_globals():
    """Register global Jinja template helpers.
    Attaches utility functions to the Flask application so they can be
    used directly inside Jinja templates.
    """
    app = get_app()

    @app.template_global()
    def obfuscate(year: str, value: str | int) -> str | int:
        """Obfuscate a value using the obfuscation mapping.
        Args:
            value (str | int): The value to obfuscate.
            year (str): Current year
        Returns:
            str | int: The obfuscated value.
        """
        return app.data_access.admin.html_nums[year][value]

    @app.template_global()
    def obscure_post(value: str | int) -> str:
        """Obscure a challenge number for display in templates.
        Args:
            value (str | int): The number to obfuscate.
        Returns:
            str: The obfuscated number for HTML output.
        """
        if isinstance(value, str):
            value = int(value)
        return f"{app.data_access.admin.obfuscations[session['year']][int(value)]}"

    @app.context_processor
    def inject_assets() -> dict[str, list[str]]:
        """Inject global template variables for CSS and JS.
        Returns:
            dict[str, list[str]]: Template context variables available to all
            rendered Jinja templates.
        """
        year = session.get("year") or app.config["CURRENT_YEAR"]
        main_file = "main.min" if app.config["USE_MINIFIED_ASSETS"] else "main"
        return {
            "css_files": [main_file, f"year_overrides/style{year}"],
            "js_files": [f"year_overrides/script{year}"],
        }
