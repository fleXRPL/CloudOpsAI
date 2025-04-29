"""
Metric Analysis module.

This module handles the analysis of CloudWatch metrics, providing insights
and trend detection for incident investigation.
"""

import logging
import statistics
from datetime import timedelta
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .ai_engine import AIDecisionEngine
from .utils import format_timestamp, get_utc_now

logger = logging.getLogger(__name__)


class MetricAnalyzer:
    """
    Analyzes CloudWatch metrics for anomalies.

    This class:
    1. Monitors key metrics across services
    2. Detects anomalies using statistical analysis
    3. Provides early warning of potential problems
    """

    def __init__(self, q_app_id: Optional[str] = None):
        """
        Initialize the analyzer with required clients.

        Args:
            q_app_id (str, optional): Amazon Q application ID. If not provided,
                                    will be read from environment variable Q_APP_ID.
        """
        try:
            self.ai_engine = AIDecisionEngine(q_app_id=q_app_id)
            self.cloudwatch = boto3.client("cloudwatch")
            self.dynamodb = boto3.resource("dynamodb")
            self.metrics_table = self.dynamodb.Table("NOCMetrics")

            # Define key metrics to monitor for each service
            self.key_metrics = {
                "EC2": ["CPUUtilization", "MemoryUtilization", "DiskSpaceUtilization"],
                "RDS": ["CPUUtilization", "FreeStorageSpace", "DatabaseConnections"],
                "Lambda": ["Duration", "Errors", "Throttles"],
                "S3": ["BucketSizeBytes", "NumberOfObjects"],
            }
        except ClientError as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            raise

    async def analyze_metrics(
        self, service: str, metric_name: str, period: int = 3600
    ) -> Dict[str, Any]:
        """
        Analyze metrics for a specific service and metric.

        Args:
            service (str): AWS service name (e.g., 'EC2', 'RDS')
            metric_name (str): Name of the metric to analyze
            period (int): Time period in seconds to analyze

        Returns:
            Dict[str, Any]: Dict containing analysis results
        """
        try:
            # Validate inputs
            if not service or not metric_name:
                raise ValueError("Service and metric name are required")
            if period <= 0:
                raise ValueError("Period must be positive")

            # Get metric data
            metric_data = await self._get_metric_data(service, metric_name, period)

            if not metric_data:
                logger.warning(f"No metric data found for {service}/{metric_name}")
                return {
                    "service": service,
                    "metric": metric_name,
                    "anomalies": [],
                    "timestamp": format_timestamp(),
                    "status": "success",
                }

            # Detect anomalies
            anomalies = self._detect_anomalies(metric_data)

            # Get AI insights if anomalies found
            insights = {}
            if anomalies:
                insights = await self._get_ai_insights(metric_data, anomalies)

            return {
                "service": service,
                "metric": metric_name,
                "anomalies": anomalies,
                "insights": insights,
                "timestamp": format_timestamp(),
                "status": "success",
            }

        except Exception as e:
            logger.error(
                f"Error analyzing metrics for {service}/{metric_name}: {str(e)}",
                exc_info=True,
            )
            return {
                "service": service,
                "metric": metric_name,
                "error": str(e),
                "timestamp": format_timestamp(),
                "status": "error",
            }

    async def _get_metric_data(
        self, service: str, metric_name: str, period: int
    ) -> List[Dict[str, Any]]:
        """
        Get metric data from CloudWatch.

        Args:
            service (str): AWS service name
            metric_name (str): Name of the metric
            period (int): Time period in seconds

        Returns:
            List[Dict[str, Any]]: List of metric data points
        """
        try:
            end_time = get_utc_now()
            start_time = end_time - timedelta(seconds=period)

            response = self.cloudwatch.get_metric_statistics(
                Namespace=f"AWS/{service}",
                MetricName=metric_name,
                Dimensions=[],  # Will be populated based on service
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5-minute intervals
                Statistics=["Average"],
            )

            return response.get("Datapoints", [])

        except ClientError as e:
            logger.error(
                f"Error getting metric data for {service}/{metric_name}: {str(e)}",
                exc_info=True,
            )
            return []

    def _detect_anomalies(
        self, metric_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metric data using simple statistical analysis.

        Args:
            metric_data (List[Dict[str, Any]]): List of metric data points

        Returns:
            List[Dict[str, Any]]: List of detected anomalies
        """
        try:
            if not metric_data:
                return []

            # Extract values
            values = [point["Average"] for point in metric_data]

            # Calculate statistics using standard library
            try:
                mean = statistics.mean(values)
                std = statistics.stdev(values) if len(values) > 1 else 0
            except statistics.StatisticsError:
                return []

            if std == 0:  # No variation in data
                return []

            # Define anomaly threshold (3 standard deviations)
            threshold = 3 * std

            # Detect anomalies
            anomalies = []
            for point in metric_data:
                if abs(point["Average"] - mean) > threshold:
                    anomalies.append(
                        {
                            "timestamp": point["Timestamp"].isoformat(),
                            "value": point["Average"],
                            "deviation": abs(point["Average"] - mean) / std,
                            "threshold": threshold,
                        }
                    )

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}", exc_info=True)
            return []

    async def _get_ai_insights(
        self, metric_data: List[Dict[str, Any]], anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get AI insights about the metric data.

        Args:
            metric_data (List[Dict[str, Any]]): List of metric data points
            anomalies (List[Dict[str, Any]]): List of detected anomalies

        Returns:
            Dict[str, Any]: Dict containing AI insights
        """
        try:
            # Prepare context for AI
            context = {
                "metric_data": metric_data,
                "anomalies": anomalies,
                "timestamp": format_timestamp(),
            }

            # Get AI analysis
            return await self.ai_engine.evaluate(context, [])

        except Exception as e:
            logger.error(f"Error getting AI insights: {str(e)}", exc_info=True)
            return {}

    async def monitor_service(self, service: str) -> Dict[str, Any]:
        """
        Monitor key metrics for a service.

        Args:
            service (str): AWS service name

        Returns:
            Dict[str, Any]: Dict containing monitoring results
        """
        try:
            if service not in self.key_metrics:
                logger.warning(f"No key metrics defined for service: {service}")
                return {
                    "service": service,
                    "error": "No key metrics defined",
                    "timestamp": format_timestamp(),
                    "status": "error",
                }

            results = {}
            for metric in self.key_metrics[service]:
                results[metric] = await self.analyze_metrics(service, metric)

            return {
                "service": service,
                "metrics": results,
                "timestamp": format_timestamp(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error monitoring service {service}: {str(e)}", exc_info=True)
            return {
                "service": service,
                "error": str(e),
                "timestamp": format_timestamp(),
                "status": "error",
            }

    async def get_service_insights(self, service: str) -> List[Dict[str, Any]]:
        """Get metric insights for a specific AWS service."""
        try:
            # Get metrics for service
            metrics = await self._get_service_metrics(service)

            # Get AI analysis
            analysis = await self.ai_engine.evaluate(
                {"service": service, "metrics": metrics},
                [],  # No predefined rules for metric analysis
            )

            return [
                {
                    "service": service,
                    "metrics": metrics,
                    "analysis": analysis,
                    "timestamp": format_timestamp(),
                }
            ]
        except Exception as e:
            logger.error(f"Failed to get service insights: {str(e)}")
            return []

    async def _get_service_metrics(self, service: str) -> List[Dict[str, Any]]:
        """
        Get metrics for a specific AWS service.

        Args:
            service (str): AWS service name (e.g., 'EC2', 'RDS')

        Returns:
            List[Dict[str, Any]]: List of metric data for the service
        """
        try:
            if service not in self.key_metrics:
                logger.warning(f"No key metrics defined for service: {service}")
                return []

            metrics = []
            for metric_name in self.key_metrics[service]:
                metric_data = await self._get_metric_data(service, metric_name, 3600)
                if metric_data:
                    metrics.append(
                        {
                            "name": metric_name,
                            "data": metric_data,
                            "timestamp": format_timestamp(),
                        }
                    )

            return metrics

        except Exception as e:
            logger.error(f"Error getting metrics for service {service}: {str(e)}")
            return []
