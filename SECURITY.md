# Security Policy

## Reporting a vulnerability

**Do not open a public issue.** Use [Private Vulnerability Reporting](https://github.com/yeongseon/kpubdata-watch/security/advisories/new).

Please include, as far as you can:

- What an attacker can do, not only what looks wrong
- The smallest way to reproduce it
- Which commit or release you looked at

You will get an acknowledgement. If the report turns out to be a defect rather
than a vulnerability, it is moved to a normal issue and you are told so.

## What counts as a vulnerability here

KPubData Watch calls Korean public data APIs with **the project's own operating
credentials** and publishes what it observes. The things we most want to hear
about:

- **A credential appearing anywhere it is not supposed to** — Git, the database,
  an application log, incident evidence, the public API, rendered HTML, an
  exception trace or a URL in a log line.
- **A way to make Watch request a URL that is not in its configured allowlist**
  (server-side request forgery).
- **A way to make the public status show something the evidence does not support**,
  such as marking a dataset healthy or critical without an observation behind it.

## Requirements the code must meet

These come from the PRD (§61–§63) and are part of the MVP's definition of done.

### Credentials (PRD §61)

Public Status credentials are the project's operating credentials, for example:

```text
DATA_GO_KR_API_KEY
KOSIS_API_KEY
...
```

They are kept in:

```text
Environment
or
Secret Manager
```

They are never stored in:

```text
Git

Database

Application Logs

Incident Evidence

Public API

Frontend HTML
```

### Secret redaction (PRD §62)

These patterns are always redacted:

```text
serviceKey
apiKey
apikey
Authorization
token
secret
```

In particular, a URL such as

```text
?serviceKey=xxxxx
```

must never survive into an exception or a log line.

### Security requirements (PRD §63)

MVP P0:

```text
No arbitrary user URL probe

Configured endpoint allowlist

Secret redaction

Request timeout

Response size limit

Outbound rate limit

HTML escaping

Database migration control

Dependency scanning

No credentials in exception trace

No raw credentials in DB
```

External users can never enter an arbitrary URL. This removes server-side request
forgery and abuse from the MVP's scope.

Full raw API responses are not stored long-term either
([docs/decisions/0006-raw-response-storage.md](docs/decisions/0006-raw-response-storage.md)).

## What does not count

- A missing hardening measure with no reachable consequence
- Denial of service by simply sending a lot of requests
- Outdated dependencies with no exploitable path in this code — open a normal issue
- Findings from a scanner, pasted without a reachable path

## Supported versions

Nothing has been released yet. Report against a commit SHA.

## Known limits, stated deliberately

- There is no implementation yet; the requirements above are what the code will
  be held to.
- Some documentation is Korean. A report in either Korean or English is fine.
