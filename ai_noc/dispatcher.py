"""
Action Dispatcher module.

This module handles the execution of remediation actions, including AWS service
interactions, notifications, and ticket creation in external systems.
"""

import json
import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ActionDispatcher:
    """
    Action dispatcher for executing remediation steps.

    Handles the execution of various types of actions including AWS service
    remediation, notifications, and external system integrations.

    Attributes:
        ssm (boto3.client): AWS Systems Manager client for automation
        sns (boto3.client): AWS SNS client for notifications
        lambda_client (boto3.client): AWS Lambda client for function invocation
    """

    def __init__(self):
        """Initialize the action dispatcher with AWS clients."""
        try:
            self.ssm = boto3.client("ssm")
            self.sns = boto3.client("sns")
            self.lambda_client = boto3.client("lambda")
        except ClientError as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    async def execute_actions(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute remediation actions based on AI decision.

        Args:
            decision (Dict[str, Any]): AI decision containing actions to execute

        Returns:
            Dict[str, Any]: Results of action execution including success/failure status
        """
        try:
            if "actions" not in decision:
                raise ValueError("Decision missing 'actions' field")

            results = []
            for action in decision["actions"]:
                result = await self._process_action(action)
                results.append(result)

            return {
                "decision_id": decision.get("id", "unknown"),
                "action_results": results,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Failed to execute actions: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _process_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single action based on its type."""
        if "type" not in action:
            logger.warning(f"Action missing 'type' field: {action}")
            return {"status": "error", "error": "Missing action type"}

        try:
            action_handlers = {
                "remediate": self._execute_remediation,
                "notify": self._send_notification,
                "ticket": self._create_ticket,
            }

            handler = action_handlers.get(action["type"])
            if handler:
                return await handler(action)

            logger.warning(f"Unknown action type: {action['type']}")
            return {
                "status": "error",
                "error": f"Unknown action type: {action['type']}",
            }
        except Exception as e:
            logger.error(f"Failed to execute action {action['type']}: {str(e)}")
            return {"status": "error", "error": str(e), "action": action}

    async def _execute_remediation(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AWS service remediation actions.

        Args:
            action (Dict[str, Any]): Remediation action details

        Returns:
            Dict[str, Any]: Result of remediation execution
        """
        try:
            if "ssm_document" in action:
                response = self.ssm.start_automation_execution(
                    DocumentName=action["ssm_document"],
                    Parameters=action.get("parameters", {}),
                )
                return {
                    "status": "success",
                    "execution_id": response["AutomationExecutionId"],
                }
            elif "lambda_function" in action:
                response = self.lambda_client.invoke(
                    FunctionName=action["lambda_function"],
                    Payload=json.dumps(action.get("payload", {})),
                )
                return {
                    "status": "success",
                    "response": json.loads(response["Payload"].read()),
                }
            else:
                logger.warning(
                    f"No supported remediation type found in action: {action}"
                )
                return {
                    "status": "error",
                    "error": "No supported remediation type found",
                }
        except ClientError as e:
            logger.error(f"Failed to execute remediation: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _send_notification(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification through configured channels.

        Args:
            action (Dict[str, Any]): Notification action details

        Returns:
            Dict[str, Any]: Result of notification sending
        """
        try:
            if "topic_arn" in action:
                response = self.sns.publish(
                    TopicArn=action["topic_arn"],
                    Message=action.get("message", ""),
                    Subject=action.get("subject", ""),
                )
                return {"status": "success", "message_id": response["MessageId"]}
            else:
                logger.warning(
                    f"No supported notification type found in action: {action}"
                )
                return {
                    "status": "error",
                    "error": "No supported notification type found",
                }
        except ClientError as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _create_ticket(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create ticket in external system.

        Args:
            action (Dict[str, Any]): Ticket creation action details

        Returns:
            Dict[str, Any]: Result of ticket creation
        """
        # Implement ticket creation logic here
        # This is a placeholder - implement actual ticket creation
        return {"status": "error", "error": "Ticket creation not implemented"}
