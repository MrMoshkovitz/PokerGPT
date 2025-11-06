"""
Configuration Management

Load and manage application configuration from YAML files and environment variables.
"""

import yaml
import os
from typing import Any, Dict
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """Application configuration manager."""

    def __init__(self, config_path: str = "config/default_config.yaml"):
        """
        Load configuration from YAML file and environment variables.

        Args:
            config_path: Path to YAML config file
        """
        self.config: Dict[str, Any] = {}
        self.config_path = config_path

        # Load environment variables
        load_dotenv()

        # Load YAML config
        self._load_yaml_config()

        # Override with environment variables
        self._load_env_overrides()

        logger.info(f"Configuration loaded from {config_path}")

    def _load_yaml_config(self):
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self.config = {}
        except Exception as e:
            logger.error(f"Error loading YAML config: {e}")
            self.config = {}

    def _load_env_overrides(self):
        """Override config with environment variables."""
        # LLM API keys
        if os.getenv("OPENAI_API_KEY"):
            self.config.setdefault("llm", {})["openai_api_key"] = os.getenv(
                "OPENAI_API_KEY"
            )

        if os.getenv("GEMINI_API_KEY"):
            self.config.setdefault("llm", {})["gemini_api_key"] = os.getenv(
                "GEMINI_API_KEY"
            )

        # Application settings
        if os.getenv("LOG_LEVEL"):
            self.config.setdefault("logging", {})["level"] = os.getenv("LOG_LEVEL")

        if os.getenv("DATABASE_PATH"):
            self.config.setdefault("database", {})["path"] = os.getenv("DATABASE_PATH")

        if os.getenv("MODEL_PATH"):
            self.config.setdefault("vision", {})["model_path"] = os.getenv("MODEL_PATH")

        # Performance settings
        if os.getenv("VISION_CONFIDENCE_THRESHOLD"):
            self.config.setdefault("vision", {})["confidence_threshold"] = float(
                os.getenv("VISION_CONFIDENCE_THRESHOLD")
            )

        if os.getenv("LLM_TIMEOUT_SECONDS"):
            self.config.setdefault("llm", {})["timeout_seconds"] = int(
                os.getenv("LLM_TIMEOUT_SECONDS")
            )

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "vision.model_path")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "vision.model_path")
            value: Value to set
        """
        keys = key_path.split(".")
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self, path: str = None):
        """
        Save configuration to YAML file.

        Args:
            path: Path to save (defaults to original config_path)
        """
        save_path = path or self.config_path

        try:
            with open(save_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def __repr__(self) -> str:
        return f"Config({self.config_path})"


# Global config instance
_config_instance: Config = None


def get_config() -> Config:
    """Get global configuration instance (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
