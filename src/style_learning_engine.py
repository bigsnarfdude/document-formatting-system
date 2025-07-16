"""
Style Learning Engine
Learns formatting patterns from before/after document examples.
"""

import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter, defaultdict

from content_preservation import ContentPreservationEngine
from safe_formatting import SafeFormattingRule, ContentSafetyLevel


@dataclass
class DocumentStyle:
    """Extracted style information from a document."""
    font_families: List[str]
    font_sizes: List[float]
    colors: List[str]
    alignments: List[str]
    spacing: Dict[str, float]
    margins: Dict[str, float]
    heading_styles: Dict[str, Dict[str, Any]]
    paragraph_styles: Dict[str, Dict[str, Any]]


@dataclass
class StylePattern:
    """A learned formatting pattern."""
    pattern_type: str  # heading, paragraph, table, list
    style_rules: Dict[str, Any]
    confidence_score: float
    usage_frequency: int
    text_characteristics: List[str]  # length, content_type, position


@dataclass
class LearnedStyleGuide:
    """Complete style guide learned from examples."""
    patterns: List[StylePattern]
    default_font: str
    default_size: float
    color_palette: List[str]
    spacing_rules: Dict[str, float]
    confidence_threshold: float
    training_examples: int


class StyleLearningEngine:
    """Learns formatting patterns from before/after document examples."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.preservation_engine = ContentPreservationEngine()
        self.logger = logging.getLogger(__name__)
        
        # Style extraction patterns
        self.heading_patterns = [
            r'^(chapter|section|part|appendix)\s+\d+',
            r'^\d+\.?\s+[A-Z]',
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS headings
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*:?\s*$'  # Title Case
        ]
        
    def learn_from_examples(self, example_pairs: List[Tuple[str, str]]) -> LearnedStyleGuide:
        """Learn formatting patterns from before/after document pairs.
        
        Args:
            example_pairs: List of (original_path, formatted_path) tuples
            
        Returns:
            LearnedStyleGuide with extracted patterns
        """
        self.logger.info(f"Learning from {len(example_pairs)} document pairs")
        
        style_data = []
        all_patterns = []
        
        for i, (original_path, formatted_path) in enumerate(example_pairs):
            self.logger.info(f"Processing pair {i+1}: {Path(original_path).name}")
            
            try:
                # Extract styles from both documents
                original_style = self._extract_document_style(original_path)
                formatted_style = self._extract_document_style(formatted_path)
                
                # Find formatting changes
                changes = self._compare_styles(original_style, formatted_style)
                
                # Extract patterns from changes
                patterns = self._extract_patterns(changes, original_path, formatted_path)
                
                style_data.append({
                    'original': original_style,
                    'formatted': formatted_style,
                    'changes': changes
                })
                
                all_patterns.extend(patterns)
                
            except Exception as e:
                self.logger.error(f"Error processing {original_path}: {e}")
                continue
        
        # Cluster and analyze patterns
        learned_patterns = self._cluster_patterns(all_patterns)
        
        # Generate style guide
        style_guide = self._generate_style_guide(learned_patterns, style_data)
        
        self.logger.info(f"Learned {len(learned_patterns)} patterns from examples")
        return style_guide
    
    def _extract_document_style(self, doc_path: str) -> DocumentStyle:
        """Extract detailed style information from a document."""
        doc = Document(doc_path)
        
        font_families = []
        font_sizes = []
        colors = []
        alignments = []
        heading_styles = {}
        paragraph_styles = {}
        
        for i, paragraph in enumerate(doc.paragraphs):
            if not paragraph.text.strip():
                continue
                
            # Extract font information
            for run in paragraph.runs:
                if run.font.name:
                    font_families.append(run.font.name)
                if run.font.size:
                    font_sizes.append(float(run.font.size.pt))
                if run.font.color.rgb:
                    colors.append(f"#{run.font.color.rgb}")
            
            # Extract paragraph formatting
            if paragraph.alignment:
                alignment_map = {
                    WD_ALIGN_PARAGRAPH.LEFT: 'left',
                    WD_ALIGN_PARAGRAPH.CENTER: 'center',
                    WD_ALIGN_PARAGRAPH.RIGHT: 'right',
                    WD_ALIGN_PARAGRAPH.JUSTIFY: 'justify'
                }
                alignments.append(alignment_map.get(paragraph.alignment, 'left'))
            
            # Classify paragraph type
            para_type = self._classify_paragraph_type(paragraph.text)
            
            # Extract style information
            style_info = {
                'font_family': font_families[-1] if font_families else None,
                'font_size': font_sizes[-1] if font_sizes else None,
                'alignment': alignments[-1] if alignments else 'left',
                'text_length': len(paragraph.text),
                'style_name': paragraph.style.name if paragraph.style else None
            }
            
            if para_type == 'heading':
                heading_styles[f"heading_{i}"] = style_info
            else:
                paragraph_styles[f"paragraph_{i}"] = style_info
        
        # Calculate spacing and margins
        spacing = self._calculate_spacing(doc)
        margins = self._calculate_margins(doc)
        
        return DocumentStyle(
            font_families=font_families,
            font_sizes=font_sizes,
            colors=colors,
            alignments=alignments,
            spacing=spacing,
            margins=margins,
            heading_styles=heading_styles,
            paragraph_styles=paragraph_styles
        )
    
    def _classify_paragraph_type(self, text: str) -> str:
        """Classify paragraph as heading, body, list, etc."""
        import re
        
        text = text.strip()
        if not text:
            return 'empty'
        
        # Check for heading patterns
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 'heading'
        
        # Check for list items
        if re.match(r'^[\d\w]\.\s+', text) or re.match(r'^[•\-\*]\s+', text):
            return 'list'
        
        # Check for short lines (likely headings)
        if len(text) < 50 and not text.endswith('.'):
            return 'heading'
        
        return 'paragraph'
    
    def _compare_styles(self, original: DocumentStyle, formatted: DocumentStyle) -> Dict[str, Any]:
        """Compare two document styles and find changes."""
        changes = {
            'font_changes': {},
            'size_changes': {},
            'color_changes': {},
            'alignment_changes': {},
            'spacing_changes': {},
            'heading_changes': {},
            'paragraph_changes': {}
        }
        
        # Analyze font family changes
        orig_fonts = Counter(original.font_families)
        form_fonts = Counter(formatted.font_families)
        
        if orig_fonts != form_fonts:
            changes['font_changes'] = {
                'from': orig_fonts.most_common(1)[0][0] if orig_fonts else None,
                'to': form_fonts.most_common(1)[0][0] if form_fonts else None
            }
        
        # Analyze size changes
        if original.font_sizes and formatted.font_sizes:
            orig_avg_size = np.mean(original.font_sizes)
            form_avg_size = np.mean(formatted.font_sizes)
            
            if abs(orig_avg_size - form_avg_size) > 1:
                changes['size_changes'] = {
                    'from': orig_avg_size,
                    'to': form_avg_size,
                    'delta': form_avg_size - orig_avg_size
                }
        
        # Compare heading styles
        for heading_id in original.heading_styles:
            if heading_id in formatted.heading_styles:
                orig_style = original.heading_styles[heading_id]
                form_style = formatted.heading_styles[heading_id]
                
                heading_changes = {}
                for key in orig_style:
                    if orig_style[key] != form_style[key]:
                        heading_changes[key] = {
                            'from': orig_style[key],
                            'to': form_style[key]
                        }
                
                if heading_changes:
                    changes['heading_changes'][heading_id] = heading_changes
        
        return changes
    
    def _extract_patterns(self, changes: Dict[str, Any], original_path: str, formatted_path: str) -> List[StylePattern]:
        """Extract reusable patterns from style changes."""
        patterns = []
        
        # Extract font pattern
        if changes['font_changes']:
            pattern = StylePattern(
                pattern_type='font_family',
                style_rules={
                    'font-family': changes['font_changes']['to']
                },
                confidence_score=0.8,
                usage_frequency=1,
                text_characteristics=['all_text']
            )
            patterns.append(pattern)
        
        # Extract size patterns
        if changes['size_changes']:
            pattern = StylePattern(
                pattern_type='font_size',
                style_rules={
                    'font-size': f"{changes['size_changes']['to']}px"
                },
                confidence_score=0.8,
                usage_frequency=1,
                text_characteristics=['body_text']
            )
            patterns.append(pattern)
        
        # Extract heading patterns
        for heading_id, heading_changes in changes['heading_changes'].items():
            css_rules = {}
            
            if 'font_size' in heading_changes:
                css_rules['font-size'] = f"{heading_changes['font_size']['to']}px"
            if 'font_family' in heading_changes:
                css_rules['font-family'] = heading_changes['font_family']['to']
            if 'alignment' in heading_changes:
                css_rules['text-align'] = heading_changes['alignment']['to']
            
            if css_rules:
                pattern = StylePattern(
                    pattern_type='heading',
                    style_rules=css_rules,
                    confidence_score=0.9,
                    usage_frequency=1,
                    text_characteristics=['heading', 'short_text']
                )
                patterns.append(pattern)
        
        return patterns
    
    def _cluster_patterns(self, patterns: List[StylePattern]) -> List[StylePattern]:
        """Cluster similar patterns and increase confidence scores."""
        if not patterns:
            return []
        
        # Group patterns by type
        pattern_groups = defaultdict(list)
        for pattern in patterns:
            pattern_groups[pattern.pattern_type].append(pattern)
        
        clustered_patterns = []
        
        for pattern_type, group_patterns in pattern_groups.items():
            if len(group_patterns) == 1:
                clustered_patterns.extend(group_patterns)
                continue
            
            # Find similar patterns and merge them
            merged_patterns = {}
            
            for pattern in group_patterns:
                rules_key = json.dumps(pattern.style_rules, sort_keys=True)
                
                if rules_key in merged_patterns:
                    # Increase confidence and frequency
                    merged_patterns[rules_key].confidence_score = min(
                        1.0,
                        merged_patterns[rules_key].confidence_score + 0.1
                    )
                    merged_patterns[rules_key].usage_frequency += 1
                else:
                    merged_patterns[rules_key] = pattern
            
            clustered_patterns.extend(merged_patterns.values())
        
        # Filter by confidence threshold
        return [p for p in clustered_patterns if p.confidence_score >= self.confidence_threshold]
    
    def _generate_style_guide(self, patterns: List[StylePattern], style_data: List[Dict]) -> LearnedStyleGuide:
        """Generate a complete style guide from learned patterns."""
        
        # Extract most common font
        all_fonts = []
        all_sizes = []
        all_colors = []
        
        for data in style_data:
            all_fonts.extend(data['formatted'].font_families)
            all_sizes.extend(data['formatted'].font_sizes)
            all_colors.extend(data['formatted'].colors)
        
        default_font = Counter(all_fonts).most_common(1)[0][0] if all_fonts else 'Arial'
        default_size = np.mean(all_sizes) if all_sizes else 12.0
        color_palette = [color for color, _ in Counter(all_colors).most_common(5)]
        
        # Extract spacing rules
        spacing_rules = {}
        if style_data:
            spacing_values = []
            for data in style_data:
                spacing_values.extend(data['formatted'].spacing.values())
            if spacing_values:
                spacing_rules['default'] = np.mean(spacing_values)
        
        return LearnedStyleGuide(
            patterns=patterns,
            default_font=default_font,
            default_size=default_size,
            color_palette=color_palette,
            spacing_rules=spacing_rules,
            confidence_threshold=self.confidence_threshold,
            training_examples=len(style_data)
        )
    
    def _calculate_spacing(self, doc: Document) -> Dict[str, float]:
        """Calculate document spacing metrics."""
        # This is a simplified implementation
        # In practice, you'd extract actual spacing values from the document
        return {'line_spacing': 1.15, 'paragraph_spacing': 6.0}
    
    def _calculate_margins(self, doc: Document) -> Dict[str, float]:
        """Calculate document margin metrics."""
        # This is a simplified implementation
        # In practice, you'd extract actual margin values from the document
        return {'top': 72.0, 'bottom': 72.0, 'left': 72.0, 'right': 72.0}
    
    def convert_to_formatting_rules(self, style_guide: LearnedStyleGuide) -> Dict[str, SafeFormattingRule]:
        """Convert learned patterns to SafeFormattingRule objects."""
        rules = {}
        
        # Create default rules
        rules['default'] = SafeFormattingRule(
            element_type='p',
            css_properties={
                'font-family': style_guide.default_font,
                'font-size': f'{style_guide.default_size}px',
                'line-height': '1.5'
            },
            conditions=['is_body_text'],
            safety_level=ContentSafetyLevel.SAFE_TO_MODIFY
        )
        
        # Convert learned patterns
        for i, pattern in enumerate(style_guide.patterns):
            rule_name = f'learned_{pattern.pattern_type}_{i}'
            
            # Determine element type
            element_type = 'p'
            conditions = ['is_body_text']
            
            if pattern.pattern_type == 'heading':
                element_type = 'h2'
                conditions = ['is_heading']
            elif pattern.pattern_type == 'font_family':
                element_type = 'p'
                conditions = ['is_body_text']
            
            rules[rule_name] = SafeFormattingRule(
                element_type=element_type,
                css_properties=pattern.style_rules,
                conditions=conditions,
                safety_level=ContentSafetyLevel.SAFE_TO_MODIFY
            )
        
        return rules
    
    def save_learned_guide(self, style_guide: LearnedStyleGuide, output_path: str):
        """Save learned style guide to JSON file."""
        guide_data = asdict(style_guide)
        
        with open(output_path, 'w') as f:
            json.dump(guide_data, f, indent=2, default=str)
        
        self.logger.info(f"Saved learned style guide to {output_path}")
    
    def load_learned_guide(self, guide_path: str) -> LearnedStyleGuide:
        """Load learned style guide from JSON file."""
        with open(guide_path, 'r') as f:
            guide_data = json.load(f)
        
        # Convert back to objects
        patterns = [StylePattern(**p) for p in guide_data['patterns']]
        guide_data['patterns'] = patterns
        
        return LearnedStyleGuide(**guide_data)