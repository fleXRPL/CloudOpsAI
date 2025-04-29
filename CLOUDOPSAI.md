# CloudOpsAI CLI

A command-line interface for interacting with the CloudOpsAI system, allowing you to monitor alerts, view incident history, and interact with the AI decision engine.

## Features

- View current CloudWatch alerts
- Review historical incident data
- Ask questions to the AI about system state
- Get time-based summaries of events
- Beautiful terminal output with rich formatting

## Installation

### Prerequisites

- Python 3.12 or higher
- AWS credentials configured
- Access to required AWS services (CloudWatch, DynamoDB, Bedrock)

### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/fleXRPL/CloudOpsAI.git
cd CloudOpsAI
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package:

```bash
pip install -e .
```

## Usage

### Basic Commands

1. View current alerts:

```bash
cloudopsai alerts
```

2. View incident history (default 24 hours):

```bash
cloudopsai incidents
```

3. View incident history for a specific time period:

```bash
cloudopsai incidents --hours 12
```

4. Ask the AI a question:

```bash
cloudopsai ask "What was the most critical incident in the last hour?"
```

### Example Questions

You can ask the AI various questions about the system, such as:

- "What was the most critical incident in the last hour?"
- "Show me all incidents related to high CPU usage"
- "What actions were taken for the last database incident?"
- "Summarize the system state for the last 3 hours"
- "What patterns do you see in the recent incidents?"

### Output Format

The CLI provides rich, formatted output:

- **Alerts**: Tabular display of current CloudWatch alarms
- **Incidents**: Chronological list of past incidents with details
- **AI Responses**: Formatted JSON responses in a panel

## Configuration

The CLI uses the following AWS services:

- CloudWatch for alert monitoring
- DynamoDB for incident history
- Bedrock for AI decision making

Ensure your AWS credentials have access to these services and are properly configured in your environment.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black ai_noc/ tests/

# Sort imports
isort ai_noc/ tests/

# Lint code
flake8 ai_noc/ tests/

# Type checking
mypy ai_noc/ tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:

1. Check the [documentation](https://github.com/fleXRPL/CloudOpsAI/wiki)
2. Open an [issue](https://github.com/fleXRPL/CloudOpsAI/issues)
3. Join our [Discussions](https://github.com/fleXRPL/CloudOpsAI/discussions)
