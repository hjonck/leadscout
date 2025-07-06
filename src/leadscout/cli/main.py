"""Main CLI entry point for LeadScout.

This module provides the primary command-line interface for the LeadScout
lead enrichment system.
"""

from pathlib import Path
from typing import Optional

import click

from ..core.config import get_settings
from .commands import cache, config, enrich
from .jobs import jobs


@click.group()
@click.version_option()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def cli(
    ctx: click.Context, verbose: bool, config_file: Optional[Path]
) -> None:
    """LeadScout: AI-Powered Lead Enrichment System.

    Enrich business lead data with AI-powered research including:
    - Name ethnicity classification for targeting
    - Website discovery and validation
    - LinkedIn profile research
    - Contact information validation
    - Lead scoring and prioritization

    Examples:
        leadscout enrich leads.xlsx --output enriched_leads.xlsx
        leadscout cache status
        leadscout config set openai_api_key YOUR_KEY
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options
    ctx.obj["verbose"] = verbose
    ctx.obj["config_file"] = config_file

    # Load and validate configuration
    try:
        settings = get_settings(config_file)
        ctx.obj["settings"] = settings
    except Exception as e:
        if verbose:
            click.echo(f"Configuration error: {e}", err=True)
        # Don't fail here - some commands (like config) might still work


# Add command groups
cli.add_command(enrich.enrich)
cli.add_command(cache.cache)
cli.add_command(config.config)
cli.add_command(jobs)


if __name__ == "__main__":
    cli()
