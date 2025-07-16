#!/usr/bin/env python3
"""
Document Formatter CLI - Command-line interface for document formatting.
Uses configuration files instead of hardcoded paths.
"""

import argparse
import sys
from pathlib import Path
from config_loader import (
    get_input_path, get_output_path, get_known_path, 
    get_default_method, get_method_config, validate_config, 
    print_config_summary, config
)

def run_multi_stage():
    """Run multi-stage formatter."""
    from multi_stage_formatter import MultiStageFormatter, compare_results
    
    input_path = get_input_path()
    output_path = get_output_path('multi_stage')
    known_path = get_known_path()
    
    method_config = get_method_config('multi_stage')
    debug = method_config.get('debug', True)
    
    print(f"🚀 Running Multi-Stage Formatter...")
    print(f"   Input: {input_path}")
    print(f"   Output: {output_path}")
    
    formatter = MultiStageFormatter()
    processed, filtered, style_counts = formatter.format_document(input_path, output_path)
    
    print(f"\n📊 Results:")
    print(f"  • Processed: {processed} paragraphs")
    print(f"  • Filtered: {filtered} paragraphs")
    print(f"  • Styles: {len(style_counts)}")
    
    if debug:
        formatter.show_debug_info()
    
    if known_path and Path(known_path).exists():
        para_diff, style_diff = compare_results(output_path, known_path)
        print(f"\n🎯 Comparison: {para_diff} paragraph gap")
    
    return True

def run_pattern_based():
    """Run pattern-based formatter."""
    try:
        from pattern_based_formatter import PatternBasedFormatter
        
        input_path = get_input_path()
        output_path = get_output_path('pattern_based')
        
        print(f"🚀 Running Pattern-Based Formatter...")
        print(f"   Input: {input_path}")
        print(f"   Output: {output_path}")
        
        formatter = PatternBasedFormatter()
        result = formatter.format_document(input_path, output_path)
        
        print(f"\n✅ Pattern-based formatting completed!")
        return True
        
    except ImportError:
        print("❌ Pattern-based formatter not available")
        return False

def run_overnight_llm():
    """Run overnight LLM formatter."""
    try:
        from overnight_llm_formatter import OvernightLLMFormatter
        
        input_path = get_input_path()
        output_path = get_output_path('overnight_llm')
        
        method_config = get_method_config('overnight_llm')
        
        print(f"🚀 Running Overnight LLM Formatter...")
        print(f"   Input: {input_path}")
        print(f"   Output: {output_path}")
        print(f"   Model: {method_config.get('model_name', 'gemma3:27b-it-qat')}")
        
        formatter = OvernightLLMFormatter(method_config)
        result = formatter.format_document(input_path, output_path)
        
        print(f"\n✅ Overnight LLM formatting completed!")
        return True
        
    except ImportError:
        print("❌ Overnight LLM formatter not available")
        return False

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Document Formatting System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python format_document.py                    # Use default method from config
  python format_document.py -m multi-stage    # Use multi-stage formatter
  python format_document.py -m pattern-based  # Use pattern-based formatter
  python format_document.py -m overnight-llm  # Use overnight LLM formatter
  python format_document.py --config          # Show configuration summary
  python format_document.py --validate        # Validate configuration
        """
    )
    
    parser.add_argument(
        '-m', '--method',
        choices=['multi-stage', 'pattern-based', 'overnight-llm'],
        help='Formatting method to use (default: from config.yaml)'
    )
    
    parser.add_argument(
        '--config',
        action='store_true',
        help='Show configuration summary and exit'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    parser.add_argument(
        '--input',
        help='Input document path (overrides config.yaml)'
    )
    
    parser.add_argument(
        '--output',
        help='Output document path (overrides config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Show configuration summary
    if args.config:
        print_config_summary()
        return
    
    # Validate configuration
    if args.validate:
        print("🔍 Validating configuration...")
        if validate_config():
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration validation failed")
            print("Please check your config.yaml file")
        return
    
    # Override config with command-line arguments
    if args.input:
        config.config['input_path'] = args.input
    if args.output:
        config.config['output_path'] = args.output
    
    # Load configuration
    print("🔧 Loading configuration...")
    print_config_summary()
    
    if not validate_config():
        print("\n❌ Configuration validation failed")
        print("Please check your config.yaml file or use --config to see current settings")
        return 1
    
    # Determine method
    method = args.method or get_default_method()
    
    # Run appropriate formatter
    methods = {
        'multi-stage': run_multi_stage,
        'pattern-based': run_pattern_based,
        'overnight-llm': run_overnight_llm
    }
    
    if method not in methods:
        print(f"❌ Unknown method: {method}")
        print(f"Available methods: {list(methods.keys())}")
        return 1
    
    print(f"\n🎯 Using method: {method}")
    
    try:
        success = methods[method]()
        if success:
            print(f"\n✅ Document formatting completed successfully!")
            return 0
        else:
            print(f"\n❌ Document formatting failed")
            return 1
    except Exception as e:
        print(f"\n❌ Error during formatting: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())