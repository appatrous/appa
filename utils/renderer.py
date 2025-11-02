"""
Configuration rendering utilities.
Handles Jinja2 template rendering for different platforms and output formats.
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class RenderError(Exception):
    """Custom exception for rendering errors."""
    pass


class ConfigRenderer:
    """Configuration renderer using Jinja2 templates."""

    def __init__(self, template_dir: Path, config_template_dir: Path):
        """
        Initialize renderer with template directories.

        Args:
            template_dir: Main template directory
            config_template_dir: Config fragments directory
        """
        self.template_dir = template_dir
        self.config_template_dir = config_template_dir

        # Create Jinja2 environment with multiple template directories
        self.env = Environment(
            loader=FileSystemLoader([
                str(template_dir),
                str(config_template_dir)
            ]),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

        # Add custom filters
        self.env.filters['to_json'] = self.to_json_filter
        self.env.filters['to_yaml'] = self.to_yaml_filter

    @staticmethod
    def to_json_filter(value: Any, indent: int = 2) -> str:
        """Jinja2 filter to convert value to JSON."""
        return json.dumps(value, indent=indent)

    @staticmethod
    def to_yaml_filter(value: Any) -> str:
        """Jinja2 filter to convert value to YAML."""
        return yaml.dump(value, default_flow_style=False)

    def render(self, platform: str, config_data: Dict[str, Any],
               output_format: str = 'cli') -> str:
        """
        Render configuration based on platform and format.

        Args:
            platform: Platform type (ios, nxos, asa, iosxr)
            config_data: Configuration data dictionary
            output_format: Output format (cli, json, yaml)

        Returns:
            str: Rendered configuration

        Raises:
            RenderError: If rendering fails
        """
        platform_lower = platform.lower()

        # Determine template name based on format
        if output_format == 'cli':
            template_name = f'{platform_lower}_config.j2'
        elif output_format == 'json':
            return self._render_json(config_data)
        elif output_format == 'yaml':
            return self._render_yaml(config_data)
        else:
            raise RenderError(f"Unsupported output format: {output_format}")

        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise RenderError(
                f"Template not found for platform '{platform}': {template_name}"
            )

        try:
            rendered = template.render(**config_data)
            return rendered.strip() + '\n'
        except Exception as e:
            raise RenderError(f"Template rendering failed: {str(e)}")

    def _render_json(self, config_data: Dict[str, Any]) -> str:
        """
        Render configuration as JSON.

        Args:
            config_data: Configuration data

        Returns:
            str: JSON string
        """
        try:
            return json.dumps(config_data, indent=2) + '\n'
        except Exception as e:
            raise RenderError(f"JSON rendering failed: {str(e)}")

    def _render_yaml(self, config_data: Dict[str, Any]) -> str:
        """
        Render configuration as YAML.

        Args:
            config_data: Configuration data

        Returns:
            str: YAML string
        """
        try:
            return yaml.dump(config_data, default_flow_style=False,
                             sort_keys=False)
        except Exception as e:
            raise RenderError(f"YAML rendering failed: {str(e)}")

    def list_templates(self, platform: Optional[str] = None) -> list:
        """
        List available templates.

        Args:
            platform: Optional platform filter

        Returns:
            list: Template names
        """
        templates = []
        for path in self.template_dir.glob('*.j2'):
            template_name = path.name
            if platform:
                if template_name.startswith(platform.lower()):
                    templates.append(template_name)
            else:
                templates.append(template_name)

        return sorted(templates)


def render_config(platform: str, config_data: Dict[str, Any],
                  output_format: str = 'cli',
                  template_dir: Optional[Path] = None,
                  config_template_dir: Optional[Path] = None) -> str:
    """
    Convenience function to render configuration.

    Args:
        platform: Platform type
        config_data: Configuration data
        output_format: Output format
        template_dir: Optional template directory override
        config_template_dir: Optional config template directory override

    Returns:
        str: Rendered configuration

    Raises:
        RenderError: If rendering fails
    """
    from flask import current_app

    if template_dir is None:
        template_dir = current_app.config['TEMPLATE_DIR']

    if config_template_dir is None:
        config_template_dir = current_app.config['CONFIG_TEMPLATE_DIR']

    renderer = ConfigRenderer(template_dir, config_template_dir)
    return renderer.render(platform, config_data, output_format)
