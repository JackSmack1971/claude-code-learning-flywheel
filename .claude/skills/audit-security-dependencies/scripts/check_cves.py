#!/usr/bin/env python3
"""
Zero-Context CVE Checker for Dependencies

Checks npm/pip packages for known CVEs using vulnerability databases.
Wraps npm audit and pip-audit with strict thresholds and clear reporting.

Usage:
    python check_cves.py --package express --severity high
    python check_cves.py --check-all --format json
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class Severity(Enum):
    """CVE severity levels."""
    CRITICAL = 4
    HIGH = 3
    MODERATE = 2
    LOW = 1
    INFO = 0

    @classmethod
    def from_string(cls, s: str) -> 'Severity':
        return cls[s.upper()]

    def __str__(self):
        return self.name.lower()


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""
    package: str
    current_version: str
    cve_id: Optional[str]
    severity: Severity
    title: str
    description: str
    fixed_version: Optional[str]
    url: Optional[str]


class PackageManager:
    """Base class for package managers."""

    def check_package(self, package_name: str) -> List[Vulnerability]:
        """Check a specific package for vulnerabilities."""
        raise NotImplementedError

    def check_all(self) -> List[Vulnerability]:
        """Check all installed packages for vulnerabilities."""
        raise NotImplementedError


class NPMChecker(PackageManager):
    """NPM package vulnerability checker."""

    def check_package(self, package_name: str) -> List[Vulnerability]:
        """Check a specific npm package."""
        # Get installed version
        try:
            result = subprocess.run(
                ['npm', 'list', package_name, '--json'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Warning: Package {package_name} not found in project", file=sys.stderr)
                return []

            data = json.loads(result.stdout)
            version = self._extract_version(data, package_name)
        except Exception as e:
            print(f"Error checking package {package_name}: {e}", file=sys.stderr)
            return []

        # Run npm audit for all packages, then filter
        return [v for v in self.check_all() if v.package == package_name]

    def check_all(self) -> List[Vulnerability]:
        """Run npm audit on all packages."""
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                capture_output=True,
                text=True
            )

            # npm audit returns non-zero if vulnerabilities found
            # We still want to parse the output
            data = json.loads(result.stdout)
            return self._parse_npm_audit(data)

        except FileNotFoundError:
            print("Error: npm not found. Is Node.js installed?", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing npm audit output: {e}", file=sys.stderr)
            sys.exit(1)

    def _extract_version(self, data: dict, package_name: str) -> Optional[str]:
        """Extract version from npm list output."""
        dependencies = data.get('dependencies', {})
        if package_name in dependencies:
            return dependencies[package_name].get('version')
        return None

    def _parse_npm_audit(self, data: dict) -> List[Vulnerability]:
        """Parse npm audit JSON output."""
        vulnerabilities = []

        # npm audit v7+ format
        if 'vulnerabilities' in data:
            for pkg_name, vuln_data in data['vulnerabilities'].items():
                for issue in vuln_data.get('via', []):
                    if isinstance(issue, dict):  # Skip string references
                        vuln = Vulnerability(
                            package=pkg_name,
                            current_version=vuln_data.get('range', 'unknown'),
                            cve_id=issue.get('cve'),
                            severity=self._parse_severity(issue.get('severity', 'info')),
                            title=issue.get('title', 'Unknown vulnerability'),
                            description=issue.get('url', ''),
                            fixed_version=self._extract_fixed_version(vuln_data),
                            url=issue.get('url')
                        )
                        vulnerabilities.append(vuln)

        # npm audit v6 format (legacy)
        elif 'advisories' in data:
            for advisory in data['advisories'].values():
                vuln = Vulnerability(
                    package=advisory.get('module_name', 'unknown'),
                    current_version=advisory.get('vulnerable_versions', 'unknown'),
                    cve_id=advisory.get('cves', [''])[0] if advisory.get('cves') else None,
                    severity=self._parse_severity(advisory.get('severity', 'info')),
                    title=advisory.get('title', 'Unknown vulnerability'),
                    description=advisory.get('overview', ''),
                    fixed_version=advisory.get('patched_versions'),
                    url=advisory.get('url')
                )
                vulnerabilities.append(vuln)

        return vulnerabilities

    def _parse_severity(self, severity_str: str) -> Severity:
        """Parse severity string to enum."""
        severity_map = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'moderate': Severity.MODERATE,
            'low': Severity.LOW,
            'info': Severity.INFO,
        }
        return severity_map.get(severity_str.lower(), Severity.INFO)

    def _extract_fixed_version(self, vuln_data: dict) -> Optional[str]:
        """Extract the fixed version from vulnerability data."""
        # Try to get from range
        fix_available = vuln_data.get('fixAvailable')
        if isinstance(fix_available, dict):
            return fix_available.get('version')
        return None


class PipChecker(PackageManager):
    """Pip package vulnerability checker."""

    def check_package(self, package_name: str) -> List[Vulnerability]:
        """Check a specific pip package."""
        all_vulns = self.check_all()
        return [v for v in all_vulns if v.package == package_name]

    def check_all(self) -> List[Vulnerability]:
        """Run pip-audit on all packages."""
        try:
            result = subprocess.run(
                ['pip-audit', '--format', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return []  # No vulnerabilities found

            data = json.loads(result.stdout)
            return self._parse_pip_audit(data)

        except FileNotFoundError:
            print("Error: pip-audit not found. Install with: pip install pip-audit", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing pip-audit output: {e}", file=sys.stderr)
            sys.exit(1)

    def _parse_pip_audit(self, data: dict) -> List[Vulnerability]:
        """Parse pip-audit JSON output."""
        vulnerabilities = []

        for vuln_entry in data.get('vulnerabilities', []):
            vuln = Vulnerability(
                package=vuln_entry.get('name', 'unknown'),
                current_version=vuln_entry.get('version', 'unknown'),
                cve_id=vuln_entry.get('id'),
                severity=Severity.MODERATE,  # pip-audit doesn't provide severity
                title=vuln_entry.get('description', 'Unknown vulnerability'),
                description=vuln_entry.get('description', ''),
                fixed_version=', '.join(vuln_entry.get('fix_versions', [])),
                url=vuln_entry.get('more_info_url')
            )
            vulnerabilities.append(vuln)

        return vulnerabilities


class Reporter:
    """Format and display vulnerability reports."""

    @staticmethod
    def print_text(vulnerabilities: List[Vulnerability], min_severity: Severity) -> None:
        """Print vulnerabilities in human-readable format."""
        # Filter by severity
        filtered = [v for v in vulnerabilities if v.severity.value >= min_severity.value]

        if not filtered:
            print("✅ No vulnerabilities found at or above the specified severity level.")
            return

        # Group by severity
        by_severity = {}
        for vuln in filtered:
            by_severity.setdefault(vuln.severity, []).append(vuln)

        print("=" * 60)
        print("SECURITY VULNERABILITY REPORT")
        print("=" * 60)
        print(f"Total vulnerabilities found: {len(filtered)}\n")

        # Print by severity (highest first)
        for severity in sorted(by_severity.keys(), key=lambda s: s.value, reverse=True):
            vulns = by_severity[severity]
            icon = "🔴" if severity in (Severity.CRITICAL, Severity.HIGH) else "🟡"
            print(f"{icon} {severity.name} SEVERITY: {len(vulns)} vulnerabilities")
            print("-" * 60)

            for vuln in vulns:
                print(f"\nPackage: {vuln.package}")
                print(f"Current Version: {vuln.current_version}")
                if vuln.cve_id:
                    print(f"CVE: {vuln.cve_id}")
                print(f"Title: {vuln.title}")
                if vuln.fixed_version:
                    print(f"Fixed in: {vuln.fixed_version}")
                if vuln.url:
                    print(f"More info: {vuln.url}")

            print()

        print("=" * 60)
        print(f"RECOMMENDATION: Fix {len(filtered)} vulnerabilities at {min_severity.name} severity or higher")

    @staticmethod
    def print_json(vulnerabilities: List[Vulnerability], min_severity: Severity) -> None:
        """Print vulnerabilities in JSON format."""
        filtered = [v for v in vulnerabilities if v.severity.value >= min_severity.value]

        output = {
            'total': len(filtered),
            'min_severity': str(min_severity),
            'vulnerabilities': [
                {
                    'package': v.package,
                    'current_version': v.current_version,
                    'cve_id': v.cve_id,
                    'severity': str(v.severity),
                    'title': v.title,
                    'description': v.description,
                    'fixed_version': v.fixed_version,
                    'url': v.url,
                }
                for v in filtered
            ]
        }

        print(json.dumps(output, indent=2))


def detect_package_manager() -> PackageManager:
    """Auto-detect package manager based on project files."""
    cwd = Path.cwd()

    if (cwd / 'package.json').exists():
        return NPMChecker()
    elif (cwd / 'requirements.txt').exists() or (cwd / 'setup.py').exists():
        return PipChecker()
    else:
        print("Error: No package.json or requirements.txt found", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Check dependencies for known CVEs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_cves.py --check-all
  python check_cves.py --package express --severity high
  python check_cves.py --check-all --format json
        """
    )

    parser.add_argument(
        '--package',
        type=str,
        help='Check a specific package'
    )

    parser.add_argument(
        '--check-all',
        action='store_true',
        help='Check all installed packages'
    )

    parser.add_argument(
        '--severity',
        type=str,
        default='moderate',
        choices=['critical', 'high', 'moderate', 'low', 'info'],
        help='Minimum severity level to report (default: moderate)'
    )

    parser.add_argument(
        '--format',
        type=str,
        default='text',
        choices=['text', 'json'],
        help='Output format (default: text)'
    )

    args = parser.parse_args()

    if not args.package and not args.check_all:
        parser.error("Either --package or --check-all must be specified")

    # Detect package manager
    pm = detect_package_manager()

    # Run checks
    if args.package:
        vulnerabilities = pm.check_package(args.package)
    else:
        vulnerabilities = pm.check_all()

    # Parse severity
    min_severity = Severity.from_string(args.severity)

    # Generate report
    if args.format == 'json':
        Reporter.print_json(vulnerabilities, min_severity)
    else:
        Reporter.print_text(vulnerabilities, min_severity)

    # Exit with error code if vulnerabilities found
    filtered = [v for v in vulnerabilities if v.severity.value >= min_severity.value]
    sys.exit(1 if filtered else 0)


if __name__ == '__main__':
    main()
