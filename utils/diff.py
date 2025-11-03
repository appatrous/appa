"""
Configuration comparison and diff utilities.
Provides tools for comparing Cisco configurations and highlighting differences.
"""
import difflib
from typing import List, Dict, Tuple
import re


class ConfigDiff:
    """Configuration diff utility."""

    @staticmethod
    def unified_diff(config1: str, config2: str, filename1: str = 'config1', filename2: str = 'config2') -> str:
        """
        Generate unified diff between two configurations.

        Args:
            config1: First configuration
            config2: Second configuration
            filename1: Label for first config
            filename2: Label for second config

        Returns:
            Unified diff string
        """
        lines1 = config1.splitlines(keepends=True)
        lines2 = config2.splitlines(keepends=True)

        diff = difflib.unified_diff(
            lines1,
            lines2,
            fromfile=filename1,
            tofile=filename2,
            lineterm=''
        )

        return ''.join(diff)

    @staticmethod
    def html_diff(config1: str, config2: str, filename1: str = 'Config 1', filename2: str = 'Config 2') -> str:
        """
        Generate HTML diff between two configurations.

        Args:
            config1: First configuration
            config2: Second configuration
            filename1: Label for first config
            filename2: Label for second config

        Returns:
            HTML diff string
        """
        lines1 = config1.splitlines()
        lines2 = config2.splitlines()

        differ = difflib.HtmlDiff(wrapcolumn=80)
        html = differ.make_file(
            lines1,
            lines2,
            fromdesc=filename1,
            todesc=filename2,
            context=True,
            numlines=3
        )

        return html

    @staticmethod
    def context_diff(config1: str, config2: str, context_lines: int = 3) -> str:
        """
        Generate context diff between two configurations.

        Args:
            config1: First configuration
            config2: Second configuration
            context_lines: Number of context lines

        Returns:
            Context diff string
        """
        lines1 = config1.splitlines(keepends=True)
        lines2 = config2.splitlines(keepends=True)

        diff = difflib.context_diff(
            lines1,
            lines2,
            lineterm='',
            n=context_lines
        )

        return ''.join(diff)

    @staticmethod
    def get_diff_stats(config1: str, config2: str) -> Dict:
        """
        Get statistics about differences between configurations.

        Args:
            config1: First configuration
            config2: Second configuration

        Returns:
            Dictionary with diff statistics
        """
        lines1 = set(config1.splitlines())
        lines2 = set(config2.splitlines())

        added = lines2 - lines1
        removed = lines1 - lines2
        common = lines1 & lines2

        return {
            'total_lines_1': len(config1.splitlines()),
            'total_lines_2': len(config2.splitlines()),
            'added_lines': len(added),
            'removed_lines': len(removed),
            'common_lines': len(common),
            'similarity_ratio': difflib.SequenceMatcher(
                None,
                config1,
                config2
            ).ratio()
        }

    @staticmethod
    def structured_diff(config1: str, config2: str) -> Dict:
        """
        Generate structured diff with categorized changes.

        Args:
            config1: First configuration
            config2: Second configuration

        Returns:
            Dictionary with categorized changes
        """
        lines1 = config1.splitlines()
        lines2 = config2.splitlines()

        sm = difflib.SequenceMatcher(None, lines1, lines2)

        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'unchanged': []
        }

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'replace':
                changes['modified'].append({
                    'type': 'modified',
                    'old_lines': lines1[i1:i2],
                    'new_lines': lines2[j1:j2],
                    'old_range': (i1, i2),
                    'new_range': (j1, j2)
                })
            elif tag == 'delete':
                changes['removed'].append({
                    'type': 'removed',
                    'lines': lines1[i1:i2],
                    'range': (i1, i2)
                })
            elif tag == 'insert':
                changes['added'].append({
                    'type': 'added',
                    'lines': lines2[j1:j2],
                    'range': (j1, j2)
                })
            elif tag == 'equal':
                changes['unchanged'].append({
                    'type': 'unchanged',
                    'lines': lines1[i1:i2],
                    'range': (i1, i2)
                })

        return changes


class CiscoConfigAnalyzer:
    """Analyze and compare Cisco configurations."""

    @staticmethod
    def extract_sections(config: str) -> Dict[str, List[str]]:
        """
        Extract configuration sections.

        Args:
            config: Configuration text

        Returns:
            Dictionary with sections
        """
        sections = {
            'interfaces': [],
            'routing': [],
            'acls': [],
            'vlans': [],
            'global': []
        }

        current_section = 'global'
        current_block = []

        for line in config.splitlines():
            line = line.rstrip()

            # Interface section
            if re.match(r'^interface\s+', line, re.IGNORECASE):
                if current_block:
                    sections[current_section].append('\n'.join(current_block))
                current_section = 'interfaces'
                current_block = [line]

            # Router section
            elif re.match(r'^router\s+', line, re.IGNORECASE):
                if current_block:
                    sections[current_section].append('\n'.join(current_block))
                current_section = 'routing'
                current_block = [line]

            # ACL section
            elif re.match(r'^(ip\s+)?access-list\s+', line, re.IGNORECASE):
                if current_block:
                    sections[current_section].append('\n'.join(current_block))
                current_section = 'acls'
                current_block = [line]

            # VLAN section
            elif re.match(r'^vlan\s+', line, re.IGNORECASE):
                if current_block:
                    sections[current_section].append('\n'.join(current_block))
                current_section = 'vlans'
                current_block = [line]

            # End of block
            elif line == '!' or (line and not line.startswith(' ')):
                if current_block:
                    sections[current_section].append('\n'.join(current_block))
                    current_block = []
                if line != '!':
                    current_section = 'global'
                    current_block = [line]

            # Continuation of current block
            elif line:
                current_block.append(line)

        # Add final block
        if current_block:
            sections[current_section].append('\n'.join(current_block))

        return sections

    @staticmethod
    def compare_sections(config1: str, config2: str) -> Dict:
        """
        Compare configurations by sections.

        Args:
            config1: First configuration
            config2: Second configuration

        Returns:
            Dictionary with section comparisons
        """
        sections1 = CiscoConfigAnalyzer.extract_sections(config1)
        sections2 = CiscoConfigAnalyzer.extract_sections(config2)

        comparisons = {}

        for section_name in sections1.keys():
            items1 = set(sections1[section_name])
            items2 = set(sections2[section_name])

            comparisons[section_name] = {
                'added': list(items2 - items1),
                'removed': list(items1 - items2),
                'unchanged': list(items1 & items2),
                'count_1': len(items1),
                'count_2': len(items2)
            }

        return comparisons

    @staticmethod
    def find_security_changes(config1: str, config2: str) -> Dict:
        """
        Identify security-relevant changes between configurations.

        Args:
            config1: First configuration
            config2: Second configuration

        Returns:
            Dictionary with security changes
        """
        security_patterns = {
            'access_lists': r'access-list|ip access-group',
            'authentication': r'aaa|username|enable secret|password',
            'encryption': r'crypto|ssh|ssl|certificate',
            'firewall': r'zone-security|class-map|policy-map',
            'logging': r'logging|snmp-server',
            'management': r'vty|console|aux',
            'routing_security': r'route-map|prefix-list|distribute-list'
        }

        security_changes = {}

        for category, pattern in security_patterns.items():
            lines1 = [l for l in config1.splitlines() if re.search(pattern, l, re.IGNORECASE)]
            lines2 = [l for l in config2.splitlines() if re.search(pattern, l, re.IGNORECASE)]

            if set(lines1) != set(lines2):
                security_changes[category] = {
                    'old': lines1,
                    'new': lines2,
                    'changed': True
                }

        return security_changes


def generate_change_summary(config1: str, config2: str, filename1: str = 'Old', filename2: str = 'New') -> Dict:
    """
    Generate comprehensive change summary.

    Args:
        config1: First configuration
        config2: Second configuration
        filename1: Label for first config
        filename2: Label for second config

    Returns:
        Dictionary with complete diff analysis
    """
    differ = ConfigDiff()
    analyzer = CiscoConfigAnalyzer()

    return {
        'files': {
            'from': filename1,
            'to': filename2
        },
        'stats': differ.get_diff_stats(config1, config2),
        'unified_diff': differ.unified_diff(config1, config2, filename1, filename2),
        'structured_changes': differ.structured_diff(config1, config2),
        'section_comparison': analyzer.compare_sections(config1, config2),
        'security_changes': analyzer.find_security_changes(config1, config2)
    }
