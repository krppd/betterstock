# Security Policy

## Supported Versions

Only the latest release of the free edition is actively supported. Security fixes are shipped in subsequent releases; there are no long-term support (LTS) branches for this edition.

## Reporting a Vulnerability

Please **do not open a public issue** to report a security vulnerability.

Instead, submit your report privately through GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) feature on this repository. If private reporting is unavailable to you, open a minimal issue stating only that you wish to report a security concern privately—without including any technical details—so we can coordinate an alternative contact method.

All reports are reviewed and acknowledged. Once a valid vulnerability is patched in a new release, a security advisory will be published crediting the reporter, unless you prefer to remain anonymous.

## Data Handling & Privacy

BetterStock operates entirely locally on the host machine. It requires no remote server, user account, or license activation.

- **Local Storage**: The database is a single SQLite file stored in the per-user data directory (`%APPDATA%\BetterStock` on Windows, or `$XDG_DATA_HOME/BetterStock` / `~/.local/share/BetterStock` on other platforms).
- **Credential Security**: Passwords are hashed using `bcrypt` and are never stored in plaintext.
- **Backups**: Database backups are local copies stored on the same machine.

### Network Activity

BetterStock makes no outbound network requests by default. Network activity only occurs when explicitly initiated by the user:

- **Product Photos**: When enabled in **Settings**, the photo search queries the Open Food Facts API. This feature is disabled by default; while turned off, the application makes no external queries.
- **External Links**: Links in **Settings** open the official project website in the system's default browser.

## Out of Scope

The following are outside the scope of this security policy:

- Running the application on an untrusted or compromised machine you do not control.
- The `betterstock.tech` website, which is maintained outside of this repository.
- The commercial/paid edition, which is maintained outside of this repository.
