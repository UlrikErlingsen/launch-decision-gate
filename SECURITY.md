# Security policy

## Supported version

Security fixes target the latest release on the default branch.

## Reporting

Please report a suspected vulnerability privately through GitHub's security-advisory feature when the repository is published. Do not include confidential project data in a public issue.

## Data-handling notes

GateSignal accepts `.xlsx` and `.json` project bundles only. It does not execute workbook macros. Upload size, workbook expansion, and row-count limits reduce accidental resource exhaustion. Exported text that could be interpreted as a spreadsheet formula is neutralized.

These controls do not turn GateSignal into a hardened multi-tenant service. A hosted deployment should add authentication, TLS, authorization, rate limiting, secure headers, isolated storage, dependency monitoring, logging appropriate to the data classification, and a documented deletion policy.

