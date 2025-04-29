"""
Notification Manager module.

This module handles sending notifications through various channels (Slack, Teams, Email, etc.)
and manages notification preferences and throttling.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import aiohttp
import boto3
from botocore.exceptions import ClientError

from .config import YAMLConfig

logger = logging.getLogger(__name__)


class NotificationManager:
    """Notification manager for sending alerts through various channels."""

    def __init__(self):
        """Initialize notification clients."""
        try:
            self.sns = boto3.client("sns")
            self.ses = boto3.client("ses")
            self.lambda_client = boto3.client("lambda")
            self.config = YAMLConfig()
            self.dynamodb = boto3.resource("dynamodb")
            self.notifications_table = self.dynamodb.Table("NOCNotifications")
        except ClientError as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    async def send_notification(
        self, incident: Dict[str, Any], channels: List[str], severity: str = "medium"
    ) -> Dict[str, Any]:
        """Send notifications through specified channels."""
        try:
            results = []
            for channel in channels:
                result = await self._send_to_channel(channel, incident, severity)
                results.append(result)

            return {
                "incident_id": incident.get("id", "unknown"),
                "notification_results": results,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Failed to send notifications: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_to_channel(
        self, channel: str, incident: Dict[str, Any], severity: str
    ) -> Dict[str, Any]:
        """Send notification to a specific channel."""
        channel_handlers = {
            "slack": self._send_slack_notification,
            "teams": self._send_teams_notification,
            "email": self._send_email_notification,
            "pagerduty": self._send_pagerduty_notification,
        }

        handler = channel_handlers.get(channel)
        if not handler:
            logger.warning(f"Unknown notification channel: {channel}")
            return {"status": "error", "error": f"Unknown channel: {channel}"}

        try:
            return await handler(incident, severity)
        except Exception as e:
            logger.error(f"Failed to send {channel} notification: {str(e)}")
            return {"status": "error", "error": str(e), "channel": channel}

    async def _send_slack_notification(
        self, incident: Dict[str, Any], severity: str
    ) -> Dict[str, Any]:
        """Send notification to Slack."""
        try:
            # Get Slack webhook URL from config
            webhook_url = self.config.get_slack_webhook_url()
            if not webhook_url:
                raise ValueError("Slack webhook URL not configured")

            # Prepare Slack message
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": incident["title"]},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": incident["description"]},
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:*\n{severity.upper()}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Status:*\n{incident['status']}",
                            },
                        ],
                    },
                ]
            }

            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    return {
                        "status": response.status,
                        "response": await response.text(),
                    }
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_teams_notification(
        self, incident: Dict[str, Any], severity: str
    ) -> Dict[str, Any]:
        """Send notification to Microsoft Teams."""
        try:
            # Get Teams webhook URL from config
            webhook_url = self.config.get_teams_webhook_url()
            if not webhook_url:
                raise ValueError("Teams webhook URL not configured")

            # Prepare Teams message card
            message = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "type": "AdaptiveCard",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "text": incident["title"],
                                    "weight": "bolder",
                                    "size": "large",
                                },
                                {
                                    "type": "TextBlock",
                                    "text": incident["description"],
                                    "wrap": True,
                                },
                                {
                                    "type": "FactSet",
                                    "facts": [
                                        {
                                            "title": "Severity",
                                            "value": severity.upper(),
                                        },
                                        {
                                            "title": "Status",
                                            "value": incident["status"],
                                        },
                                    ],
                                },
                            ],
                            "actions": [
                                {
                                    "type": "Action.OpenUrl",
                                    "title": "View Details",
                                    "url": (
                                        "https://console.aws.amazon.com/cloudwatch/home"
                                        f"?region=us-east-1#alarmsV2:alarm/{incident['id']}"
                                    ),
                                }
                            ],
                        },
                    }
                ],
            }

            # Send to Teams
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    return {
                        "status": response.status,
                        "response": await response.text(),
                    }
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_email_notification(
        self, incident: Dict[str, Any], severity: str
    ) -> Dict[str, Any]:
        """Send notification via email using SES."""
        try:
            # Get email configuration
            from_email = self.config.get_email_from()
            to_emails = self.config.get_email_recipients()

            if not from_email or not to_emails:
                raise ValueError("Email configuration not complete")

            # Prepare email content
            subject = f"[{severity.upper()}] {incident['title']}"

            # Create HTML email with rich content
            html_content = f"""
            <h1>{incident['title']}</h1>
            <p>{incident['description']}</p>
            <h2>Details</h2>
            <ul>
                <li><strong>Severity:</strong> {severity.upper()}</li>
                <li><strong>Status:</strong> {incident['status']}</li>
                <li><strong>Incident ID:</strong> {incident['id']}</li>
            </ul>
            """

            # Send email
            response = self.ses.send_email(
                Source=from_email,
                Destination={"ToAddresses": to_emails},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": html_content}},
                },
            )

            return {"status": "success", "message_id": response["MessageId"]}
        except ClientError as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_pagerduty_notification(
        self, incident: Dict[str, Any], severity: str
    ) -> Dict[str, Any]:
        """Send notification to PagerDuty."""
        try:
            # Get PagerDuty configuration
            api_key = self.config.get_pagerduty_key()
            if not api_key:
                raise ValueError("PagerDuty API key not configured")

            # Prepare PagerDuty incident
            incident_data = {
                "incident": {
                    "type": "incident",
                    "title": incident["title"],
                    "description": incident["description"],
                    "urgency": "high" if severity in ["high", "critical"] else "low",
                    "body": {
                        "type": "incident_body",
                        "details": incident.get("historical_context", {}),
                    },
                }
            }

            # Send to PagerDuty
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.pagerduty.com/incidents",
                    headers={
                        "Authorization": f"Token token={api_key}",
                        "Content-Type": "application/json",
                    },
                    json=incident_data,
                ) as response:
                    return {
                        "status": response.status,
                        "response": await response.text(),
                    }
        except Exception as e:
            logger.error(f"Failed to send PagerDuty notification: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _get_historical_context(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical context for incident."""
        try:
            # Get incidents from the last 24 hours
            start_time = datetime.utcnow() - timedelta(hours=24)

            response = self.notifications_table.scan(
                FilterExpression="timestamp >= :start",
                ExpressionAttributeValues={":start": start_time.isoformat()},
            )

            return {
                "recent_incidents": response.get("Items", []),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": datetime.utcnow().isoformat(),
                },
            }
        except ClientError as e:
            logger.error(f"Failed to get historical context: {str(e)}")
            return {
                "recent_incidents": [],
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": datetime.utcnow().isoformat(),
                },
            }

    async def _record_notification(
        self, incident: Dict[str, Any], channels: List[str], results: Dict[str, Any]
    ) -> None:
        """Record notification in DynamoDB."""
        try:
            self.notifications_table.put_item(
                Item={
                    "incident_id": incident.get("id", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                    "channels": channels,
                    "results": results,
                    "severity": incident.get("severity", "medium"),
                }
            )
        except ClientError as e:
            logger.error(f"Failed to record notification: {str(e)}")
