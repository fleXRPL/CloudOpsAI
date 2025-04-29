"""
YAML Configuration Engine module.

This module handles the loading and parsing of YAML-based remediation rules
from S3, providing a structured way to define monitoring and remediation logic.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import boto3
import yaml
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class YAMLConfig:
    """
    YAML configuration parser and manager for NOC Agent rules.

    This class handles loading and parsing of YAML configuration files from S3,
    providing methods to match incoming alerts with defined remediation rules.

    Attributes:
        s3 (boto3.client): AWS S3 client for configuration file access
        rules (Dict[str, Any]): Parsed remediation rules from YAML configuration
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager with S3 client and load rules.

        Args:
            config_path (str, optional): S3 path to configuration file. If not provided,
                                       will be read from environment variable CONFIG_S3_PATH.
        """
        try:
            self.s3 = boto3.client("s3")
            self.config_path = config_path or os.environ.get("CONFIG_S3_PATH")
            if not self.config_path:
                raise ValueError("Configuration S3 path not provided")
            self.rules = self._load_config()
        except Exception as e:
            logger.error(f"Failed to initialize YAMLConfig: {str(e)}")
            raise

    def _load_config(self) -> Dict[str, Any]:
        """
        Load and parse YAML configuration from S3.

        Returns:
            Dict[str, Any]: Parsed YAML configuration containing remediation rules

        Raises:
            ClientError: If S3 access fails
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            bucket, key = self._parse_s3_path()
            response = self.s3.get_object(Bucket=bucket, Key=key)
            return yaml.safe_load(response["Body"])
        except ClientError as e:
            logger.error(f"Failed to load configuration from S3: {str(e)}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {str(e)}")
            raise

    def _parse_s3_path(self) -> Tuple[str, str]:
        """
        Parse S3 path into bucket and key.

        Returns:
            Tuple[str, str]: Tuple containing (bucket, key)

        Raises:
            ValueError: If S3 path is invalid
        """
        try:
            parts = self.config_path.replace("s3://", "").split("/")
            if len(parts) < 2:
                raise ValueError(f"Invalid S3 path: {self.config_path}")
            return parts[0], "/".join(parts[1:])
        except Exception as e:
            logger.error(f"Failed to parse S3 path: {str(e)}")
            raise

    def get_matching_rules(self, alarm_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find matching remediation rules for a given alarm.

        Args:
            alarm_data (Dict[str, Any]): CloudWatch alarm data

        Returns:
            List[Dict[str, Any]]: List of matching remediation rules
        """
        try:
            matching = []
            for rule in self.rules.get("rules", []):
                if self._rule_matches(rule, alarm_data):
                    matching.append(rule)
            return matching
        except Exception as e:
            logger.error(f"Failed to get matching rules: {str(e)}")
            return []

    def _rule_matches(self, rule: Dict[str, Any], alarm_data: Dict[str, Any]) -> bool:
        """
        Check if a rule matches the given alarm data.

        Args:
            rule (Dict[str, Any]): Rule to check
            alarm_data (Dict[str, Any]): Alarm data to match against

        Returns:
            bool: True if rule matches, False otherwise
        """
        try:
            # Implement rule matching logic here
            # This is a placeholder - implement actual matching logic
            return True
        except Exception as e:
            logger.error(f"Failed to check rule match: {str(e)}")
            return False

    def get_slack_webhook_url(self) -> str:
        """Get Slack webhook URL from configuration."""
        if "notifications" not in self.rules:
            raise ValueError("Notifications configuration not found")
        if "slack" not in self.rules["notifications"]:
            raise ValueError("Slack configuration not found")
        return str(self.rules["notifications"]["slack"]["webhook_url"])

    def get_teams_webhook_url(self) -> str:
        """Get Teams webhook URL from configuration."""
        if "notifications" not in self.rules:
            raise ValueError("Notifications configuration not found")
        if "teams" not in self.rules["notifications"]:
            raise ValueError("Teams configuration not found")
        return str(self.rules["notifications"]["teams"]["webhook_url"])

    def get_email_from(self) -> str:
        """Get email sender address from configuration."""
        if "notifications" not in self.rules:
            raise ValueError("Notifications configuration not found")
        if "email" not in self.rules["notifications"]:
            raise ValueError("Email configuration not found")
        return str(self.rules["notifications"]["email"]["from"])

    def get_email_recipients(self) -> List[str]:
        """Get email recipient list from configuration."""
        if "notifications" not in self.rules:
            raise ValueError("Notifications configuration not found")
        if "email" not in self.rules["notifications"]:
            raise ValueError("Email configuration not found")
        return list(self.rules["notifications"]["email"]["recipients"])

    def get_pagerduty_key(self) -> str:
        """Get PagerDuty API key from configuration."""
        if "notifications" not in self.rules:
            raise ValueError("Notifications configuration not found")
        if "pagerduty" not in self.rules["notifications"]:
            raise ValueError("PagerDuty configuration not found")
        return str(self.rules["notifications"]["pagerduty"]["api_key"])
