"""
AI Engine utilizing AWS Bedrock and Amazon Q.
"""

import json
import logging
import os
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AIDecisionEngine:
    """
    AI-powered decision engine for incident analysis and response.

    Uses Amazon Bedrock and Amazon Q to analyze incidents, evaluate their severity,
    and suggest appropriate remediation actions based on historical data and context.

    Attributes:
        bedrock (boto3.client): AWS Bedrock client for AI services
        q (boto3.client): Amazon Q client for operational knowledge
        dynamodb (boto3.resource): AWS DynamoDB resource for incident history
        incidents_table (Table): DynamoDB table for storing incident data
    """

    def __init__(self, q_app_id: str | None = None) -> None:
        """
        Initialize the AI Decision Engine.

        Args:
            q_app_id (str | None, optional): Amazon Q application ID. If not provided,
                                    will be read from environment variable Q_APP_ID.
        """
        try:
            self.bedrock = boto3.client("bedrock-runtime")
            self.q = boto3.client("amazonq")
            self.dynamodb = boto3.resource("dynamodb")
            self.incidents_table = self.dynamodb.Table("NOCIncidents")
            self.q_app_id = q_app_id or os.environ.get("Q_APP_ID")
            if not self.q_app_id:
                raise ValueError("Amazon Q application ID not provided")
        except ClientError as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    async def evaluate(
        self, alarm_data: Dict[str, Any], rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate an incident using AI and suggest appropriate actions.

        Args:
            alarm_data (Dict[str, Any]): CloudWatch alarm data
            rules (List[Dict[str, Any]]): List of matching remediation rules

        Returns:
            Dict[str, Any]: AI decision including recommended actions and reasoning
        """
        try:
            # Use Amazon Q for operational knowledge and documentation
            q_response = await self._query_amazon_q(alarm_data)

            # Use Bedrock for decision making
            bedrock_response = await self._get_bedrock_decision(
                alarm_data, rules, q_response
            )

            return self._combine_ai_responses(bedrock_response, q_response)
        except Exception as e:
            logger.error(f"Error in AI evaluation: {str(e)}")
            return {"error": str(e), "status": "error"}

    async def _query_amazon_q(self, alarm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query Amazon Q for operational knowledge.

        Args:
            alarm_data (Dict[str, Any]): CloudWatch alarm data

        Returns:
            Dict[str, Any]: Response from Amazon Q
        """
        try:
            response = self.q.query(
                applicationId=self.q_app_id,
                query=f"What are common solutions for {alarm_data['alarmName']} alerts?",
            )
            return dict(response)
        except ClientError as e:
            logger.error(f"Amazon Q query failed: {str(e)}")
            return {"error": str(e)}

    async def _get_bedrock_decision(
        self,
        alarm_data: Dict[str, Any],
        rules: List[Dict[str, Any]],
        q_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get decision from Bedrock with context from Amazon Q.

        Args:
            alarm_data (Dict[str, Any]): CloudWatch alarm data
            rules (List[Dict[str, Any]]): List of matching remediation rules
            q_context (Dict[str, Any]): Context from Amazon Q

        Returns:
            Dict[str, Any]: Response from Bedrock
        """
        try:
            prompt = self._build_prompt(alarm_data, rules, q_context)
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-v2", body=prompt
            )
            return dict(response)
        except ClientError as e:
            logger.error(f"Bedrock invocation failed: {str(e)}")
            return {"error": str(e)}

    def _build_prompt(
        self,
        alarm_data: Dict[str, Any],
        rules: List[Dict[str, Any]],
        q_context: Dict[str, Any],
    ) -> str:
        """
        Build the prompt for the AI model based on alarm data, rules, and context from Amazon Q.

        Args:
            alarm_data (Dict[str, Any]): CloudWatch alarm data
            rules (List[Dict[str, Any]]): List of matching remediation rules
            q_context (Dict[str, Any]): Context from Amazon Q

        Returns:
            str: Formatted prompt for the AI model
        """
        return f"""Given the following alert:
{json.dumps(alarm_data, indent=2)}

And these matching rules:
{json.dumps(rules, indent=2)}

With this context from Amazon Q:
{json.dumps(q_context, indent=2)}

Determine:
1. Is this a real incident requiring action?
2. What specific remediation steps should be taken?
3. Should we notify anyone?

Return your response as JSON."""

    def _combine_ai_responses(
        self, bedrock_response: Dict[str, Any], q_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine responses from Bedrock and Amazon Q.

        Args:
            bedrock_response (Dict[str, Any]): Response from Bedrock
            q_response (Dict[str, Any]): Response from Amazon Q

        Returns:
            Dict[str, Any]: Combined AI decision
        """
        return {
            "bedrock_decision": bedrock_response,
            "q_context": q_response,
            "status": "success",
        }
