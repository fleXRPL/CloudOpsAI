# Security Policy

## Supported Versions

CloudOpsAI follows semantic versioning (MAJOR.MINOR.PATCH) and maintains security updates for the following versions:

| Version | Supported          | End of Life      |
| ------- | ------------------ | ---------------- |
| 1.0.x   | :white_check_mark: | TBD              |
| 0.2.x   | :white_check_mark: | December 2026    |
| 0.1.x   | :x:                | June 2025        |
| < 0.1   | :x:                | N/A              |

## Security Features

CloudOpsAI implements the following security measures:

- IAM roles with least privilege
- Multi-account support via AWS Organizations
- Data encryption at rest and in transit
- Regular security audits
- Compliance with AWS security best practices
- Automated security scanning via Dependabot
- SonarQube Cloud integration for code quality

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you believe you've found a security vulnerability in CloudOpsAI, please follow these steps:

1. **Do Not** disclose the vulnerability publicly
2. Email your findings to security@cloudopsai.com
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

### What to Expect

- You will receive an acknowledgment within 48 hours
- We will investigate and provide updates every 7 days
- If the vulnerability is accepted:
  - We will work on a fix
  - You will be notified when the fix is deployed
  - You will be credited in our security advisory
- If the vulnerability is declined:
  - You will receive a detailed explanation
  - You may appeal the decision

### Responsible Disclosure

We follow responsible disclosure practices:
- We will not take legal action against you for reporting vulnerabilities
- We will work with you to validate and fix the issue
- We will credit you in our security advisory
- We will not share your personal information without your permission

## Security Updates

- Critical security updates are released within 24 hours
- High severity updates are released within 7 days
- Medium severity updates are released within 30 days
- Low severity updates are included in regular releases

## Security Best Practices

When using CloudOpsAI, please follow these security best practices:

1. Keep your AWS credentials secure
2. Regularly rotate access keys
3. Use IAM roles with least privilege
4. Enable MFA for all AWS accounts
5. Monitor CloudTrail logs
6. Regularly update to the latest supported version
7. Review and audit your configuration files
8. Use encryption for sensitive data

## Security Contact

For security-related questions or concerns:
- Email: security@cloudopsai.com
- GitHub Security Advisory: [Create a security advisory](https://github.com/fleXRPL/CloudOpsAI/security/advisories/new)
- AWS Security Hub: [AWS Security Hub](https://aws.amazon.com/security-hub/)
