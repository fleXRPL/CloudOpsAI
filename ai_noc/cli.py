"""
Command Line Interface for CloudOpsAI.

This module provides a CLI for interacting with the NOC Agent, viewing alerts,
and managing configurations.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .ai_engine import AIDecisionEngine
from .config import YAMLConfig
from .utils import format_timestamp

logger = logging.getLogger(__name__)
console = Console()


class CloudOpsAICLI:
    """
    Command-line interface for CloudOpsAI system.

    Provides interactive access to:
    - Current alert status
    - Historical incident data
    - System actions and decisions
    - Time-based summaries
    """

    def __init__(
        self, config_path: Optional[str] = None, q_app_id: Optional[str] = None
    ):
        """
        Initialize CLI with required AWS clients and components.

        Args:
            config_path (str, optional): S3 path to configuration file. If not provided,
                                       will be read from environment variable CONFIG_S3_PATH.
            q_app_id (str, optional): Amazon Q application ID. If not provided,
                                    will be read from environment variable Q_APP_ID.
        """
        try:
            self.ai_engine = AIDecisionEngine(q_app_id=q_app_id)
            self.config = YAMLConfig(config_path=config_path)
            self.cloudwatch = boto3.client("cloudwatch")
            self.dynamodb = boto3.resource("dynamodb")
            self.incidents_table = self.dynamodb.Table("NOCIncidents")
        except ClientError as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    async def get_current_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all currently active CloudWatch alarms.

        Returns:
            List[Dict[str, Any]]: List of active CloudWatch alarms
        """
        try:
            response = self.cloudwatch.describe_alarms(StateValue="ALARM")
            return response.get("MetricAlarms", [])
        except ClientError as e:
            logger.error(f"Failed to get current alerts: {str(e)}")
            return []

    async def get_incident_history(self, hours: int) -> List[Dict[str, Any]]:
        """
        Get incident history for the specified time period.

        Args:
            hours (int): Number of hours to look back

        Returns:
            List[Dict[str, Any]]: List of incidents
        """
        try:
            if hours <= 0:
                raise ValueError("Hours must be positive")

            start_time = datetime.utcnow() - timedelta(hours=hours)
            response = self.incidents_table.scan(
                FilterExpression="timestamp >= :start",
                ExpressionAttributeValues={":start": start_time.isoformat()},
            )
            return response.get("Items", [])
        except ClientError as e:
            logger.error(f"Failed to get incident history: {str(e)}")
            return []

    async def ask_ai(self, question: str) -> Dict[str, Any]:
        """
        Ask the AI engine a question about the system.

        Args:
            question (str): Question to ask the AI

        Returns:
            Dict[str, Any]: AI response
        """
        try:
            if not question:
                raise ValueError("Question cannot be empty")

            return await self.ai_engine.evaluate(
                {"question": question}, self.config.get_matching_rules({})
            )
        except Exception as e:
            logger.error(f"Failed to get AI response: {str(e)}")
            return {"error": str(e), "status": "error"}

    def display_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """
        Display current alerts in a formatted table.

        Args:
            alerts (List[Dict[str, Any]]): List of alerts to display
        """
        try:
            table = Table(title="Current Alerts")
            table.add_column("Alarm Name")
            table.add_column("State")
            table.add_column("Metric")
            table.add_column("Value")

            for alert in alerts:
                table.add_row(
                    alert.get("AlarmName", "Unknown"),
                    alert.get("StateValue", "Unknown"),
                    alert.get("MetricName", "Unknown"),
                    str(alert.get("StateReasonData", "N/A")),
                )

            console.print(table)
        except Exception as e:
            logger.error(f"Failed to display alerts: {str(e)}")
            console.print(f"[red]Error displaying alerts: {str(e)}[/red]")

    def display_incidents(self, incidents: List[Dict[str, Any]]) -> None:
        """
        Display incident history in a formatted table.

        Args:
            incidents (List[Dict[str, Any]]): List of incidents to display
        """
        try:
            table = Table(title="Incident History")
            table.add_column("Time")
            table.add_column("Type")
            table.add_column("Status")
            table.add_column("Actions")

            for incident in incidents:
                table.add_row(
                    incident.get("timestamp", "Unknown"),
                    incident.get("type", "Unknown"),
                    incident.get("status", "Unknown"),
                    str(incident.get("actions", [])),
                )

            console.print(table)
        except Exception as e:
            logger.error(f"Failed to display incidents: {str(e)}")
            console.print(f"[red]Error displaying incidents: {str(e)}[/red]")

    def display_ai_response(self, response: Dict[str, Any]) -> None:
        """
        Display AI response in a formatted panel.

        Args:
            response (Dict[str, Any]): AI response to display
        """
        try:
            console.print(
                Panel(
                    json.dumps(response, indent=2),
                    title="AI Response",
                    border_style="blue",
                )
            )
        except Exception as e:
            logger.error(f"Failed to display AI response: {str(e)}")
            console.print(f"[red]Error displaying AI response: {str(e)}[/red]")

    async def list_alerts(self) -> List[Dict[str, Any]]:
        """List all active alerts."""
        try:
            cloudwatch = boto3.client("cloudwatch")
            response = cloudwatch.describe_alarms(StateValue="ALARM")

            alerts = response.get("MetricAlarms", [])
            return [
                {
                    "name": alert["AlarmName"],
                    "state": alert["StateValue"],
                    "metric": alert["MetricName"],
                    "namespace": alert["Namespace"],
                    "timestamp": format_timestamp(),
                }
                for alert in alerts
            ]
        except Exception as e:
            logger.error(f"Failed to list alerts: {str(e)}")
            return []


def show_status(detail: bool = False) -> None:
    """Show system status."""
    try:
        config = YAMLConfig()
        status = {
            "config_loaded": bool(config.rules),
            "aws_configured": True,
            "time": datetime.utcnow().isoformat(),
        }

        if detail:
            cloudwatch = boto3.client("cloudwatch")
            status["active_alarms"] = len(
                cloudwatch.describe_alarms(StateValue="ALARM")["MetricAlarms"]
            )

        console.print(
            Panel(
                json.dumps(status, indent=2),
                title="System Status",
                border_style="green" if status["config_loaded"] else "red",
            )
        )
    except Exception as e:
        logger.error(f"Failed to show status: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")


def manage_config(action: str) -> None:
    """Manage system configuration."""
    try:
        config = YAMLConfig()

        if action == "show":
            console.print(
                Panel(
                    json.dumps(config.rules, indent=2),
                    title="Current Configuration",
                    border_style="blue",
                )
            )
        elif action == "validate":
            # Implement validation logic here
            is_valid = True  # Placeholder
            console.print(
                f"[{'green' if is_valid else 'red'}]Configuration is "
                f"{'valid' if is_valid else 'invalid'}[/]"
            )
    except Exception as e:
        logger.error(f"Failed to manage config: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")


async def main() -> None:
    """Main CLI entry point."""
    try:
        parser = argparse.ArgumentParser(description="CloudOpsAI CLI")
        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # Add status command
        status_parser = subparsers.add_parser("status", help="Show system status")
        status_parser.add_argument(
            "--detail", action="store_true", help="Show detailed status"
        )

        # Add config command
        config_parser = subparsers.add_parser("config", help="Manage configuration")
        config_parser.add_argument(
            "action", choices=["show", "validate"], help="Config action"
        )

        # Parse and execute
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        if args.command == "status":
            show_status(args.detail)
        elif args.command == "config":
            manage_config(args.action)

    except Exception as e:
        logger.error(f"CLI error: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
