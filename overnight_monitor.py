#!/usr/bin/env python3
"""
Overnight LLM Processing Monitor
Monitor and control overnight processing, estimate completion times
"""

import os
import pickle
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

class OvernightMonitor:
    """Monitor overnight LLM processing progress."""
    
    def __init__(self):
        self.progress_file = "overnight_progress.pkl"
        self.log_file = "overnight_processing.log"
        self.status_file = "overnight_status.json"
    
    def get_progress(self):
        """Get current progress information."""
        if not os.path.exists(self.progress_file):
            return {
                'status': 'not_started',
                'message': 'No processing session found'
            }
        
        try:
            with open(self.progress_file, 'rb') as f:
                progress_data = pickle.load(f)
            
            current_index = progress_data.get('current_index', 0)
            llm_calls = progress_data.get('llm_calls', 0)
            rule_hits = progress_data.get('rule_hits', 0)
            start_time = progress_data.get('start_time', None)
            
            # Estimate total document size from log
            total_paragraphs = self._estimate_total_paragraphs()
            
            if start_time:
                elapsed_time = time.time() - start_time
                progress_percent = (current_index / total_paragraphs) * 100 if total_paragraphs > 0 else 0
                
                # Calculate rates
                llm_rate = llm_calls / (elapsed_time / 60) if elapsed_time > 0 else 0
                paragraph_rate = current_index / (elapsed_time / 60) if elapsed_time > 0 else 0
                
                # Estimate completion time
                remaining_paragraphs = total_paragraphs - current_index
                if paragraph_rate > 0:
                    eta_minutes = remaining_paragraphs / paragraph_rate
                    eta = datetime.now() + timedelta(minutes=eta_minutes)
                else:
                    eta = None
                
                return {
                    'status': 'in_progress',
                    'current_paragraph': current_index,
                    'total_paragraphs': total_paragraphs,
                    'progress_percent': progress_percent,
                    'llm_calls': llm_calls,
                    'rule_hits': rule_hits,
                    'elapsed_hours': elapsed_time / 3600,
                    'llm_rate_per_minute': llm_rate,
                    'paragraph_rate_per_minute': paragraph_rate,
                    'eta': eta.strftime('%Y-%m-%d %H:%M:%S') if eta else 'Unknown',
                    'eta_hours': eta_minutes / 60 if eta else None
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Invalid progress data'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error reading progress: {e}'
            }
    
    def _estimate_total_paragraphs(self):
        """Estimate total paragraphs from log file."""
        if not os.path.exists(self.log_file):
            return 2400  # Default estimate
        
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Look for document loaded message
            for line in lines:
                if 'Document loaded:' in line and 'total paragraphs' in line:
                    # Extract number from message like "Document loaded: 2380 total paragraphs"
                    parts = line.split('Document loaded: ')[1].split(' total paragraphs')[0]
                    return int(parts)
            
            return 2400  # Default fallback
        except:
            return 2400
    
    def get_recent_logs(self, lines=20):
        """Get recent log entries."""
        if not os.path.exists(self.log_file):
            return []
        
        try:
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
            
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except:
            return []
    
    def save_status(self, status_data):
        """Save current status to JSON file."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            print(f"Error saving status: {e}")
    
    def display_status(self):
        """Display current processing status."""
        progress = self.get_progress()
        
        print("🌙 Overnight LLM Processing Monitor")
        print("=" * 50)
        
        if progress['status'] == 'not_started':
            print("📊 Status: Not started")
            print("💡 Run: python overnight_llm_formatter.py")
            
        elif progress['status'] == 'in_progress':
            print(f"📊 Status: Processing in progress")
            print(f"📈 Progress: {progress['current_paragraph']:,}/{progress['total_paragraphs']:,} paragraphs ({progress['progress_percent']:.1f}%)")
            print(f"🤖 LLM Calls: {progress['llm_calls']:,}")
            print(f"⚡ Rule Hits: {progress['rule_hits']:,}")
            print(f"⏱️  Elapsed: {progress['elapsed_hours']:.1f} hours")
            print(f"📊 Rate: {progress['llm_rate_per_minute']:.1f} LLM calls/min, {progress['paragraph_rate_per_minute']:.1f} paragraphs/min")
            
            if progress['eta_hours']:
                print(f"🎯 ETA: {progress['eta']} ({progress['eta_hours']:.1f} hours remaining)")
            
            # Progress bar
            progress_bar_width = 40
            filled = int(progress['progress_percent'] / 100 * progress_bar_width)
            bar = '█' * filled + '░' * (progress_bar_width - filled)
            print(f"📊 Progress: [{bar}] {progress['progress_percent']:.1f}%")
            
        elif progress['status'] == 'error':
            print(f"❌ Status: Error")
            print(f"💬 Message: {progress['message']}")
        
        # Save status for external monitoring
        self.save_status(progress)
        
        print("\n📋 Recent Log Entries:")
        print("-" * 30)
        recent_logs = self.get_recent_logs(10)
        for log in recent_logs:
            print(log.strip())
    
    def watch_progress(self, interval=30):
        """Watch progress with periodic updates."""
        print("👁️  Watching overnight processing (Ctrl+C to stop)...")
        
        try:
            while True:
                os.system('clear')  # Clear screen
                self.display_status()
                
                progress = self.get_progress()
                if progress['status'] == 'not_started':
                    print("\n⏳ Waiting for processing to start...")
                elif progress['status'] == 'in_progress':
                    print(f"\n⏳ Next update in {interval} seconds...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped.")
    
    def estimate_overnight_feasibility(self):
        """Estimate if processing can complete overnight."""
        progress = self.get_progress()
        
        if progress['status'] != 'in_progress':
            print("📊 Cannot estimate - no processing in progress")
            return
        
        print("🌙 Overnight Feasibility Analysis")
        print("=" * 40)
        
        # Current performance
        current_rate = progress.get('paragraph_rate_per_minute', 0)
        remaining_paragraphs = progress['total_paragraphs'] - progress['current_paragraph']
        
        if current_rate > 0:
            # Time estimates
            remaining_minutes = remaining_paragraphs / current_rate
            remaining_hours = remaining_minutes / 60
            
            # Overnight window (assume 8 hours)
            overnight_hours = 8
            overnight_paragraphs = current_rate * 60 * overnight_hours
            
            print(f"📊 Current rate: {current_rate:.1f} paragraphs/minute")
            print(f"📈 Remaining: {remaining_paragraphs:,} paragraphs")
            print(f"⏱️  Time needed: {remaining_hours:.1f} hours")
            print(f"🌙 Overnight capacity: {overnight_paragraphs:,.0f} paragraphs")
            
            if remaining_hours <= overnight_hours:
                print(f"✅ Will complete overnight! ({remaining_hours:.1f} hours needed)")
            else:
                shortage = remaining_hours - overnight_hours
                print(f"⚠️  May not complete overnight (need {shortage:.1f} extra hours)")
                
                # Suggestions
                print("\n💡 Optimization suggestions:")
                print("   • Reduce LLM timeout (currently 20s)")
                print("   • Increase rule-based confidence threshold")
                print("   • Process in chunks with breaks")
        else:
            print("❌ Cannot estimate - no processing rate data")

def main():
    """Main monitoring function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor overnight LLM processing")
    parser.add_argument('--watch', action='store_true', help='Watch progress continuously')
    parser.add_argument('--interval', type=int, default=30, help='Update interval in seconds')
    parser.add_argument('--feasibility', action='store_true', help='Analyze overnight feasibility')
    
    args = parser.parse_args()
    
    monitor = OvernightMonitor()
    
    if args.feasibility:
        monitor.estimate_overnight_feasibility()
    elif args.watch:
        monitor.watch_progress(args.interval)
    else:
        monitor.display_status()

if __name__ == '__main__':
    main()