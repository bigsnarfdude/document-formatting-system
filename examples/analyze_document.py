#!/usr/bin/env python3
"""
Document Analysis Tool
Analyzes a document for safety classification and formatting recommendations.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from content_preservation import ContentPreservationEngine, ContentSafetyLevel
from safe_formatting import SafeFormattingEngine


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def analyze_document(document_path: str, verbose: bool = False) -> dict:
    """Analyze a document for safety and formatting recommendations."""
    preservation_engine = ContentPreservationEngine()
    formatting_engine = SafeFormattingEngine()
    
    logger = logging.getLogger(__name__)
    
    try:
        # Create content fingerprint
        logger.info("Creating content fingerprint...")
        fingerprint = preservation_engine.create_content_fingerprint(document_path)
        
        # Identify prohibited zones
        logger.info("Identifying prohibited zones...")
        prohibited_zones = preservation_engine.identify_prohibited_zones(document_path)
        
        # Generate safety report
        logger.info("Generating safety report...")
        safety_report = preservation_engine.get_safety_report(document_path)
        
        # Extract content for detailed analysis
        logger.info("Extracting content with safety classification...")
        extracted_content = formatting_engine.extract_content_safely(document_path)
        
        # Analyze paragraph-level safety
        paragraphs = extracted_content['paragraphs']
        safety_counts = {level: 0 for level in ContentSafetyLevel}
        critical_paragraphs = []
        review_paragraphs = []
        
        for para in paragraphs:
            safety_counts[para.safety_level] += 1
            if para.safety_level == ContentSafetyLevel.CONTENT_CRITICAL:
                critical_paragraphs.append({
                    'index': para.index,
                    'text': para.text[:100] + ('...' if len(para.text) > 100 else ''),
                    'element_type': para.element_type,
                    'style': para.style_name
                })
            elif para.safety_level == ContentSafetyLevel.REQUIRES_REVIEW:
                review_paragraphs.append({
                    'index': para.index,
                    'text': para.text[:100] + ('...' if len(para.text) > 100 else ''),
                    'element_type': para.element_type,
                    'style': para.style_name
                })
        
        # Compile analysis results
        analysis = {
            'document_path': document_path,
            'fingerprint': {
                'word_count': fingerprint.word_count,
                'character_count': fingerprint.character_count,
                'paragraph_count': len(fingerprint.paragraph_hashes),
                'numerical_values_count': len(fingerprint.numerical_values),
                'numerical_values': fingerprint.numerical_values
            },
            'prohibited_zones': {
                'total_zones': len(prohibited_zones),
                'zone_types': {},
                'zones': []
            },
            'safety_classification': {
                'total_paragraphs': len(paragraphs),
                'safe_to_modify': safety_counts[ContentSafetyLevel.SAFE_TO_MODIFY],
                'requires_review': safety_counts[ContentSafetyLevel.REQUIRES_REVIEW],
                'content_critical': safety_counts[ContentSafetyLevel.CONTENT_CRITICAL],
                'safe_percentage': (safety_counts[ContentSafetyLevel.SAFE_TO_MODIFY] / len(paragraphs) * 100) if paragraphs else 0
            },
            'critical_content': critical_paragraphs,
            'review_content': review_paragraphs,
            'tables': {
                'count': len(extracted_content['tables']),
                'details': []
            },
            'recommendations': {
                'automation_feasible': safety_report['automation_feasibility']['recommended_approach'],
                'safe_percentage': safety_report['automation_feasibility']['safe_percentage']
            }
        }
        
        # Analyze prohibited zones
        for zone in prohibited_zones:
            zone_type = zone.zone_type
            if zone_type not in analysis['prohibited_zones']['zone_types']:
                analysis['prohibited_zones']['zone_types'][zone_type] = 0
            analysis['prohibited_zones']['zone_types'][zone_type] += 1
            
            analysis['prohibited_zones']['zones'].append({
                'type': zone_type,
                'paragraph_range': f"{zone.start_paragraph}-{zone.end_paragraph}",
                'sample_text': zone.text_sample,
                'safety_level': zone.safety_level.value
            })
        
        # Analyze tables
        for i, table in enumerate(extracted_content['tables']):
            table_info = {
                'index': i,
                'rows': len(table.rows),
                'columns': len(table.rows[0]) if table.rows else 0,
                'safety_concerns': []
            }
            
            # Check table cells for safety concerns
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row):
                    safety_level = preservation_engine.assess_paragraph_safety(cell['text'])
                    if safety_level != ContentSafetyLevel.SAFE_TO_MODIFY:
                        table_info['safety_concerns'].append({
                            'position': f"row {row_idx}, col {cell_idx}",
                            'safety_level': safety_level.value,
                            'text': cell['text'][:50] + ('...' if len(cell['text']) > 50 else '')
                        })
            
            analysis['tables']['details'].append(table_info)
        
        logger.info("Document analysis completed successfully")
        return analysis
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise


def print_analysis_report(analysis: dict, detailed: bool = False):
    """Print a formatted analysis report."""
    doc_name = Path(analysis['document_path']).name
    
    print("📄 DOCUMENT ANALYSIS REPORT")
    print("="*50)
    print(f"Document: {doc_name}")
    print(f"Path: {analysis['document_path']}")
    
    # Document fingerprint
    print(f"\n📊 DOCUMENT FINGERPRINT")
    print(f"   Word count: {analysis['fingerprint']['word_count']:,}")
    print(f"   Character count: {analysis['fingerprint']['character_count']:,}")
    print(f"   Paragraphs: {analysis['fingerprint']['paragraph_count']}")
    print(f"   Numerical values: {analysis['fingerprint']['numerical_values_count']}")
    
    if analysis['fingerprint']['numerical_values'] and detailed:
        print(f"   Protected numerical values:")
        for value in analysis['fingerprint']['numerical_values'][:10]:  # Show first 10
            print(f"      • {value}")
        if len(analysis['fingerprint']['numerical_values']) > 10:
            remaining = len(analysis['fingerprint']['numerical_values']) - 10
            print(f"      ... and {remaining} more")
    
    # Safety classification
    print(f"\n🛡️  SAFETY CLASSIFICATION")
    safety = analysis['safety_classification']
    print(f"   Total paragraphs: {safety['total_paragraphs']}")
    print(f"   ✅ Safe to modify: {safety['safe_to_modify']} ({safety['safe_to_modify']/safety['total_paragraphs']*100:.1f}%)")
    print(f"   👁️  Requires review: {safety['requires_review']} ({safety['requires_review']/safety['total_paragraphs']*100:.1f}%)")
    print(f"   🚫 Content critical: {safety['content_critical']} ({safety['content_critical']/safety['total_paragraphs']*100:.1f}%)")
    
    # Prohibited zones
    print(f"\n🚫 PROHIBITED ZONES")
    zones = analysis['prohibited_zones']
    print(f"   Total zones: {zones['total_zones']}")
    
    if zones['zone_types']:
        print(f"   Zone types:")
        for zone_type, count in zones['zone_types'].items():
            print(f"      • {zone_type}: {count}")
    
    if detailed and zones['zones']:
        print(f"   Zone details:")
        for zone in zones['zones'][:5]:  # Show first 5
            print(f"      • {zone['type']} (para {zone['paragraph_range']}): {zone['sample_text']}")
        if len(zones['zones']) > 5:
            print(f"      ... and {len(zones['zones']) - 5} more zones")
    
    # Tables analysis
    tables = analysis['tables']
    if tables['count'] > 0:
        print(f"\n📋 TABLES ANALYSIS")
        print(f"   Total tables: {tables['count']}")
        
        for table in tables['details']:
            print(f"   Table {table['index']}: {table['rows']} rows × {table['columns']} columns")
            if table['safety_concerns']:
                print(f"      Safety concerns: {len(table['safety_concerns'])}")
                if detailed:
                    for concern in table['safety_concerns'][:3]:  # Show first 3
                        print(f"         • {concern['position']}: {concern['safety_level']} - {concern['text']}")
    
    # Critical content details
    if detailed and analysis['critical_content']:
        print(f"\n🚨 CRITICAL CONTENT SAMPLES")
        for para in analysis['critical_content'][:5]:  # Show first 5
            print(f"   Para {para['index']} ({para['element_type']}): {para['text']}")
    
    # Review content details
    if detailed and analysis['review_content']:
        print(f"\n👁️  REVIEW CONTENT SAMPLES")
        for para in analysis['review_content'][:5]:  # Show first 5
            print(f"   Para {para['index']} ({para['element_type']}): {para['text']}")
    
    # Recommendations
    print(f"\n🤖 AUTOMATION RECOMMENDATIONS")
    recommendations = analysis['recommendations']
    print(f"   Safe percentage: {recommendations['safe_percentage']:.1f}%")
    print(f"   Recommendation: {recommendations['automation_feasible']}")
    
    # Risk assessment
    risk_level = "LOW"
    if safety['content_critical'] / safety['total_paragraphs'] > 0.5:
        risk_level = "HIGH"
    elif safety['content_critical'] / safety['total_paragraphs'] > 0.2:
        risk_level = "MEDIUM"
    
    print(f"\n⚖️  RISK ASSESSMENT")
    print(f"   Content modification risk: {risk_level}")
    
    if risk_level == "HIGH":
        print(f"   ⚠️  WARNING: High proportion of critical content")
        print(f"   💡 SUGGESTION: Manual formatting recommended")
    elif risk_level == "MEDIUM":
        print(f"   ⚠️  CAUTION: Moderate critical content")
        print(f"   💡 SUGGESTION: Automated formatting with extensive human review")
    else:
        print(f"   ✅ LOW RISK: Suitable for automated formatting")
        print(f"   💡 SUGGESTION: Automated formatting with standard human review")


def main():
    """Main function for document analysis tool."""
    parser = argparse.ArgumentParser(
        description="Analyze Word documents for content safety and formatting recommendations"
    )
    parser.add_argument(
        "document",
        help="Path to the Word document to analyze"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-d", "--detailed",
        action="store_true",
        help="Show detailed analysis including content samples"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate document path
    document_path = Path(args.document)
    if not document_path.exists():
        print(f"❌ Error: Document not found: {document_path}")
        return 1
    
    if not document_path.suffix.lower() in ['.docx', '.doc']:
        print(f"❌ Error: Unsupported file format. Please provide a Word document (.docx or .doc)")
        return 1
    
    try:
        # Analyze document
        print(f"🔍 Analyzing document: {document_path.name}")
        analysis = analyze_document(str(document_path), args.verbose)
        
        if args.json:
            # Output JSON
            import json
            print(json.dumps(analysis, indent=2, default=str))
        else:
            # Output formatted report
            print_analysis_report(analysis, args.detailed)
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)