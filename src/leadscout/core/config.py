"""Configuration management for LeadScout.

This module handles all configuration loading, validation, and management
including API keys, cache settings, and processing parameters.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """LeadScout configuration settings.

    Uses Pydantic BaseSettings to load configuration from multiple sources:
    1. Environment variables
    2. .env files
    3. Configuration files
    4. Default values

    Attributes:
        openai_api_key: OpenAI API key for name classification
        claude_api_key: Claude API key for alternative classification
        cache_dir: Directory for SQLite cache storage
        log_level: Logging level for the application
        max_concurrent: Maximum concurrent API calls
        batch_size: Default batch size for processing
        confidence_threshold: Minimum confidence for classifications
        cache_ttl_days: Cache time-to-live in days
        enable_telemetry: Whether to enable usage telemetry

    Example:
        >>> settings = Settings()
        >>> settings.get_openai_key()
        'sk-...'
    """

    # API Configuration
    openai_api_key: Optional[SecretStr] = Field(
        default=None, description="OpenAI API key for name classification"
    )
    claude_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Claude API key for alternative classification",
    )

    # Cache Configuration
    cache_dir: Path = Field(
        default=Path("./cache"), description="Directory for cache storage"
    )
    cache_ttl_days: int = Field(
        default=30, description="Cache time-to-live in days"
    )

    # Processing Configuration
    max_concurrent: int = Field(
        default=10, ge=1, le=50, description="Maximum concurrent API calls"
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Default batch size for processing",
    )

    # Classification Configuration
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for classifications",
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")

    # Application Configuration
    enable_telemetry: bool = Field(
        default=True, description="Enable usage telemetry"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="LEADSCOUT_",
    )

    @field_validator("cache_dir")
    @classmethod
    def validate_cache_dir(cls, v: Path) -> Path:
        """Validate and create cache directory if needed."""
        if not v.is_absolute():
            v = Path.cwd() / v

        # Create directory if it doesn't exist
        v.mkdir(parents=True, exist_ok=True)

        # Check write permissions
        test_file = v / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise ValueError(f"Cache directory not writable: {v} - {e}")

        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level. Must be one of: {valid_levels}"
            )
        return v.upper()

    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key value.

        Returns:
            API key string or None if not set
        """
        return (
            self.openai_api_key.get_secret_value()
            if self.openai_api_key
            else None
        )

    def get_claude_key(self) -> Optional[str]:
        """Get Claude API key value.

        Returns:
            API key string or None if not set
        """
        return (
            self.claude_api_key.get_secret_value()
            if self.claude_api_key
            else None
        )

    def has_llm_keys(self) -> bool:
        """Check if at least one LLM API key is configured.

        Returns:
            True if any LLM API key is available
        """
        return bool(self.get_openai_key() or self.get_claude_key())

    def get_cache_db_path(self) -> Path:
        """Get path to SQLite cache database.

        Returns:
            Path to cache database file
        """
        return self.cache_dir / "leadscout.db"

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the complete configuration.

        Returns:
            Dictionary containing validation results
        """
        issues = []
        warnings = []

        # Check API keys
        if not self.has_llm_keys():
            issues.append(
                "No LLM API keys configured - name classification will not work"
            )

        # Check cache directory
        if not self.cache_dir.exists():
            warnings.append(
                f"Cache directory does not exist: {self.cache_dir}"
            )
        elif not self.cache_dir.is_dir():
            issues.append(f"Cache path is not a directory: {self.cache_dir}")

        # Check configuration values
        if self.max_concurrent > 20:
            warnings.append(
                f"High concurrent limit ({self.max_concurrent}) may hit API rate limits"
            )

        if self.batch_size > 500:
            warnings.append(
                f"Large batch size ({self.batch_size}) may cause memory issues"
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "api_keys_configured": self.has_llm_keys(),
            "cache_dir_exists": self.cache_dir.exists(),
            "cache_db_path": str(self.get_cache_db_path()),
        }

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert settings to dictionary.

        Args:
            include_secrets: Whether to include secret values

        Returns:
            Dictionary representation of settings
        """
        data = {}

        for field_name, field in self.model_fields.items():
            value = getattr(self, field_name)

            # Handle SecretStr fields
            if isinstance(value, SecretStr):
                if include_secrets:
                    data[field_name] = value.get_secret_value()
                else:
                    data[field_name] = (
                        "[HIDDEN]" if value is not None else None
                    )
            # Handle Path fields
            elif isinstance(value, Path):
                data[field_name] = str(value)
            else:
                data[field_name] = value

        return data


@lru_cache()
def get_settings(config_file: Optional[Path] = None) -> Settings:
    """Get cached settings instance.

    Uses LRU cache to ensure settings are loaded only once per session.

    Args:
        config_file: Optional path to configuration file

    Returns:
        Settings instance
    """
    if config_file:
        # If config file is provided, load from that file
        # TODO: Implement config file loading
        pass

    return Settings(openai_api_key=None, claude_api_key=None)


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML or TOML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If config file doesn't exist
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    import yaml

    suffix = config_path.suffix.lower()

    if suffix in [".yml", ".yaml"]:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    elif suffix == ".toml":
        import toml

        with open(config_path, "r", encoding="utf-8") as f:
            return toml.load(f)
    else:
        raise ValueError(f"Unsupported config file format: {suffix}")


def create_example_config(output_path: Path) -> None:
    """Create an example configuration file.

    Args:
        output_path: Where to create the example config file
    """
    example_config = {
        "api_keys": {
            "openai_api_key": "sk-your-openai-key-here",
            "claude_api_key": "your-claude-key-here",
        },
        "cache": {"cache_dir": "./cache", "cache_ttl_days": 30},
        "processing": {
            "max_concurrent": 10,
            "batch_size": 100,
            "confidence_threshold": 0.8,
        },
        "logging": {"log_level": "INFO"},
        "application": {"enable_telemetry": True},
    }

    import yaml

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(example_config, f, default_flow_style=False, indent=2)


def get_config_locations() -> Dict[str, Path]:
    """Get standard configuration file locations.

    Returns:
        Dictionary mapping config types to their paths
    """
    home = Path.home()
    cwd = Path.cwd()

    return {
        "global_config": home / ".leadscout" / "config.yml",
        "project_config": cwd / ".leadscout" / "config.yml",
        "env_file": cwd / ".env",
        "global_env": home / ".leadscout" / ".env",
    }
