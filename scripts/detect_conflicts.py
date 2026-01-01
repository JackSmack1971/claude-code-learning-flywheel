#!/usr/bin/env python3
"""
Detect semantic conflicts between skills in the repository.

This script prevents the issue where 67% of deployments experience skill collision
by checking for semantic overlap between skill descriptions and trigger conditions.

Uses TF-IDF and Jaccard similarity to identify potential conflicts without requiring
heavy dependencies like embedding models (suitable for lightweight CI environments).

Usage:
    python scripts/detect_conflicts.py                    # Check all skills
    python scripts/detect_conflicts.py --threshold 0.75   # Custom similarity threshold
    python scripts/detect_conflicts.py --strict           # Fail on any potential conflict
    python scripts/detect_conflicts.py --update-registry  # Update registry.yaml with findings
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
from collections import Counter
import math


# Configuration
DEFAULT_SIMILARITY_THRESHOLD = 0.75
REGISTRY_FILE = ".claude/registry.yaml"


class SkillInfo:
    """Container for skill metadata."""

    def __init__(self, file_path: Path, name: str, description: str, tags: List[str] = None, allowed_tools: List[str] = None):
        self.file_path = file_path
        self.name = name
        self.description = description
        self.tags = tags or []
        self.allowed_tools = allowed_tools or []

        # Extract trigger terms from description
        self.trigger_terms = self._extract_trigger_terms()

    def _extract_trigger_terms(self) -> Set[str]:
        """Extract key trigger terms from description."""
        terms = set()

        # Look for "Use when" patterns
        use_when_pattern = r'[Uu]se when\s+([^.]+)'
        matches = re.findall(use_when_pattern, self.description)
        for match in matches:
            # Extract nouns and verbs (simplified)
            words = re.findall(r'\b[a-z]{3,}\b', match.lower())
            terms.update(words)

        # Add tags as trigger terms
        terms.update([tag.lower() for tag in self.tags])

        return terms

    def get_text_for_comparison(self) -> str:
        """Get combined text for similarity comparison."""
        return f"{self.description} {' '.join(self.tags)}".lower()


def extract_frontmatter(content: str) -> Dict:
    """Extract YAML frontmatter from markdown content.

    Robust parser that handles:
    - Quoted strings with colons
    - Arrays (inline and empty)
    - Comments
    - Edge cases (missing values, malformed lines)
    """
    if not content.startswith('---'):
        return {}

    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}

        frontmatter_text = parts[1].strip()
        metadata = {}

        for line_num, line in enumerate(frontmatter_text.split('\n'), 1):
            original_line = line
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Must contain colon for key:value
            if ':' not in line:
                continue

            try:
                # Split on first colon only
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Validate key (must be non-empty and valid YAML key)
                if not key or key.startswith('-'):
                    continue

                # Handle quoted strings (preserve colons inside quotes)
                if value:
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    # Handle arrays
                    elif value.startswith('[') and value.endswith(']'):
                        # Parse inline array
                        array_content = value[1:-1].strip()
                        if not array_content:
                            value = []
                        else:
                            # Split by comma and clean each item
                            items = []
                            for item in array_content.split(','):
                                item = item.strip()
                                # Remove quotes from array items
                                if (item.startswith('"') and item.endswith('"')) or \
                                   (item.startswith("'") and item.endswith("'")):
                                    item = item[1:-1]
                                if item:
                                    items.append(item)
                            value = items
                    # Handle empty/null values
                    elif value.lower() in ('null', '~', ''):
                        value = ''
                else:
                    value = ''

                metadata[key] = value

            except ValueError:
                # Line doesn't follow key:value format, skip it
                continue
            except Exception:
                # Skip malformed lines silently
                continue

        return metadata

    except Exception:
        return {}


def load_skill(file_path: Path) -> SkillInfo:
    """Load skill metadata from SKILL.md file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = extract_frontmatter(content)

        name = metadata.get('name', file_path.parent.name)
        description = metadata.get('description', '')
        tags = metadata.get('tags', [])
        allowed_tools = metadata.get('allowed-tools', [])

        return SkillInfo(file_path, name, description, tags, allowed_tools)

    except Exception as e:
        print(f"⚠️  Warning: Failed to load skill {file_path}: {e}")
        return None


def find_all_skills(base_path: Path = Path('.claude/skills')) -> List[SkillInfo]:
    """Find all SKILL.md files and load their metadata."""
    skills = []

    if not base_path.exists():
        return skills

    for root, dirs, files in os.walk(base_path):
        if 'SKILL.md' in files:
            skill_path = Path(root) / 'SKILL.md'
            skill = load_skill(skill_path)
            if skill:
                skills.append(skill)

    return skills


def tokenize(text: str) -> List[str]:
    """Tokenize text into words, preserving coding-relevant symbols.

    Preserves:
    - Hyphens for kebab-case (e.g., 'api-endpoint')
    - Underscores for snake_case (e.g., 'user_auth')
    - Periods for file extensions and method calls (e.g., '.py', 'config.json')
    - At-signs for decorators and mentions (e.g., '@property')

    This prevents false negatives where 'api-endpoint' and 'api endpoint'
    would be treated as identical.
    """
    # Replace most punctuation with spaces, but preserve coding symbols
    # Keep: - _ . @ (coding-relevant)
    # Remove: , ; : ! ? " ' ( ) [ ] { } etc.
    text = re.sub(r'[^\w\s\-_.@]', ' ', text.lower())

    # Split on whitespace and filter short tokens
    tokens = []
    for word in text.split():
        # Keep tokens that are:
        # - At least 2 chars (reduced from 3 to keep file extensions like '.py')
        # - Or single-char tokens that are coding symbols (like '@')
        if len(word) >= 2 or word in ['@', '.']:
            tokens.append(word)

    return tokens


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts."""
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Compute term frequency."""
    counter = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counter.items()}


def compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    """Compute inverse document frequency."""
    num_docs = len(documents)
    idf = {}

    # Count document frequency for each term
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            idf[term] = idf.get(term, 0) + 1

    # Calculate IDF
    for term in idf:
        idf[term] = math.log(num_docs / idf[term])

    return idf


def compute_tfidf(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    """Compute TF-IDF vector."""
    tf = compute_tf(tokens)
    tfidf = {}

    for term, tf_value in tf.items():
        tfidf[term] = tf_value * idf.get(term, 0)

    return tfidf


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Calculate cosine similarity between two TF-IDF vectors."""
    # Get all terms
    all_terms = set(vec1.keys()) | set(vec2.keys())

    # Calculate dot product and magnitudes
    dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in all_terms)
    mag1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
    mag2 = math.sqrt(sum(val ** 2 for val in vec2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def tfidf_similarity(text1: str, text2: str, idf: Dict[str, float]) -> float:
    """Calculate TF-IDF cosine similarity between two texts."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    vec1 = compute_tfidf(tokens1, idf)
    vec2 = compute_tfidf(tokens2, idf)

    return cosine_similarity(vec1, vec2)


def detect_conflicts(skills: List[SkillInfo], threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> List[Tuple[SkillInfo, SkillInfo, float, str]]:
    """
    Detect semantic conflicts between skills.

    Returns:
        List of tuples: (skill1, skill2, similarity_score, conflict_type)
    """
    conflicts = []

    # Prepare documents for IDF calculation
    documents = [tokenize(skill.get_text_for_comparison()) for skill in skills]
    idf = compute_idf(documents)

    # Compare each pair of skills
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            skill1 = skills[i]
            skill2 = skills[j]

            text1 = skill1.get_text_for_comparison()
            text2 = skill2.get_text_for_comparison()

            # Calculate both Jaccard and TF-IDF similarity
            jaccard_sim = jaccard_similarity(text1, text2)
            tfidf_sim = tfidf_similarity(text1, text2, idf)

            # Use the maximum of both similarities
            max_similarity = max(jaccard_sim, tfidf_sim)

            # Check for conflicts
            if max_similarity >= threshold:
                conflict_type = "High semantic overlap"
                conflicts.append((skill1, skill2, max_similarity, conflict_type))

            # Check for trigger term overlap
            common_triggers = skill1.trigger_terms & skill2.trigger_terms
            if len(common_triggers) >= 3:  # 3 or more common trigger terms
                conflict_type = f"Shared trigger terms: {', '.join(list(common_triggers)[:5])}"
                # Only add if not already flagged
                if max_similarity < threshold:
                    conflicts.append((skill1, skill2, len(common_triggers) / max(len(skill1.trigger_terms), len(skill2.trigger_terms)), conflict_type))

            # Check for tool permission conflicts (same allowed-tools but different purposes)
            if skill1.allowed_tools and skill2.allowed_tools:
                if set(skill1.allowed_tools) == set(skill2.allowed_tools) and max_similarity >= 0.3:
                    conflict_type = f"Identical tool permissions with similar purpose (similarity: {max_similarity:.2f})"
                    if not any(c[0] == skill1 and c[1] == skill2 for c in conflicts):
                        conflicts.append((skill1, skill2, max_similarity, conflict_type))

    return conflicts


def generate_registry(skills: List[SkillInfo]) -> str:
    """Generate a registry.yaml file mapping trigger terms to skills."""
    trigger_map = {}

    for skill in skills:
        for term in skill.trigger_terms:
            if term not in trigger_map:
                trigger_map[term] = []
            trigger_map[term].append(skill.name)

    # Generate YAML
    yaml_content = ["---", "# Skill Trigger Registry", "#",
                    "# This file maps trigger terms to specific skills to disambiguate overlaps.",
                    "# Auto-generated by detect_conflicts.py", "", "triggers:"]

    for term in sorted(trigger_map.keys()):
        skill_names = trigger_map[term]
        if len(skill_names) > 1:
            # Multiple skills for same trigger - needs disambiguation
            yaml_content.append(f"  {term}:")
            yaml_content.append(f"    # ⚠️ CONFLICT: Multiple skills use this trigger")
            for skill_name in skill_names:
                yaml_content.append(f"    - {skill_name}")
        else:
            yaml_content.append(f"  {term}: {skill_names[0]}")

    return "\n".join(yaml_content)


def print_conflicts(conflicts: List[Tuple[SkillInfo, SkillInfo, float, str]]):
    """Print detected conflicts in a readable format."""
    if not conflicts:
        print("\n✅ No semantic conflicts detected!")
        return

    print(f"\n⚠️  Found {len(conflicts)} potential conflict(s):\n")
    print("=" * 80)

    for idx, (skill1, skill2, similarity, conflict_type) in enumerate(conflicts, 1):
        print(f"\nConflict #{idx}: {conflict_type}")
        print(f"Similarity Score: {similarity:.2%}")
        print(f"\nSkill 1: {skill1.name}")
        print(f"  Path: {skill1.file_path.relative_to(Path.cwd())}")
        print(f"  Description: {skill1.description[:100]}...")
        print(f"\nSkill 2: {skill2.name}")
        print(f"  Path: {skill2.file_path.relative_to(Path.cwd())}")
        print(f"  Description: {skill2.description[:100]}...")
        print("-" * 80)

    print(f"\n💡 Recommendations:")
    print("1. Review the conflicting skills to ensure they have distinct purposes")
    print("2. Use 'allowed-tools' to differentiate read-only vs action skills")
    print("3. Update descriptions to clarify when each skill should be used")
    print("4. Consider merging skills if they truly serve the same purpose")
    print("5. Run with --update-registry to create a disambiguation map")


def main():
    parser = argparse.ArgumentParser(
        description='Detect semantic conflicts between skills'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help=f'Similarity threshold for conflict detection (default: {DEFAULT_SIMILARITY_THRESHOLD})'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail (exit 1) if any conflicts are detected'
    )
    parser.add_argument(
        '--update-registry',
        action='store_true',
        help='Update the registry.yaml file with trigger term mappings'
    )

    args = parser.parse_args()

    # Find all skills
    skills = find_all_skills()

    if not skills:
        print("⚠️  No SKILL.md files found in .claude/skills/")
        sys.exit(0)

    print(f"📊 Analyzing {len(skills)} skills for semantic conflicts...")
    print(f"   Threshold: {args.threshold:.0%} similarity")

    # Detect conflicts
    conflicts = detect_conflicts(skills, args.threshold)

    # Print results
    print_conflicts(conflicts)

    # Update registry if requested
    if args.update_registry:
        registry_content = generate_registry(skills)
        registry_path = Path(REGISTRY_FILE)
        registry_path.parent.mkdir(parents=True, exist_ok=True)

        with open(registry_path, 'w', encoding='utf-8') as f:
            f.write(registry_content)

        print(f"\n📝 Updated {REGISTRY_FILE}")

    # Exit based on strict mode
    if args.strict and conflicts:
        print("\n❌ Conflicts detected in strict mode. Failing build.")
        sys.exit(1)
    elif conflicts:
        print(f"\n⚠️  {len(conflicts)} conflict(s) detected. Review and resolve before deployment.")
        sys.exit(0)
    else:
        print("\n✅ All skills are semantically distinct!")
        sys.exit(0)


if __name__ == '__main__':
    main()
