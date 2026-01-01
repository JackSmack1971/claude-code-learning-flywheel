#!/bin/bash
# pr_scanner.sh - Zero-Context Script for Changelog Generation
#
# Purpose: Efficiently scans git history for pull requests and merge commits,
#          categorizes them by conventional commit prefixes, and outputs
#          pre-formatted markdown for CHANGELOG.md insertion.
#
# Usage:
#   bash pr_scanner.sh                    # Auto-detect last tag
#   bash pr_scanner.sh --since v1.0.0     # Explicit start tag
#   bash pr_scanner.sh --help             # Show usage

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# --- Configuration ---
VERBOSE=0
SINCE_TAG=""
NEW_VERSION=""
LABEL_FILTER=""
PATH_FILTER="."
OUTPUT_FILE=""

# --- Color codes for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper functions ---
log_info() {
    if [[ $VERBOSE -eq 1 ]]; then
        echo -e "${BLUE}[INFO]${NC} $1" >&2
    fi
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

usage() {
    cat <<EOF
Usage: pr_scanner.sh [OPTIONS]

Scans git history for pull requests and outputs formatted changelog entries.

OPTIONS:
    --since TAG          Start from specific git tag (default: auto-detect latest)
    --new-version VER    Specify version for changelog header (default: auto-increment)
    --label LABEL        Filter PRs by GitHub label (requires gh CLI)
    --path PATH          Scope to specific directory (default: .)
    --output FILE        Write to file instead of stdout
    --verbose            Enable debug logging
    --help               Show this help message

EXAMPLES:
    # Auto-detect last tag and scan recent merges
    bash pr_scanner.sh

    # Scan since specific version
    bash pr_scanner.sh --since v1.0.0

    # Generate changelog for v2.0.0 release
    bash pr_scanner.sh --new-version 2.0.0

    # Filter by release-notes label (requires gh CLI)
    bash pr_scanner.sh --label release-notes

    # Scope to specific package in monorepo
    bash pr_scanner.sh --path packages/core

EXIT CODES:
    0 - Success
    1 - Invalid arguments or git error
    2 - No changes found

DEPENDENCIES:
    - git (2.0+)
    - bash (4.0+)
    - Optional: gh (GitHub CLI) for label filtering
EOF
}

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --since)
            SINCE_TAG="$2"
            shift 2
            ;;
        --new-version)
            NEW_VERSION="$2"
            shift 2
            ;;
        --label)
            LABEL_FILTER="$2"
            shift 2
            ;;
        --path)
            PATH_FILTER="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# --- Validate git repository ---
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "Not a git repository. Run this script from within a git repo."
    exit 1
fi

log_info "Git repository detected: $(git rev-parse --show-toplevel)"

# --- Auto-detect last tag if not specified ---
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

    if [[ -z "$SINCE_TAG" ]]; then
        log_warn "No tags found. Scanning last 30 days of commits."
        SINCE_REF="@{30.days.ago}"
    else
        SINCE_REF="$SINCE_TAG"
        log_info "Auto-detected last tag: $SINCE_TAG"
    fi
else
    SINCE_REF="$SINCE_TAG"
    log_info "Using specified tag: $SINCE_TAG"
fi

# --- Auto-increment version if not specified ---
if [[ -z "$NEW_VERSION" ]]; then
    if [[ -n "$SINCE_TAG" ]]; then
        # Extract version number and increment patch
        BASE_VERSION=$(echo "$SINCE_TAG" | sed 's/^v//')

        # Simple patch increment (assumes semver X.Y.Z)
        if [[ "$BASE_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
            MAJOR="${BASH_REMATCH[1]}"
            MINOR="${BASH_REMATCH[2]}"
            PATCH="${BASH_REMATCH[3]}"
            NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
            log_info "Auto-incremented version: $BASE_VERSION → $NEW_VERSION"
        else
            NEW_VERSION="Unreleased"
            log_warn "Could not parse semver from tag. Using 'Unreleased'"
        fi
    else
        NEW_VERSION="Unreleased"
        log_info "No tag detected. Using 'Unreleased' version"
    fi
fi

# --- Extract merge commits ---
log_info "Scanning merge commits since: $SINCE_REF"

# Git log format: <hash>|<commit message>
MERGE_COMMITS=$(git log "$SINCE_REF..HEAD" --merges --pretty=format:"%h|%s" -- "$PATH_FILTER" || true)

if [[ -z "$MERGE_COMMITS" ]]; then
    log_warn "No merge commits found since $SINCE_REF"
    exit 2
fi

log_info "Found $(echo "$MERGE_COMMITS" | wc -l) merge commits"

# --- Categorize commits by conventional commit prefix ---
declare -A categories=(
    ["Added"]=""
    ["Changed"]=""
    ["Fixed"]=""
    ["Removed"]=""
    ["Security"]=""
    ["Deprecated"]=""
)

while IFS='|' read -r hash message; do
    log_info "Processing: $message"

    # Extract PR number from merge message (GitHub format)
    # Example: "Merge pull request #123 from user/branch"
    if [[ "$message" =~ \#([0-9]+) ]]; then
        PR_NUM="${BASH_REMATCH[1]}"
    else
        PR_NUM=""
    fi

    # Extract conventional commit prefix
    # Formats: "feat: description" or "feat(scope): description" or "Merge pull request #123 from user/feat/something"
    PREFIX=""
    DESCRIPTION=""

    # Try to extract from merge message format: "Merge pull request #123 from user/feat/..."
    if [[ "$message" =~ Merge\ pull\ request\ \#[0-9]+\ from\ [^/]+/([^/]+)/ ]]; then
        PREFIX="${BASH_REMATCH[1]}"
    # Try conventional commit format: "feat: description" or "feat(scope): description"
    elif [[ "$message" =~ ^([a-z]+)(\([^)]+\))?:\ (.+)$ ]]; then
        PREFIX="${BASH_REMATCH[1]}"
        DESCRIPTION="${BASH_REMATCH[3]}"
    # Try to extract from branch name in merge message
    elif [[ "$message" =~ /([a-z]+)- ]]; then
        PREFIX="${BASH_REMATCH[1]}"
    fi

    # If no description extracted, use full message (cleaned)
    if [[ -z "$DESCRIPTION" ]]; then
        DESCRIPTION=$(echo "$message" | sed 's/Merge pull request #[0-9]* from [^ ]* //' | sed 's/^Merge branch.*//')
    fi

    # Build entry with PR number if available
    if [[ -n "$PR_NUM" ]]; then
        ENTRY="- $DESCRIPTION (#$PR_NUM)"
    else
        ENTRY="- $DESCRIPTION ($hash)"
    fi

    # Categorize based on prefix
    case "$PREFIX" in
        feat|feature)
            categories["Added"]+="$ENTRY"$'\n'
            ;;
        fix|bugfix)
            categories["Fixed"]+="$ENTRY"$'\n'
            ;;
        refactor|perf|style|chore)
            categories["Changed"]+="$ENTRY"$'\n'
            ;;
        remove|breaking)
            categories["Removed"]+="$ENTRY"$'\n'
            ;;
        security|sec)
            categories["Security"]+="$ENTRY"$'\n'
            ;;
        deprecate|deprecated)
            categories["Deprecated"]+="$ENTRY"$'\n'
            ;;
        docs|test|ci|build)
            # Skip non-user-facing changes
            log_info "Skipping non-user-facing commit: $PREFIX"
            ;;
        *)
            # Default to Changed if unable to categorize
            log_warn "Unable to categorize: $message (prefix: '$PREFIX')"
            categories["Changed"]+="$ENTRY"$'\n'
            ;;
    esac

done <<< "$MERGE_COMMITS"

# --- Generate changelog output ---
OUTPUT=""

# Header
TODAY=$(date +%Y-%m-%d)
if [[ "$NEW_VERSION" == "Unreleased" ]]; then
    OUTPUT+="## [Unreleased]"$'\n\n'
else
    OUTPUT+="## [$NEW_VERSION] - $TODAY"$'\n\n'
fi

# Sections (in Keep a Changelog order)
SECTION_ORDER=("Added" "Changed" "Deprecated" "Removed" "Fixed" "Security")

for section in "${SECTION_ORDER[@]}"; do
    content="${categories[$section]}"

    if [[ -n "$content" ]]; then
        OUTPUT+="### $section"$'\n'
        OUTPUT+="$content"
        OUTPUT+=$'\n'
    fi
done

# --- Output result ---
if [[ -n "$OUTPUT_FILE" ]]; then
    echo "$OUTPUT" > "$OUTPUT_FILE"
    log_success "Changelog written to: $OUTPUT_FILE"
else
    echo "$OUTPUT"
fi

log_success "Changelog generation complete"
exit 0
