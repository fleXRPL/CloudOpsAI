"""
AI NOC Agent main module.

This module implements the core NOC Agent functionality, orchestrating the processing
of CloudWatch events through configuration parsing, AI decision making, and action dispatching.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .ai_engine import AIDecisionEngine
from .config import YAMLConfig
from .correlation import AlertCorrelator
from .dispatcher import ActionDispatcher
from .metrics import MetricAnalyzer
from .notifications import NotificationManager
from .utils import format_timestamp, safe_get

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class NOCAgent:
    """
    Main NOC Agent class that processes and responds to CloudWatch events.

    This class orchestrates the entire event processing pipeline, from parsing
    CloudWatch alerts to executing remediation actions based on AI decisions.

    Attributes:
        config (YAMLConfig): Configuration manager for YAML-based rules
        ai_engine (AIDecisionEngine): AI decision making component
        dispatcher (ActionDispatcher): Action execution component
        correlator (AlertCorrelator): Alert correlation component
        notifier (NotificationManager): Notification management component
        metric_analyzer (MetricAnalyzer): Metric analysis component
    """

    def __init__(self, q_app_id: Optional[str] = None):
        """
        Initialize NOC Agent with its core components.

        Args:
            q_app_id (str, optional): Amazon Q application ID. If not provided,
                                    will be read from environment variable Q_APP_ID.
        """
        try:
            self.config = YAMLConfig()
            self.ai_engine = AIDecisionEngine(q_app_id=q_app_id)
            self.dispatcher = ActionDispatcher()
            self.correlator = AlertCorrelator()
            self.notifier = NotificationManager()
            self.metric_analyzer = MetricAnalyzer()
        except Exception as e:
            logger.error(f"Failed to initialize NOC Agent: {str(e)}")
            raise

    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming CloudWatch events and execute appropriate actions.

        Args:
            event (Dict[str, Any]): CloudWatch event data containing alert information

        Returns:
            Dict[str, Any]: Result of action execution including decision ID and action results
        """
        try:
            # Validate event structure
            if "detail" not in event:
                raise ValueError("Invalid event structure: missing 'detail' field")

            # Get all current alarms
            current_alarms = await self._get_current_alarms()

            # Correlate alerts
            correlation_result = await self.correlator.correlate_alerts(current_alarms)

            # For each correlated group
            results = []
            for group in correlation_result["groups"]:
                # Get metric analysis for affected services
                metric_insights = await self._get_metric_insights(group)

                # Load matching rules
                rules = self.config.get_matching_rules(group["alerts"])

                # Get AI decision with metric insights
                decision = await self.ai_engine.evaluate(
                    {**group, "metric_insights": metric_insights}, rules
                )

                # Execute actions
                action_result = await self.dispatcher.execute_actions(decision)

                # Send notifications
                notification_result = await self.notifier.send_notification(
                    incident={
                        "id": decision["id"],
                        "type": group["root_cause"],
                        "description": f"Root cause: {group['root_cause']}",
                        "severity": safe_get(decision, "severity", "medium"),
                        "alerts": group["alerts"],
                        "actions": action_result["action_results"],
                        "metric_insights": metric_insights,
                        "timestamp": format_timestamp(),
                    },
                    channels=self._get_notification_channels(decision),
                    severity=safe_get(decision, "severity", "medium"),
                )

                results.append(
                    {
                        "correlation": group,
                        "metric_insights": metric_insights,
                        "decision": decision,
                        "actions": action_result,
                        "notifications": notification_result,
                        "timestamp": format_timestamp(),
                    }
                )

            return {
                "status": "success",
                "results": results,
                "timestamp": format_timestamp(),
            }

        except Exception as e:
            logger.error(f"Error processing event: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "timestamp": format_timestamp()}

    async def _get_current_alarms(self) -> List[Dict[str, Any]]:
        """Get all currently active CloudWatch alarms."""
        try:
            cloudwatch = boto3.client("cloudwatch")
            response = cloudwatch.describe_alarms(StateValue="ALARM")
            return safe_get(response, "MetricAlarms", [])
        except ClientError as e:
            logger.error(f"Failed to get current alarms: {str(e)}")
            return []

    async def _get_metric_insights(self, alert_group: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get metric insights for services affected by alerts.

        Args:
            alert_group (Dict[str, Any]): Group of related alerts

        Returns:
            Dict[str, Any]: Dict containing metric insights
        """
        try:
            # Extract affected services from alerts
            services = set()
            for alert in alert_group["alerts"]:
                if "Namespace" in alert:
                    service = alert["Namespace"].replace("AWS/", "")
                    services.add(service)

            # Get insights for each service
            insights = {}
            for service in services:
                insights[service] = await self.metric_analyzer.get_service_insights(
                    service
                )

            return insights
        except Exception as e:
            logger.error(f"Failed to get metric insights: {str(e)}")
            return {}

    def _get_notification_channels(self, decision: Dict[str, Any]) -> List[str]:
        """
        Determine which notification channels to use based on decision.

        Args:
            decision (Dict[str, Any]): AI decision containing severity and other factors

        Returns:
            List[str]: List of notification channels to use
        """
        severity = safe_get(decision, "severity", "medium")
        channels = ["teams"]  # Always notify Teams

        if severity in ["high", "critical"]:
            channels.extend(["slack", "pagerduty"])

        if severity == "critical":
            channels.append("email")

        return channels


async def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for processing CloudWatch events.

    Args:
        event (Dict[str, Any]): CloudWatch event data
        context (Any): Lambda context

    Returns:
        Dict[str, Any]: Dict containing processing results
    """
    try:
        logger.info(f"Processing event: {json.dumps(event)}")
        agent = NOCAgent()
        result = await agent.process_event(event)

        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "timestamp": format_timestamp()}),
        }
