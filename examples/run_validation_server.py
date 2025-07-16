#!/usr/bin/env python3
"""
Run Validation Server
Starts the human validation interface web server for document review.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validation_interface import HumanValidationInterface


def main():
    """Run the validation server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🖥️  Non-Destructive Document Formatting System")
    print("   Human Validation Interface Server")
    print("   " + "="*40)
    
    # Create validation interface
    try:
        port = 5000
        interface = HumanValidationInterface(port=port)
        
        print(f"\n🌐 Starting validation server...")
        print(f"   Server URL: http://localhost:{port}")
        print(f"   Dashboard: http://localhost:{port}/")
        print(f"   API Status: http://localhost:{port}/api/status/<request_id>")
        
        print(f"\n📋 Server Features:")
        print(f"   ✓ Document validation dashboard")
        print(f"   ✓ Side-by-side content comparison")
        print(f"   ✓ Safety-critical content highlighting")
        print(f"   ✓ Approval/rejection workflow")
        print(f"   ✓ Document download capability")
        print(f"   ✓ Reviewer comment system")
        
        print(f"\n🔒 Safety Features:")
        print(f"   ✓ Content integrity verification")
        print(f"   ✓ Prohibited zone identification")
        print(f"   ✓ Numerical value preservation")
        print(f"   ✓ Audit trail logging")
        
        print(f"\n⚠️  Usage Instructions:")
        print(f"   1. Process documents using the formatting system")
        print(f"   2. Documents requiring validation will appear in dashboard")
        print(f"   3. Click 'Review Document' to examine changes")
        print(f"   4. Approve or reject changes with comments")
        print(f"   5. System maintains complete audit trail")
        
        print(f"\n🚀 Starting server (Press Ctrl+C to stop)...")
        print("="*50)
        
        # Run server
        interface.run_server(debug=True)
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Server stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        logging.exception("Server startup error")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)