"""
Tests for Style Learning Engine
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from style_learning_engine import (
    StyleLearningEngine,
    DocumentStyle,
    StylePattern,
    LearnedStyleGuide
)
from safe_formatting import SafeFormattingEngine, SafeFormattingRule
from content_preservation import ContentSafetyLevel


class TestStyleLearningEngine(unittest.TestCase):
    """Test cases for StyleLearningEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = StyleLearningEngine(confidence_threshold=0.7)
        self.temp_dir = tempfile.mkdtemp()
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        self.assertEqual(self.engine.confidence_threshold, 0.7)
        self.assertIsNotNone(self.engine.preservation_engine)
        self.assertIsNotNone(self.engine.heading_patterns)
    
    def test_classify_paragraph_type(self):
        """Test paragraph type classification."""
        # Test heading detection
        self.assertEqual(self.engine._classify_paragraph_type("Chapter 1: Introduction"), "heading")
        self.assertEqual(self.engine._classify_paragraph_type("1. Overview"), "heading")
        self.assertEqual(self.engine._classify_paragraph_type("EXECUTIVE SUMMARY"), "heading")
        
        # Test list detection
        self.assertEqual(self.engine._classify_paragraph_type("1. First item"), "list")
        self.assertEqual(self.engine._classify_paragraph_type("• Bullet point"), "list")
        self.assertEqual(self.engine._classify_paragraph_type("- Dash item"), "list")
        
        # Test paragraph detection
        self.assertEqual(self.engine._classify_paragraph_type("This is a regular paragraph with normal text."), "paragraph")
        
        # Test empty content
        self.assertEqual(self.engine._classify_paragraph_type(""), "empty")
        self.assertEqual(self.engine._classify_paragraph_type("   "), "empty")
    
    def test_document_style_creation(self):
        """Test DocumentStyle creation."""
        style = DocumentStyle(
            font_families=['Arial', 'Times New Roman'],
            font_sizes=[12.0, 14.0, 16.0],
            colors=['#000000', '#FF0000'],
            alignments=['left', 'center'],
            spacing={'line_spacing': 1.5},
            margins={'top': 72.0, 'bottom': 72.0},
            heading_styles={},
            paragraph_styles={}
        )
        
        self.assertEqual(len(style.font_families), 2)
        self.assertEqual(len(style.font_sizes), 3)
        self.assertEqual(style.spacing['line_spacing'], 1.5)
    
    def test_style_pattern_creation(self):
        """Test StylePattern creation."""
        pattern = StylePattern(
            pattern_type='heading',
            style_rules={'font-size': '16px', 'font-weight': 'bold'},
            confidence_score=0.8,
            usage_frequency=2,
            text_characteristics=['short_text', 'heading']
        )
        
        self.assertEqual(pattern.pattern_type, 'heading')
        self.assertEqual(pattern.confidence_score, 0.8)
        self.assertEqual(pattern.usage_frequency, 2)
        self.assertIn('font-size', pattern.style_rules)
    
    def test_compare_styles(self):
        """Test style comparison functionality."""
        original = DocumentStyle(
            font_families=['Times New Roman'],
            font_sizes=[12.0],
            colors=['#000000'],
            alignments=['left'],
            spacing={},
            margins={},
            heading_styles={},
            paragraph_styles={}
        )
        
        formatted = DocumentStyle(
            font_families=['Arial'],
            font_sizes=[14.0],
            colors=['#000000'],
            alignments=['left'],
            spacing={},
            margins={},
            heading_styles={},
            paragraph_styles={}
        )
        
        changes = self.engine._compare_styles(original, formatted)
        
        self.assertIn('font_changes', changes)
        self.assertEqual(changes['font_changes']['from'], 'Times New Roman')
        self.assertEqual(changes['font_changes']['to'], 'Arial')
        
        self.assertIn('size_changes', changes)
        self.assertEqual(changes['size_changes']['from'], 12.0)
        self.assertEqual(changes['size_changes']['to'], 14.0)
    
    def test_extract_patterns(self):
        """Test pattern extraction from style changes."""
        changes = {
            'font_changes': {'from': 'Times New Roman', 'to': 'Arial'},
            'size_changes': {'from': 12.0, 'to': 14.0, 'delta': 2.0},
            'heading_changes': {
                'heading_1': {
                    'font_size': {'from': 16.0, 'to': 18.0},
                    'font_family': {'from': 'Times New Roman', 'to': 'Arial'}
                }
            }
        }
        
        patterns = self.engine._extract_patterns(changes, 'original.docx', 'formatted.docx')
        
        self.assertGreater(len(patterns), 0)
        
        # Check for font pattern
        font_patterns = [p for p in patterns if p.pattern_type == 'font_family']
        self.assertEqual(len(font_patterns), 1)
        self.assertEqual(font_patterns[0].style_rules['font-family'], 'Arial')
        
        # Check for size pattern  
        size_patterns = [p for p in patterns if p.pattern_type == 'font_size']
        self.assertEqual(len(size_patterns), 1)
        self.assertEqual(size_patterns[0].style_rules['font-size'], '14.0px')
    
    def test_cluster_patterns(self):
        """Test pattern clustering."""
        patterns = [
            StylePattern('heading', {'font-size': '16px'}, 0.8, 1, ['heading']),
            StylePattern('heading', {'font-size': '16px'}, 0.7, 1, ['heading']),
            StylePattern('font_family', {'font-family': 'Arial'}, 0.9, 1, ['all_text'])
        ]
        
        clustered = self.engine._cluster_patterns(patterns)
        
        # Should merge similar patterns
        heading_patterns = [p for p in clustered if p.pattern_type == 'heading']
        self.assertEqual(len(heading_patterns), 1)
        self.assertEqual(heading_patterns[0].usage_frequency, 2)
        self.assertGreater(heading_patterns[0].confidence_score, 0.8)
    
    def test_generate_style_guide(self):
        """Test style guide generation."""
        patterns = [
            StylePattern('heading', {'font-size': '16px'}, 0.8, 2, ['heading']),
            StylePattern('font_family', {'font-family': 'Arial'}, 0.9, 3, ['all_text'])
        ]
        
        style_data = [{
            'formatted': DocumentStyle(
                font_families=['Arial', 'Arial', 'Arial'],
                font_sizes=[12.0, 14.0, 16.0],
                colors=['#000000'],
                alignments=['left'],
                spacing={'default': 1.5},
                margins={},
                heading_styles={},
                paragraph_styles={}
            )
        }]
        
        style_guide = self.engine._generate_style_guide(patterns, style_data)
        
        self.assertEqual(len(style_guide.patterns), 2)
        self.assertEqual(style_guide.default_font, 'Arial')
        self.assertEqual(style_guide.default_size, 14.0)
        self.assertEqual(style_guide.training_examples, 1)
    
    def test_convert_to_formatting_rules(self):
        """Test conversion to SafeFormattingRule objects."""
        patterns = [
            StylePattern('heading', {'font-size': '16px', 'font-weight': 'bold'}, 0.8, 2, ['heading']),
            StylePattern('font_family', {'font-family': 'Arial'}, 0.9, 3, ['all_text'])
        ]
        
        style_guide = LearnedStyleGuide(
            patterns=patterns,
            default_font='Arial',
            default_size=12.0,
            color_palette=['#000000'],
            spacing_rules={'default': 1.5},
            confidence_threshold=0.7,
            training_examples=3
        )
        
        rules = self.engine.convert_to_formatting_rules(style_guide)
        
        self.assertIn('default', rules)
        self.assertIsInstance(rules['default'], SafeFormattingRule)
        self.assertEqual(rules['default'].css_properties['font-family'], 'Arial')
        self.assertEqual(rules['default'].css_properties['font-size'], '12.0px')
        
        # Check learned patterns converted to rules
        learned_rules = [name for name in rules.keys() if name.startswith('learned_')]
        self.assertGreater(len(learned_rules), 0)
    
    def test_save_and_load_learned_guide(self):
        """Test saving and loading learned style guide."""
        patterns = [
            StylePattern('heading', {'font-size': '16px'}, 0.8, 2, ['heading'])
        ]
        
        style_guide = LearnedStyleGuide(
            patterns=patterns,
            default_font='Arial',
            default_size=12.0,
            color_palette=['#000000'],
            spacing_rules={'default': 1.5},
            confidence_threshold=0.7,
            training_examples=3
        )
        
        # Save guide
        output_path = Path(self.temp_dir) / 'test_guide.json'
        self.engine.save_learned_guide(style_guide, str(output_path))
        
        # Verify file exists
        self.assertTrue(output_path.exists())
        
        # Load guide
        loaded_guide = self.engine.load_learned_guide(str(output_path))
        
        # Verify loaded data
        self.assertEqual(len(loaded_guide.patterns), 1)
        self.assertEqual(loaded_guide.default_font, 'Arial')
        self.assertEqual(loaded_guide.default_size, 12.0)
        self.assertEqual(loaded_guide.training_examples, 3)


class TestSafeFormattingEngineIntegration(unittest.TestCase):
    """Test integration with SafeFormattingEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = SafeFormattingEngine()
    
    def test_formatting_engine_initialization(self):
        """Test formatting engine initialization."""
        self.assertIsNotNone(self.engine.default_style_guide)
        self.assertIsNone(self.engine.learned_style_guide)
        
        # Test with learned style guide path
        # Note: This would work with an actual learned guide file
        engine_with_learned = SafeFormattingEngine(learned_style_guide_path=None)
        self.assertIsNone(engine_with_learned.learned_style_guide)
    
    def test_get_active_style_guide(self):
        """Test getting active style guide."""
        style_guide = self.engine.get_active_style_guide()
        self.assertIsInstance(style_guide, dict)
        self.assertIn('h1', style_guide)
        self.assertIn('h2', style_guide)
    
    def test_learned_patterns_info(self):
        """Test getting learned patterns information."""
        info = self.engine.get_learned_patterns_info()
        self.assertIsNone(info)  # No learned guide loaded
        
        # Test with mock learned guide
        mock_guide = Mock()
        mock_guide.patterns = [Mock(pattern_type='heading'), Mock(pattern_type='font')]
        mock_guide.default_font = 'Arial'
        mock_guide.default_size = 12.0
        mock_guide.confidence_threshold = 0.7
        mock_guide.training_examples = 3
        
        self.engine.learned_style_guide = mock_guide
        
        info = self.engine.get_learned_patterns_info()
        self.assertIsNotNone(info)
        self.assertEqual(info['patterns_count'], 2)
        self.assertEqual(info['default_font'], 'Arial')
        self.assertEqual(info['training_examples'], 3)


if __name__ == '__main__':
    unittest.main()