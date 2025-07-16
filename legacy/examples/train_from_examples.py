#!/usr/bin/env python3
"""
Train Document Formatting System from Examples
Learns formatting patterns from before/after document pairs.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.style_learning_engine import StyleLearningEngine
from src.safe_formatting import SafeFormattingEngine


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('training.log')
        ]
    )


def validate_document_pairs(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Validate that all document files exist."""
    validated_pairs = []
    
    for original_path, formatted_path in pairs:
        original = Path(original_path)
        formatted = Path(formatted_path)
        
        if not original.exists():
            print(f"❌ Original document not found: {original}")
            continue
            
        if not formatted.exists():
            print(f"❌ Formatted document not found: {formatted}")
            continue
            
        if not original.suffix.lower() == '.docx':
            print(f"❌ Original document must be .docx: {original}")
            continue
            
        if not formatted.suffix.lower() == '.docx':
            print(f"❌ Formatted document must be .docx: {formatted}")
            continue
        
        validated_pairs.append((str(original), str(formatted)))
        print(f"✅ Valid pair: {original.name} → {formatted.name}")
    
    return validated_pairs


def main():
    parser = argparse.ArgumentParser(
        description="Train document formatting system from example pairs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train from 3 document pairs
  python train_from_examples.py \\
    --pair original1.docx formatted1.docx \\
    --pair original2.docx formatted2.docx \\
    --pair original3.docx formatted3.docx
  
  # Train with custom output location
  python train_from_examples.py \\
    --pair doc1_before.docx doc1_after.docx \\
    --pair doc2_before.docx doc2_after.docx \\
    --output my_learned_styles.json
  
  # Train with detailed logging
  python train_from_examples.py \\
    --pair original.docx formatted.docx \\
    --verbose
        """
    )
    
    parser.add_argument(
        '--pair', 
        nargs=2, 
        metavar=('ORIGINAL', 'FORMATTED'),
        action='append',
        required=True,
        help='Document pair: original and formatted version'
    )
    
    parser.add_argument(
        '--output',
        default='learned_style_guide.json',
        help='Output file for learned style guide (default: learned_style_guide.json)'
    )
    
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.7,
        help='Minimum confidence threshold for learned patterns (default: 0.7)'
    )
    
    parser.add_argument(
        '--generate-rules',
        action='store_true',
        help='Generate SafeFormattingRule objects and save to JSON'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    print("🤖 Document Formatting System - Example-Based Learning")
    print("=" * 60)
    
    # Validate document pairs
    print(f"\n📋 Validating {len(args.pair)} document pairs...")
    validated_pairs = validate_document_pairs(args.pair)
    
    if not validated_pairs:
        print("❌ No valid document pairs found. Exiting.")
        return 1
    
    if len(validated_pairs) < len(args.pair):
        print(f"⚠️  Only {len(validated_pairs)} of {len(args.pair)} pairs are valid.")
    
    print(f"\n🎯 Training from {len(validated_pairs)} document pairs...")
    
    # Initialize learning engine
    learning_engine = StyleLearningEngine(confidence_threshold=args.confidence_threshold)
    
    try:
        # Learn from examples
        print("🔍 Analyzing document styles...")
        learned_guide = learning_engine.learn_from_examples(validated_pairs)
        
        print(f"\n📊 Learning Results:")
        print(f"   • Patterns learned: {len(learned_guide.patterns)}")
        print(f"   • Default font: {learned_guide.default_font}")
        print(f"   • Default size: {learned_guide.default_size}px")
        print(f"   • Color palette: {len(learned_guide.color_palette)} colors")
        print(f"   • Confidence threshold: {learned_guide.confidence_threshold}")
        print(f"   • Training examples: {learned_guide.training_examples}")
        
        # Display learned patterns
        print(f"\n🎨 Learned Patterns:")
        for i, pattern in enumerate(learned_guide.patterns, 1):
            print(f"   {i}. {pattern.pattern_type}")
            print(f"      • Confidence: {pattern.confidence_score:.2f}")
            print(f"      • Usage: {pattern.usage_frequency}x")
            print(f"      • Rules: {pattern.style_rules}")
        
        # Save learned guide
        print(f"\n💾 Saving learned style guide to {args.output}...")
        learning_engine.save_learned_guide(learned_guide, args.output)
        
        # Generate formatting rules if requested
        if args.generate_rules:
            rules_output = args.output.replace('.json', '_rules.json')
            print(f"🔧 Generating SafeFormattingRule objects...")
            
            formatting_rules = learning_engine.convert_to_formatting_rules(learned_guide)
            
            # Save rules to JSON
            import json
            rules_data = {}
            for name, rule in formatting_rules.items():
                rules_data[name] = {
                    'element_type': rule.element_type,
                    'css_properties': rule.css_properties,
                    'conditions': rule.conditions,
                    'safety_level': rule.safety_level.value
                }
            
            with open(rules_output, 'w') as f:
                json.dump(rules_data, f, indent=2)
            
            print(f"💾 Saved formatting rules to {rules_output}")
            print(f"   • Generated {len(formatting_rules)} rules")
        
        print(f"\n✅ Training completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Review the learned patterns in {args.output}")
        print(f"2. Test the learned styles on new documents")
        print(f"3. Integrate with the formatting system")
        
        return 0
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        print(f"❌ Training failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())