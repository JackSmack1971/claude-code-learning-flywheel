#!/usr/bin/env python3
"""
Modularized validation checkers for the Learning Flywheel governance.
"""
import re
from pathlib import Path
from typing import Dict, Any

# Modularized validation checkers for skill governance rules.

class BaseChecker:
    """Base class for validation checkers.
    
    Attributes:
        result: A ValidationResult object to collect errors and warnings.
    """
    def __init__(self, result: Any):
        """Initializes the checker with a result container.
        
        Args:
            result: Container for validation results.
        """
        self.result = result

class MetadataChecker(BaseChecker):
    """Handles validation of frontmatter fields.
    
    Enforces rules for skill name (kebab-case), description length/triggers,
    and enterprise-specific tool restrictions.
    """
    
    def __init__(self, result: Any, config: Dict[str, Any]):
        """Initializes the MetadataChecker.
        
        Args:
            result: Container for validation results.
            config: Configuration dictionary with validation thresholds.
        """
        super().__init__(result)
        self.config = config

    def check(self, metadata: Dict[str, Any], file_path: Path):
        """Validate metadata fields against configuration.
        
        Args:
            metadata: Dictionary containing frontmatter fields.
            file_path: Path to the SKILL.md file being validated.
        """
        # Validation patterns and constants
        valid_name_pattern = self.config.get('valid_name_pattern')
        min_desc_length = self.config.get('min_description_length', 40)
        required_phrases = self.config.get('required_description_phrases', [])
        
        # 1. Name
        if 'name' not in metadata:
            self.result.add_error("Frontmatter missing required field: 'name'")
        else:
            name = metadata['name']
            if not valid_name_pattern.match(name):
                self.result.add_error(f"Invalid name format: '{name}'. Use kebab-case: verb-noun-context")

        # 2. Description
        if 'description' not in metadata:
            self.result.add_error("Frontmatter missing required field: 'description'")
        else:
            desc = metadata['description']
            if len(desc) < min_desc_length:
                self.result.add_warning(
                    f"Description too vague ({len(desc)} chars, min {min_desc_length}). "
                    "Add specific trigger conditions."
                )
            if not any(phrase in desc for phrase in required_phrases):
                self.result.add_warning("Description should include 'Use when' to define trigger conditions")

        # 3. Enterprise rules
        is_enterprise_skill = 'plugins/company-' in str(file_path) or 'plugins/enterprise-' in str(file_path)
        if 'allowed-tools' in metadata:
            if isinstance(metadata['allowed-tools'], list) and len(metadata['allowed-tools']) == 0:
                if is_enterprise_skill:
                    self.result.add_error("Enterprise skills MUST specify 'allowed-tools' for governance and security")
                else:
                    self.result.add_info("Consider specifying allowed-tools to restrict skill tool usage")
        elif is_enterprise_skill:
            self.result.add_error("Enterprise skills MUST include 'allowed-tools' field in frontmatter")

class ContentChecker(BaseChecker):
    """Handles validation of Negative Knowledge and structural content.
    
    Ensures that mandatory sections like 'Negative Knowledge' are present
    and contain substantial content (e.g., failure tables).
    """
    
    def __init__(self, result: Any, config: Dict[str, Any]):
        """Initializes the ContentChecker.
        
        Args:
            result: Container for validation results.
            config: Configuration dictionary with validation thresholds.
        """
        super().__init__(result)
        self.config = config

    def check(self, body: str):
        """Analyze body content for required sections and completeness.
        
        Args:
            body: The Markdown content of the skill file (excluding frontmatter).
        """
        required_sections = self.config.get('required_sections', [])
        
        has_negative_knowledge = any(section in body for section in required_sections)
        if not has_negative_knowledge:
            self.result.add_error("Missing required section: 'Negative Knowledge' or 'Failed Attempts'.")
        else:
            neg_knowledge_match = re.search(
                r'#+\s*(Negative Knowledge|Failed Attempts).*?\n(.*?)(?=\n#+|\Z)',
                body, re.DOTALL | re.IGNORECASE
            )
            if neg_knowledge_match:
                section_content = neg_knowledge_match.group(2).strip()
                if len(section_content) < 100 and '|' not in section_content:
                    self.result.add_warning("Negative Knowledge section exists but appears minimal. Add a failure.")

class BudgetChecker(BaseChecker):
    """Handles context budget and anti-pattern detection.
    
    Monitors file size (line count) and identifies deterministic logic
    that should be moved to external scripts to preserve token budget.
    """
    
    def __init__(self, result: Any, config: Dict[str, Any]):
        """Initializes the BudgetChecker.
        
        Args:
            result: Container for validation results.
            config: Configuration dictionary with validation thresholds.
        """
        super().__init__(result)
        self.config = config

    def check(self, body: str):
        """Validate context budget and detect logic anti-patterns.
        
        Args:
            body: The Markdown content of the skill file (excluding frontmatter).
        """
        max_lines = self.config.get('max_skill_lines', 500)
        rec_lines = self.config.get('recommended_skill_lines', 400)
        logic_threshold = self.config.get('deterministic_logic_threshold', 50)
        
        line_count = len(body.split('\n'))
        if line_count > max_lines:
            self.result.add_error(f"❌ FAIL: Exceeds token budget: {line_count} lines (max {max_lines}).")
        elif line_count > rec_lines:
            self.result.add_warning(f"Approaching context limit: {line_count}/{max_lines} lines.")

        # Deterministic logic check
        if_else_matches = re.findall(r'^\s*(if|elif|else|switch|case)\s', body, re.MULTILINE)
        list_matches = re.findall(r'^\s*[-*]\s+\w+:\s*["\']', body, re.MULTILINE)
        deterministic_lines = len(if_else_matches) + (len(list_matches) // 2)

        if deterministic_lines > logic_threshold:
            self.result.add_warning(f"Detected {deterministic_lines} lines of deterministic logic. Move to scripts/.")

        if 'TODO' in body or 'FIXME' in body:
            self.result.add_warning("Contains TODO/FIXME markers - complete before committing")
