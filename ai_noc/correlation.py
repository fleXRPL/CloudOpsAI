"""
Alert Correlation module.

This module handles the correlation of related alerts to identify incident patterns
and root causes.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .ai_engine import AIDecisionEngine

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Get current UTC time with timezone information."""
    return datetime.now(timezone.utc)


class AlertCorrelator:
    """
    Correlates multiple alerts and determines root causes.

    This class:
    1. Groups related alerts based on timing and resource relationships
    2. Analyzes patterns across alerts
    3. Determines root causes using AI
    4. Suggests remediation steps
    """

    def __init__(self, q_app_id: Optional[str] = None):
        """
        Initialize the correlator with required clients.

        Args:
            q_app_id (str, optional): Amazon Q application ID. If not provided,
                                    will be read from environment variable Q_APP_ID.
        """
        try:
            self.ai_engine = AIDecisionEngine(q_app_id=q_app_id)
            self.cloudwatch = boto3.client("cloudwatch")
            self.dynamodb = boto3.resource("dynamodb")
            self.incidents_table = self.dynamodb.Table("NOCIncidents")
        except ClientError as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    async def correlate_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Correlate multiple alerts and determine root cause.

        Args:
            alerts (List[Dict[str, Any]]): List of CloudWatch alarms

        Returns:
            Dict[str, Any]: Dict containing correlation results and root cause analysis
        """
        try:
            if not alerts:
                return {
                    "correlation_time": get_utc_now().isoformat(),
                    "groups": [],
                    "status": "success",
                }

            # Group related alerts
            alert_groups = await self._group_alerts(alerts)

            # Analyze each group
            results = []
            for group in alert_groups:
                try:
                    # Get historical context for the entire group
                    history = await self._get_historical_context(group)

                    # Analyze with AI using the group and history
                    analysis = await self._analyze_with_ai(group, history)

                    results.append({
                        "alerts": group,
                        "root_cause": analysis.get("root_cause", "unknown"),
                        "confidence": analysis.get("confidence", 0.0),
                        "recommended_actions": analysis.get("actions", []),
                    })
                except Exception as e:
                    logger.error(f"Failed to analyze alert group: {str(e)}")
                    results.append({"alerts": group, "error": str(e), "status": "error"})

            return {
                "correlation_time": get_utc_now().isoformat(),
                "groups": results,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Failed to correlate alerts: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _group_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group related alerts together based on common attributes."""
        groups = []
        current_group: List[Dict[str, Any]] = []

        # Sort alerts by timestamp
        sorted_alerts = sorted(alerts, key=lambda x: x.get("StateUpdatedTimestamp", ""))

        for alert in sorted_alerts:
            if not current_group:
                current_group.append(alert)
            else:
                # Check if this alert is related to the current group
                if self._are_alerts_related(current_group[-1], alert):
                    current_group.append(alert)
                else:
                    groups.append(current_group)
                    current_group = [alert]

        if current_group:
            groups.append(current_group)

        return groups

    def _are_alerts_related(
        self, alert1: Dict[str, Any], alert2: Dict[str, Any]
    ) -> bool:
        """
        Determine if two alerts are related based on timing and resources.

        Args:
            alert1 (Dict[str, Any]): First CloudWatch alarm
            alert2 (Dict[str, Any]): Second CloudWatch alarm

        Returns:
            bool: True if alerts are related, False otherwise
        """
        try:
            # Check timing (within 5 minutes)
            time1 = alert1.get(
                "StateUpdatedTimestamp", datetime.min.replace(tzinfo=timezone.utc)
            )
            time2 = alert2.get(
                "StateUpdatedTimestamp", datetime.min.replace(tzinfo=timezone.utc)
            )
            time_diff = abs((time1 - time2).total_seconds())
            if time_diff > 300:  # 5 minutes
                return False

            # Check resource relationships
            return alert1.get("Namespace") == alert2.get(
                "Namespace"
            ) or self._check_resource_relationship(alert1, alert2)
        except Exception as e:
            logger.error(f"Failed to check alert relationship: {str(e)}")
            return False

    def _check_resource_relationship(
        self, alert1: Dict[str, Any], alert2: Dict[str, Any]
    ) -> bool:
        """
        Check if resources in alerts are related (e.g., EC2 instance and its EBS volume).

        Args:
            alert1 (Dict[str, Any]): First CloudWatch alarm
            alert2 (Dict[str, Any]): Second CloudWatch alarm

        Returns:
            bool: True if resources are related, False otherwise
        """
        try:
            # This is a simplified version. In production, we would:
            # 1. Use AWS Config to understand resource relationships
            # 2. Check resource tags for relationships
            # 3. Use service-specific knowledge (e.g., EC2 instance and its volumes)
            return False
        except Exception as e:
            logger.error(f"Failed to check resource relationship: {str(e)}")
            return False

    async def _get_historical_context(
        self, alert_group: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get historical context for alert group from DynamoDB.

        Args:
            alert_group (Dict[str, Any]): Group of related alerts

        Returns:
            Dict[str, Any]: Dict containing historical context
        """
        try:
            # Get incidents from the last 24 hours
            start_time = get_utc_now() - timedelta(hours=24)

            response = self.incidents_table.scan(
                FilterExpression="timestamp >= :start",
                ExpressionAttributeValues={":start": start_time.isoformat()},
            )

            return {
                "recent_incidents": response.get("Items", []),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": get_utc_now().isoformat(),
                },
            }
        except ClientError as e:
            logger.error(f"Failed to get historical context: {str(e)}")
            return {
                "recent_incidents": [],
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": get_utc_now().isoformat(),
                },
            }

    async def _analyze_with_ai(
        self, alert_group: Dict[str, Any], history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze alert group with AI to determine root cause and actions.

        Args:
            alert_group (Dict[str, Any]): Group of related alerts
            history (Dict[str, Any]): Historical context

        Returns:
            Dict[str, Any]: Dict containing AI analysis results
        """
        try:
            # Prepare context for AI
            context = {
                "alerts": alert_group,
                "history": history,
                "timestamp": get_utc_now().isoformat(),
            }

            # Get AI analysis
            return await self.ai_engine.evaluate(context, [])
        except Exception as e:
            logger.error(f"Failed to analyze with AI: {str(e)}")
            return {
                "root_cause": "unknown",
                "confidence": 0.0,
                "actions": [],
                "error": str(e),
            }

