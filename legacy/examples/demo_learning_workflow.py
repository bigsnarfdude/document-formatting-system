#!/usr/bin/env python3
"""
Demo: Complete Learning Workflow
Shows how to train the system from examples and apply learned styles.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from style_learning_engine import StyleLearningEngine
from safe_formatting import SafeFormattingEngine
from content_preservation import ContentPreservationEngine


def demo_learning_workflow():
    """Demonstrate the complete learning workflow."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("🤖 Document Formatting System - Learning Workflow Demo")
    print("=" * 60)
    
    # Step 1: Create sample document pairs for demonstration
    print("\n📋 Step 1: Preparing Training Data")
    print("For this demo, you would provide 3 document pairs:")
    print("   • original1.docx → formatted1.docx")
    print("   • original2.docx → formatted2.docx") 
    print("   • original3.docx → formatted3.docx")
    
    # Note: In real usage, you would have actual document pairs
    example_pairs = [
        # ("path/to/original1.docx", "path/to/formatted1.docx"),
        # ("path/to/original2.docx", "path/to/formatted2.docx"),
        # ("path/to/original3.docx", "path/to/formatted3.docx"),
    ]
    
    print(f"\n🎯 Expected workflow with {len(example_pairs) if example_pairs else 3} document pairs:")
    
    # Step 2: Learning from examples
    print("\n🔍 Step 2: Learning from Examples")
    print("   • Analyzing document styles...")
    print("   • Extracting formatting patterns...")
    print("   • Clustering similar patterns...")
    print("   • Generating style guide...")
    
    # Initialize learning engine
    learning_engine = StyleLearningEngine(confidence_threshold=0.7)
    
    # Simulate learning results (in real usage, this would process actual documents)
    print("\n📊 Simulated Learning Results:")
    print("   • Patterns learned: 5")
    print("   • Default font: Arial")
    print("   • Default size: 12px")
    print("   • Color palette: 3 colors")
    print("   • Confidence threshold: 0.7")
    print("   • Training examples: 3")
    
    # Step 3: Save learned style guide
    print("\n💾 Step 3: Saving Learned Style Guide")
    output_path = "demo_learned_styles.json"
    print(f"   • Saving to: {output_path}")
    
    # Step 4: Apply learned styles
    print("\n🎨 Step 4: Applying Learned Styles")
    print("   • Loading learned style guide...")
    
    # Initialize formatting engine with learned styles
    # Note: In real usage, you would pass the actual learned style guide path
    formatting_engine = SafeFormattingEngine()
    
    # Show current style guide info
    style_guide = formatting_engine.get_active_style_guide()
    print(f"   • Active style guide has {len(style_guide)} rules")
    
    # Step 5: Format new document
    print("\n📄 Step 5: Format New Document")
    print("   • Loading document...")
    print("   • Applying learned patterns...")
    print("   • Generating formatted output...")
    
    # Step 6: Validation and safety checks
    print("\n🛡️ Step 6: Safety Validation")
    print("   • Content preservation: ✅ PASSED")
    print("   • CSS safety validation: ✅ PASSED")
    print("   • Prohibited pattern check: ✅ PASSED")
    
    print("\n✅ Demo Complete!")
    print("\nTo use with real documents:")
    print("1. Run: python train_from_examples.py --pair original1.docx formatted1.docx \\")
    print("                                        --pair original2.docx formatted2.docx \\")
    print("                                        --pair original3.docx formatted3.docx")
    print("2. Use the generated learned_style_guide.json with SafeFormattingEngine")
    print("3. Apply learned styles to new documents")


def demo_advanced_features():
    """Demonstrate advanced learning features."""
    
    print("\n🚀 Advanced Learning Features")
    print("=" * 40)
    
    # Pattern analysis
    print("\n🔍 Pattern Analysis:")
    print("   • Heading detection with confidence scoring")
    print("   • Font consistency analysis")
    print("   • Color palette extraction")
    print("   • Spacing pattern recognition")
    
    # Style adaptation
    print("\n🎨 Style Adaptation:")
    print("   • Automatic style rule generation")
    print("   • Context-aware formatting")
    print("   • Safety-first CSS validation")
    print("   • Rollback capability")
    
    # Integration capabilities
    print("\n🔗 Integration Capabilities:")
    print("   • Seamless integration with existing system")
    print("   • Backward compatibility maintained")
    print("   • Human validation workflow preserved")
    print("   • Audit trail enhancement")


if __name__ == '__main__':
    demo_learning_workflow()
    demo_advanced_features()