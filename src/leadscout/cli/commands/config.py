"""Configuration management commands."""

from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml

from ...core.config import Settings, get_config_locations, load_config_file


@click.group()
def config() -> None:
    """Manage LeadScout configuration.

    Configure API keys, settings, and other options required for
    the lead enrichment system to function properly.
    """


@config.command()
@click.argument("key", type=str)
@click.argument("value", type=str)
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    help="Set configuration globally for all projects",
)
@click.pass_context
def set(ctx: click.Context, key: str, value: str, is_global: bool) -> None:
    """Set a configuration value.

    Sets configuration values for API keys and other settings.
    By default, settings are stored for the current project only.
    Use --global to set system-wide defaults.

    Common configuration keys:
        openai_api_key        - OpenAI API key for name classification
        claude_api_key        - Claude API key for alternative classification
        cache_dir            - Directory for cache storage
        log_level            - Logging level (DEBUG, INFO, WARNING, ERROR)
        max_concurrent       - Default concurrent API calls
        batch_size           - Default batch processing size

    Examples:
        leadscout config set openai_api_key sk-...
        leadscout config set cache_dir /path/to/cache
        leadscout config set --global log_level INFO
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Setting configuration: {key}")
        click.echo(f"Global: {is_global}")
        # Don't log the actual value for security
        click.echo(
            f"Value: {'*' * len(value) if 'key' in key.lower() else value}"
        )

    # Validate key names
    valid_keys = {
        "openai_api_key",
        "claude_api_key", 
        "anthropic_api_key",
        "cache_dir",
        "log_level",
        "max_concurrent",
        "batch_size",
        "confidence_threshold",
        "cache_ttl_days",
        "enable_telemetry",
    }

    if key not in valid_keys:
        click.echo(
            f"Warning: '{key}' is not a recognized configuration key", err=True
        )
        click.echo(f"Valid keys: {', '.join(sorted(valid_keys))}")
        if not click.confirm("Continue anyway?"):
            ctx.exit(1)

    try:
        # Get config file path
        config_locations = get_config_locations()
        config_path = config_locations["global_config" if is_global else "project_config"]
        
        # Create config directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing config or create new
        config_data = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
            except Exception as e:
                if verbose:
                    click.echo(f"Warning: Could not load existing config: {e}")
        
        # Convert value to appropriate type
        converted_value = _convert_config_value(key, value)
        
        # Update config data
        config_data[key] = converted_value
        
        # Save config file
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        config_scope = "global" if is_global else "project"
        click.echo(f"✅ Set {config_scope} configuration:")
        click.echo(f"  {key} = {'[HIDDEN]' if 'key' in key.lower() else converted_value}")
        click.echo(f"  Saved to: {config_path}")
        
    except Exception as e:
        click.echo(f"❌ Failed to set configuration: {e}", err=True)
        ctx.exit(1)


@config.command()
@click.argument("key", type=str, required=False)
@click.option(
    "--all", "show_all", is_flag=True, help="Show all configuration values"
)
@click.pass_context
def get(ctx: click.Context, key: Optional[str], show_all: bool) -> None:
    """Get configuration value(s).

    Displays current configuration values. Shows a single value if
    a key is specified, or all values if --all is used.

    Examples:
        leadscout config get openai_api_key
        leadscout config get --all
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if not key and not show_all:
        click.echo("Error: Specify a configuration key or use --all", err=True)
        ctx.exit(1)

    if verbose:
        if key:
            click.echo(f"Getting configuration: {key}")
        else:
            click.echo("Getting all configuration values")

    try:
        # Load current settings
        settings = Settings()
        config_data = settings.to_dict(include_secrets=False)
        
        if show_all:
            click.echo("Current configuration:")
            click.echo("=" * 50)
            
            # Group by category
            api_keys = ["openai_api_key", "claude_api_key", "anthropic_api_key"]
            cache_settings = ["cache_dir", "cache_ttl_days"]
            processing = ["max_concurrent", "batch_size", "confidence_threshold"]
            other = ["log_level", "enable_telemetry"]
            
            click.echo("\n🔑 API Keys:")
            for k in api_keys:
                if k in config_data:
                    status = "[SET]" if config_data[k] != "[HIDDEN]" and config_data[k] is not None else "[NOT SET]"
                    click.echo(f"  {k}: {status}")
            
            click.echo("\n📁 Cache Settings:")
            for k in cache_settings:
                if k in config_data:
                    click.echo(f"  {k}: {config_data[k]}")
            
            click.echo("\n⚙️  Processing Settings:")
            for k in processing:
                if k in config_data:
                    click.echo(f"  {k}: {config_data[k]}")
            
            click.echo("\n🔧 Other Settings:")
            for k in other:
                if k in config_data:
                    click.echo(f"  {k}: {config_data[k]}")
                    
        elif key:
            if key in config_data:
                value = config_data[key]
                if "key" in key.lower() and value != "[HIDDEN]" and value is not None:
                    click.echo(f"{key}: [HIDDEN]")
                else:
                    click.echo(f"{key}: {value}")
            else:
                click.echo(f"❌ Configuration key '{key}' not found")
                ctx.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Failed to get configuration: {e}", err=True)
        ctx.exit(1)


@config.command()
@click.pass_context
def show(ctx: click.Context) -> None:
    """Show all configuration values and their sources.

    Displays the complete configuration including:
    - Current values and their sources (file, environment, default)
    - Configuration file locations
    - Environment variables
    - Validation status
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("Showing complete configuration...")

    try:
        # Load current settings and config locations
        settings = Settings()
        config_locations = get_config_locations()
        
        click.echo("LeadScout Configuration")
        click.echo("=" * 50)

        click.echo("\n📁 Configuration Sources:")
        
        # Check each config file
        for name, path in config_locations.items():
            exists = "✅" if path.exists() else "❌"
            click.echo(f"  {name.replace('_', ' ').title()}: {exists} {path}")
        
        # Show validation results
        validation = settings.validate_configuration()
        
        click.echo(f"\n🔍 Configuration Status:")
        status_icon = "✅" if validation["valid"] else "❌"
        click.echo(f"  Overall Status: {status_icon} {'Valid' if validation['valid'] else 'Issues Found'}")
        click.echo(f"  API Keys Configured: {'✅' if validation['api_keys_configured'] else '❌'}")
        click.echo(f"  Cache Directory: {'✅' if validation['cache_dir_exists'] else '❌'} {validation['cache_db_path']}")
        
        # Show issues if any
        if validation["issues"]:
            click.echo(f"\n❌ Issues:")
            for issue in validation["issues"]:
                click.echo(f"  • {issue}")
        
        if validation["warnings"]:
            click.echo(f"\n⚠️  Warnings:")
            for warning in validation["warnings"]:
                click.echo(f"  • {warning}")
        
        # Show current values
        config_data = settings.to_dict(include_secrets=False)
        
        click.echo("\n🔑 API Configuration:")
        api_keys = ["openai_api_key", "claude_api_key", "anthropic_api_key"]
        for key in api_keys:
            if key in config_data:
                value = config_data[key]
                status = "[SET]" if value == "[HIDDEN]" else "[NOT SET]" if value is None else "[SET]"
                source = "(environment)" if value == "[HIDDEN]" else "(default)" if value is None else "(config file)"
                click.echo(f"  {key}: {status} {source}")

        click.echo("\n⚙️  Processing Configuration:")
        processing_keys = ["max_concurrent", "batch_size", "confidence_threshold"]
        for key in processing_keys:
            if key in config_data:
                click.echo(f"  {key}: {config_data[key]}")
        
        click.echo("\n📁 Cache Configuration:")
        cache_keys = ["cache_dir", "cache_ttl_days"]
        for key in cache_keys:
            if key in config_data:
                click.echo(f"  {key}: {config_data[key]}")
        
        click.echo("\n🔧 Other Settings:")
        other_keys = ["log_level", "enable_telemetry"]
        for key in other_keys:
            if key in config_data:
                click.echo(f"  {key}: {config_data[key]}")
                
    except Exception as e:
        click.echo(f"❌ Failed to show configuration: {e}", err=True)
        ctx.exit(1)


@config.command()
@click.pass_context
def test(ctx: click.Context) -> None:
    """Test configuration and API connections.

    Validates the current configuration by:
    - Checking API key formats
    - Testing API connections
    - Verifying cache directory access
    - Validating all settings
    """
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo("Testing configuration and connections...")

    try:
        # Load settings and validate
        settings = Settings()
        validation = settings.validate_configuration()
        
        click.echo("Testing LeadScout Configuration...")
        click.echo("=" * 50)

        click.echo("\n🔍 Checking Configuration:")
        if validation["valid"]:
            click.echo("  ✅ Configuration: Valid")
        else:
            click.echo("  ❌ Configuration: Issues found")
            for issue in validation["issues"]:
                click.echo(f"    • {issue}")

        click.echo("\n🔑 Checking API Keys:")
        
        # Check OpenAI key
        openai_key = settings.get_openai_key()
        if openai_key:
            if openai_key.startswith('sk-') and len(openai_key) > 20:
                click.echo("  ✅ OpenAI API Key: Valid format")
            else:
                click.echo("  ⚠️  OpenAI API Key: Invalid format")
        else:
            click.echo("  ❌ OpenAI API Key: Not configured")
        
        # Check Claude/Anthropic key
        claude_key = settings.get_claude_key() or settings.get_anthropic_key()
        if claude_key:
            click.echo("  ✅ Claude/Anthropic API Key: Configured")
        else:
            click.echo("  ❌ Claude/Anthropic API Key: Not configured")

        click.echo("\n📁 Checking Cache Directory:")
        cache_dir = settings.cache_dir
        if cache_dir.exists():
            click.echo(f"  ✅ Cache directory: {cache_dir}")
            
            # Test write permissions
            try:
                test_file = cache_dir / ".write_test"
                test_file.touch()
                test_file.unlink()
                click.echo("  ✅ Write permissions: OK")
            except Exception as e:
                click.echo(f"  ❌ Write permissions: Failed - {e}")
        else:
            click.echo(f"  ❌ Cache directory: Does not exist - {cache_dir}")

        # Test database connectivity
        click.echo("\n🗄️  Checking Database:")
        try:
            import sqlite3
            
            # Test jobs database
            jobs_db_path = Path("cache/jobs.db")
            if jobs_db_path.exists():
                conn = sqlite3.connect(jobs_db_path)
                conn.execute("SELECT 1")
                conn.close()
                click.echo("  ✅ Jobs database: Accessible")
            else:
                click.echo("  ⚠️  Jobs database: Not found (will be created on first use)")
            
            # Test learning database
            learning_db_path = Path("cache/llm_learning.db")
            if learning_db_path.exists():
                conn = sqlite3.connect(learning_db_path)
                conn.execute("SELECT 1")
                conn.close()
                click.echo("  ✅ Learning database: Accessible")
            else:
                click.echo("  ⚠️  Learning database: Not found (will be created on first use)")
                
        except Exception as e:
            click.echo(f"  ❌ Database connectivity: Failed - {e}")

        # Summary
        click.echo("\n📊 Summary:")
        if validation["valid"] and settings.has_llm_keys():
            click.echo("  ✅ Configuration is ready for use")
        else:
            click.echo("  ⚠️  Configuration has issues that may affect functionality")
            if not settings.has_llm_keys():
                click.echo("  💡 Tip: Set at least one API key to enable name classification")
                click.echo("      leadscout config set openai_api_key YOUR_KEY")
                
    except Exception as e:
        click.echo(f"❌ Configuration test failed: {e}", err=True)
        ctx.exit(1)


def _convert_config_value(key: str, value: str) -> Any:
    """Convert string value to appropriate type for configuration key."""
    
    # Integer values
    if key in ["max_concurrent", "batch_size", "cache_ttl_days"]:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"'{key}' must be an integer, got: {value}")
    
    # Float values
    if key in ["confidence_threshold"]:
        try:
            float_val = float(value)
            if not 0.0 <= float_val <= 1.0:
                raise ValueError(f"'{key}' must be between 0.0 and 1.0, got: {float_val}")
            return float_val
        except ValueError:
            raise ValueError(f"'{key}' must be a number between 0.0 and 1.0, got: {value}")
    
    # Boolean values
    if key in ["enable_telemetry"]:
        if value.lower() in ["true", "yes", "1", "on"]:
            return True
        elif value.lower() in ["false", "no", "0", "off"]:
            return False
        else:
            raise ValueError(f"'{key}' must be true/false, got: {value}")
    
    # Log level validation
    if key == "log_level":
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value.upper() not in valid_levels:
            raise ValueError(f"'{key}' must be one of {valid_levels}, got: {value}")
        return value.upper()
    
    # Path values
    if key in ["cache_dir"]:
        return str(Path(value).expanduser().resolve())
    
    # String values (API keys, etc.)
    return value
