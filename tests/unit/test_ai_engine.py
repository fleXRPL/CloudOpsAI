from unittest.mock import Mock, patch

import boto3
import pytest

from ai_noc.ai_engine import AIDecisionEngine


@pytest.fixture
def mock_bedrock() -> Mock:
    with patch("boto3.client") as mock_client:
        yield mock_client.return_value


@pytest.fixture
def mock_dynamodb() -> Mock:
    with patch("boto3.resource") as mock_resource:
        mock_table = Mock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
async def ai_engine(mock_bedrock, mock_dynamodb) -> AIDecisionEngine:
    return AIDecisionEngine()


@pytest.mark.asyncio
async def test_evaluate_high_cpu_incident(
    ai_engine: AIDecisionEngine, mock_bedrock: Mock, mock_dynamodb: Mock
) -> None:
    # Setup
    alarm_data = {
        "detail": {
            "alarmName": "HighCPU",
            "state": {"value": "ALARM"},
            "configuration": {
                "metrics": [{"metricName": "CPUUtilization", "namespace": "AWS/EC2"}]
            },
        }
    }
    rules = [{"name": "HighCPU_Remediation"}]

    # Mock DynamoDB response
    mock_dynamodb.query.return_value = {
        "Items": [{"timestamp": "2024-01-01T00:00:00Z", "action": "restart"}]
    }

    # Mock Bedrock response
    mock_bedrock.invoke_model.return_value = {
        "body": b'{"decision": "remediate", "actions": ["restart"]}'
    }

    # Execute
    result = await ai_engine.evaluate(alarm_data, rules)

    # Assert
    assert result["decision"] == "remediate"
    assert "actions" in result
    assert isinstance(result["actions"], list)
    mock_bedrock.invoke_model.assert_called_once()
    mock_dynamodb.query.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_with_no_action_needed(
    ai_engine: AIDecisionEngine, mock_bedrock: Mock, mock_dynamodb: Mock
) -> None:
    # Setup test for non-critical scenario
    alarm_data = {
        "detail": {
            "alarmName": "LowCPU",
            "state": {"value": "OK"},
            "configuration": {
                "metrics": [{"metricName": "CPUUtilization", "namespace": "AWS/EC2"}]
            },
        }
    }
    rules = [{"name": "LowCPU_NoAction"}]

    # Mock DynamoDB response
    mock_dynamodb.query.return_value = {"Items": []}

    # Mock Bedrock response
    mock_bedrock.invoke_model.return_value = {
        "body": b'{"decision": "no_action", "actions": []}'
    }

    # Execute
    result = await ai_engine.evaluate(alarm_data, rules)

    # Assert
    assert result["decision"] == "no_action"
    assert "actions" in result
    assert isinstance(result["actions"], list)
    assert len(result["actions"]) == 0
    mock_bedrock.invoke_model.assert_called_once()
    mock_dynamodb.query.assert_called_once()
