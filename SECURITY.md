# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ |
| 1.0.0-rc* | Best-effort |
| < 1.0   | ❌ |

## Reporting a vulnerability

Please **do not** open a public issue for security-sensitive reports.

1. Email or privately message the maintainer via GitHub Security Advisories if enabled.
2. Include EvoNAS version, reproduction steps, and impact assessment.
3. Allow reasonable time for a fix before public disclosure.

## Scope notes

EvoNAS v1.0.0 is a **local / research-oriented** platform. It does **not** ship production auth, multi-tenant isolation, or hardened cloud defaults. Treat network exposure of the API/dashboard as a lab risk: bind to localhost unless you add your own reverse-proxy auth.

## Supply chain

Prefer installing from the tagged release `v1.0.0` and verifying `reproducibility/` manifests when citing scientific results.
