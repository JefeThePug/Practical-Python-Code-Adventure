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
        return app.data_cache.admin.html_nums[year][value]

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
        return f"{app.data_cache.admin.obfuscations[session['year']][int(value)]}"

    @app.context_processor
    def inject_css_files() -> dict[str, list[str]]:
        """Inject global template variables for CSS and border asset selection.
        Provides:
            - borders: Year-coded border suffixes (e.g. "2025A", "2025B")
            - css_files: Ordered list of CSS base names to be loaded by templates
        Returns:
            dict[str, list[str]]: Template context variables available to all
            rendered Jinja templates.
        """
        year = app.config["CURRENT_YEAR"]
        return {
            "css_files": [
                "main",
                f"year_overrides/style{session.get('year', year)}",
            ],
        }
