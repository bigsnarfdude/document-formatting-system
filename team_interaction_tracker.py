#!/usr/bin/env python3
"""
Team Interaction Tracker for Document Formatting System
Captures manual corrections, user feedback, and team collaboration patterns for RL training
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from docx import Document
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from rl_data_collector import RLDataCollector, FormattingAction, Reward

@dataclass
class UserInteraction:
    """Represents a user interaction with the formatting system"""
    interaction_id: str
    user_id: str
    interaction_type: str  # 'manual_correction', 'approval', 'rejection', 'feedback'
    paragraph_index: int
    original_text: str
    corrected_text: str
    original_style: str
    corrected_style: str
    confidence_rating: float  # User's confidence in their correction
    time_spent: float  # Seconds spent on this interaction
    reasoning: str
    timestamp: str

@dataclass
class TeamSession:
    """Represents a collaborative formatting session"""
    session_id: str
    team_members: List[str]
    document_path: str
    session_start: str
    session_end: Optional[str]
    interactions: List[UserInteraction]
    consensus_decisions: List[Dict[str, Any]]
    disagreements: List[Dict[str, Any]]
    final_approval: Optional[bool]
    session_notes: str

class TeamInteractionTracker:
    """Tracks team interactions and manual corrections for RL training"""
    
    def __init__(self, rl_collector: RLDataCollector = None, enable_gui: bool = False):
        self.rl_collector = rl_collector or RLDataCollector()
        self.data_dir = Path("team_interaction_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.current_session: Optional[TeamSession] = None
        self.interaction_start_time: Optional[float] = None
        
        # GUI components (optional)
        self.enable_gui = enable_gui
        self.root = None
        self.feedback_window = None
        
        if enable_gui:
            self._setup_gui()

    def start_team_session(self, team_members: List[str], document_path: str) -> str:
        """Start a new team formatting session"""
        session_id = f"team_session_{int(time.time())}_{len(team_members)}"
        
        self.current_session = TeamSession(
            session_id=session_id,
            team_members=team_members,
            document_path=document_path,
            session_start=datetime.now().isoformat(),
            session_end=None,
            interactions=[],
            consensus_decisions=[],
            disagreements=[],
            final_approval=None,
            session_notes=""
        )
        
        # Start RL episode for the team session
        self.rl_collector.start_episode(
            user_id=f"team_{len(team_members)}",
            document_path=document_path,
            method_used="team_collaborative",
            user_preferences={
                "team_members": team_members,
                "session_type": "collaborative_formatting"
            }
        )
        
        print(f"Started team session {session_id} with {len(team_members)} members")
        return session_id

    def record_manual_correction(self, user_id: str, paragraph_index: int, 
                               original_text: str, corrected_text: str,
                               original_style: str, corrected_style: str,
                               reasoning: str = "", confidence: float = 0.8) -> str:
        """Record a manual correction made by a team member"""
        
        if not self.current_session:
            raise ValueError("No active team session. Call start_team_session() first.")
        
        interaction_id = f"correction_{int(time.time())}_{user_id}"
        
        # Calculate time spent (if tracking was started)
        time_spent = 0.0
        if self.interaction_start_time:
            time_spent = time.time() - self.interaction_start_time
            self.interaction_start_time = None
        
        interaction = UserInteraction(
            interaction_id=interaction_id,
            user_id=user_id,
            interaction_type="manual_correction",
            paragraph_index=paragraph_index,
            original_text=original_text[:500],  # Truncate for storage
            corrected_text=corrected_text[:500],
            original_style=original_style,
            corrected_style=corrected_style,
            confidence_rating=confidence,
            time_spent=time_spent,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
        
        self.current_session.interactions.append(interaction)
        
        # Record as RL action
        self.rl_collector.record_action(
            action_type="manual_correction",
            parameters={
                "paragraph_index": paragraph_index,
                "style_change": f"{original_style} -> {corrected_style}",
                "text_change_length": abs(len(corrected_text) - len(original_text)),
                "reasoning": reasoning
            },
            confidence=confidence,
            method_used="human_correction",
            paragraph_index=paragraph_index,
            original_text=original_text,
            applied_style=corrected_style
        )
        
        # Calculate reward based on correction quality
        reward_score = self._calculate_correction_reward(interaction)
        self.rl_collector.record_reward(
            quality_score=reward_score,
            user_satisfaction=confidence,
            manual_corrections_needed=0,  # This IS a correction, so it reduces future corrections
            efficiency_metric=1.0 / max(time_spent, 0.1)  # Faster corrections get higher efficiency
        )
        
        self._save_interaction(interaction)
        return interaction_id

    def record_approval_decision(self, user_id: str, paragraph_index: int,
                               approved: bool, reasoning: str = "",
                               confidence: float = 0.8) -> str:
        """Record an approval/rejection decision"""
        
        if not self.current_session:
            raise ValueError("No active team session. Call start_team_session() first.")
        
        interaction_id = f"approval_{int(time.time())}_{user_id}"
        
        interaction = UserInteraction(
            interaction_id=interaction_id,
            user_id=user_id,
            interaction_type="approval" if approved else "rejection",
            paragraph_index=paragraph_index,
            original_text="",
            corrected_text="",
            original_style="",
            corrected_style="",
            confidence_rating=confidence,
            time_spent=time.time() - (self.interaction_start_time or time.time()),
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
        
        self.current_session.interactions.append(interaction)
        
        # Record as RL action
        self.rl_collector.record_action(
            action_type="approval_decision",
            parameters={
                "approved": approved,
                "paragraph_index": paragraph_index,
                "reasoning": reasoning
            },
            confidence=confidence,
            method_used="human_review"
        )
        
        # Reward based on approval decision
        reward_score = 0.8 if approved else 0.3  # Approvals are generally positive
        self.rl_collector.record_reward(
            quality_score=reward_score,
            user_satisfaction=confidence
        )
        
        self._save_interaction(interaction)
        return interaction_id

    def record_team_disagreement(self, paragraph_index: int, 
                               disagreeing_users: List[str],
                               proposed_solutions: List[Dict[str, Any]],
                               resolution: Optional[Dict[str, Any]] = None) -> None:
        """Record when team members disagree on formatting"""
        
        if not self.current_session:
            return
        
        disagreement = {
            "paragraph_index": paragraph_index,
            "disagreeing_users": disagreeing_users,
            "proposed_solutions": proposed_solutions,
            "resolution": resolution,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_session.disagreements.append(disagreement)
        
        # Record as negative reward (disagreements indicate uncertainty)
        self.rl_collector.record_reward(
            quality_score=0.4,  # Lower score for disagreements
            user_satisfaction=0.3,
            manual_corrections_needed=len(proposed_solutions)
        )

    def record_team_consensus(self, paragraph_index: int,
                            consensus_decision: Dict[str, Any],
                            participating_users: List[str]) -> None:
        """Record when team reaches consensus"""
        
        if not self.current_session:
            return
        
        consensus = {
            "paragraph_index": paragraph_index,
            "decision": consensus_decision,
            "participating_users": participating_users,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_session.consensus_decisions.append(consensus)
        
        # Record as positive reward (consensus indicates good quality)
        self.rl_collector.record_reward(
            quality_score=0.9,  # High score for consensus
            user_satisfaction=0.8,
            manual_corrections_needed=0
        )

    def start_interaction_timer(self) -> None:
        """Start timing an interaction (for measuring time spent)"""
        self.interaction_start_time = time.time()

    def record_batch_feedback(self, feedback_data: List[Dict[str, Any]]) -> None:
        """Record feedback for multiple paragraphs at once"""
        
        for feedback in feedback_data:
            self.record_manual_correction(
                user_id=feedback.get("user_id", "unknown"),
                paragraph_index=feedback.get("paragraph_index", -1),
                original_text=feedback.get("original_text", ""),
                corrected_text=feedback.get("corrected_text", ""),
                original_style=feedback.get("original_style", ""),
                corrected_style=feedback.get("corrected_style", ""),
                reasoning=feedback.get("reasoning", ""),
                confidence=feedback.get("confidence", 0.7)
            )

    def end_team_session(self, final_approval: bool, session_notes: str = "") -> Dict[str, Any]:
        """End the team session and calculate summary metrics"""
        
        if not self.current_session:
            raise ValueError("No active team session to end.")
        
        self.current_session.session_end = datetime.now().isoformat()
        self.current_session.final_approval = final_approval
        self.current_session.session_notes = session_notes
        
        # Calculate session summary
        summary = self._calculate_session_summary()
        
        # End the RL episode
        self.rl_collector.end_episode(
            output_document_path=self.current_session.document_path,
            final_quality_score=summary.get("overall_quality_score", 0.7)
        )
        
        # Save session data
        self._save_team_session(self.current_session)
        
        # Reset for next session
        session_data = asdict(self.current_session)
        self.current_session = None
        
        return summary

    def get_interaction_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in team interactions for RL insights"""
        
        interactions_file = self.data_dir / "interactions.jsonl"
        if not interactions_file.exists():
            return {}
        
        patterns = {
            "most_corrected_styles": {},
            "user_correction_rates": {},
            "common_disagreement_types": [],
            "efficiency_by_user": {},
            "consensus_success_rate": 0.0
        }
        
        with open(interactions_file, "r") as f:
            for line in f:
                interaction = json.loads(line)
                
                # Track style corrections
                if interaction["interaction_type"] == "manual_correction":
                    original_style = interaction["original_style"]
                    patterns["most_corrected_styles"][original_style] = patterns["most_corrected_styles"].get(original_style, 0) + 1
                    
                    # Track user efficiency
                    user_id = interaction["user_id"]
                    if user_id not in patterns["efficiency_by_user"]:
                        patterns["efficiency_by_user"][user_id] = []
                    patterns["efficiency_by_user"][user_id].append(interaction["time_spent"])
        
        # Calculate average efficiency per user
        for user_id, times in patterns["efficiency_by_user"].items():
            patterns["efficiency_by_user"][user_id] = sum(times) / len(times)
        
        return patterns

    def export_team_training_data(self) -> Dict[str, Any]:
        """Export team interaction data for RL training"""
        
        # Get standard RL data
        rl_data = self.rl_collector.get_training_data("trajectory")
        
        # Add team-specific features
        team_features = {
            "interaction_patterns": self.get_interaction_patterns(),
            "team_sessions": self._load_all_sessions(),
            "collaboration_metrics": self._calculate_collaboration_metrics()
        }
        
        return {
            "rl_trajectories": rl_data,
            "team_features": team_features,
            "export_timestamp": datetime.now().isoformat()
        }

    def _calculate_correction_reward(self, interaction: UserInteraction) -> float:
        """Calculate reward score for a manual correction"""
        
        # Base reward from confidence
        reward = interaction.confidence_rating
        
        # Bonus for detailed reasoning
        if len(interaction.reasoning) > 20:
            reward += 0.1
        
        # Penalty for very slow corrections (>60 seconds)
        if interaction.time_spent > 60:
            reward -= 0.2
        
        # Bonus for style improvements (heuristic)
        if interaction.corrected_style in ["Heading 1", "Heading 2", "Heading 3", "Body Text", "List Paragraph"]:
            reward += 0.1
        
        return max(0.0, min(1.0, reward))

    def _calculate_session_summary(self) -> Dict[str, Any]:
        """Calculate summary metrics for the team session"""
        
        if not self.current_session:
            return {}
        
        total_interactions = len(self.current_session.interactions)
        corrections = [i for i in self.current_session.interactions if i.interaction_type == "manual_correction"]
        approvals = [i for i in self.current_session.interactions if i.interaction_type == "approval"]
        
        avg_confidence = sum(i.confidence_rating for i in self.current_session.interactions) / max(1, total_interactions)
        total_time = sum(i.time_spent for i in self.current_session.interactions)
        
        return {
            "session_id": self.current_session.session_id,
            "total_interactions": total_interactions,
            "manual_corrections": len(corrections),
            "approvals": len(approvals),
            "disagreements": len(self.current_session.disagreements),
            "consensus_decisions": len(self.current_session.consensus_decisions),
            "average_confidence": avg_confidence,
            "total_time_spent": total_time,
            "team_size": len(self.current_session.team_members),
            "final_approval": self.current_session.final_approval,
            "overall_quality_score": avg_confidence if self.current_session.final_approval else avg_confidence * 0.7
        }

    def _save_interaction(self, interaction: UserInteraction) -> None:
        """Save interaction to storage"""
        interactions_file = self.data_dir / "interactions.jsonl"
        with open(interactions_file, "a") as f:
            f.write(json.dumps(asdict(interaction)) + "\n")

    def _save_team_session(self, session: TeamSession) -> None:
        """Save complete team session"""
        sessions_file = self.data_dir / "team_sessions.jsonl"
        with open(sessions_file, "a") as f:
            f.write(json.dumps(asdict(session)) + "\n")

    def _load_all_sessions(self) -> List[Dict[str, Any]]:
        """Load all team sessions from storage"""
        sessions = []
        sessions_file = self.data_dir / "team_sessions.jsonl"
        
        if sessions_file.exists():
            with open(sessions_file, "r") as f:
                for line in f:
                    sessions.append(json.loads(line))
        
        return sessions

    def _calculate_collaboration_metrics(self) -> Dict[str, Any]:
        """Calculate metrics about team collaboration effectiveness"""
        
        sessions = self._load_all_sessions()
        if not sessions:
            return {}
        
        total_disagreements = sum(len(s.get("disagreements", [])) for s in sessions)
        total_consensus = sum(len(s.get("consensus_decisions", [])) for s in sessions)
        total_sessions = len(sessions)
        
        avg_team_size = sum(len(s.get("team_members", [])) for s in sessions) / total_sessions
        avg_session_time = sum(
            sum(i.get("time_spent", 0) for i in s.get("interactions", [])) 
            for s in sessions
        ) / total_sessions
        
        return {
            "average_disagreements_per_session": total_disagreements / total_sessions,
            "average_consensus_per_session": total_consensus / total_sessions,
            "consensus_to_disagreement_ratio": total_consensus / max(1, total_disagreements),
            "average_team_size": avg_team_size,
            "average_session_duration": avg_session_time,
            "total_sessions_analyzed": total_sessions
        }

    def _setup_gui(self) -> None:
        """Setup GUI for real-time feedback collection"""
        
        self.root = tk.Tk()
        self.root.title("Team Formatting Feedback")
        self.root.geometry("600x400")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # User ID entry
        ttk.Label(main_frame, text="User ID:").grid(row=0, column=0, sticky=tk.W)
        self.user_id_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.user_id_var, width=20).grid(row=0, column=1, sticky=tk.W)
        
        # Paragraph text area
        ttk.Label(main_frame, text="Original Text:").grid(row=1, column=0, sticky=(tk.W, tk.N))
        self.original_text = tk.Text(main_frame, height=3, width=50)
        self.original_text.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Corrected Text:").grid(row=2, column=0, sticky=(tk.W, tk.N))
        self.corrected_text = tk.Text(main_frame, height=3, width=50)
        self.corrected_text.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        # Style dropdowns
        ttk.Label(main_frame, text="Original Style:").grid(row=3, column=0, sticky=tk.W)
        self.original_style_var = tk.StringVar()
        style_options = ["Normal", "Heading 1", "Heading 2", "Heading 3", "Heading 4", "Heading 5", "Body Text", "List Paragraph"]
        ttk.Combobox(main_frame, textvariable=self.original_style_var, values=style_options).grid(row=3, column=1, sticky=tk.W)
        
        ttk.Label(main_frame, text="Corrected Style:").grid(row=4, column=0, sticky=tk.W)
        self.corrected_style_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.corrected_style_var, values=style_options).grid(row=4, column=1, sticky=tk.W)
        
        # Confidence slider
        ttk.Label(main_frame, text="Confidence:").grid(row=5, column=0, sticky=tk.W)
        self.confidence_var = tk.DoubleVar(value=0.8)
        ttk.Scale(main_frame, variable=self.confidence_var, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200).grid(row=5, column=1, sticky=(tk.W, tk.E))
        
        # Reasoning text
        ttk.Label(main_frame, text="Reasoning:").grid(row=6, column=0, sticky=(tk.W, tk.N))
        self.reasoning_text = tk.Text(main_frame, height=2, width=50)
        self.reasoning_text.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        # Buttons
        ttk.Button(main_frame, text="Record Correction", command=self._submit_correction).grid(row=7, column=0, pady=10)
        ttk.Button(main_frame, text="Approve", command=self._submit_approval).grid(row=7, column=1, pady=10)
        ttk.Button(main_frame, text="Reject", command=self._submit_rejection).grid(row=7, column=2, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def _submit_correction(self) -> None:
        """Submit manual correction from GUI"""
        try:
            self.record_manual_correction(
                user_id=self.user_id_var.get(),
                paragraph_index=0,  # Would need to be set externally
                original_text=self.original_text.get("1.0", tk.END).strip(),
                corrected_text=self.corrected_text.get("1.0", tk.END).strip(),
                original_style=self.original_style_var.get(),
                corrected_style=self.corrected_style_var.get(),
                reasoning=self.reasoning_text.get("1.0", tk.END).strip(),
                confidence=self.confidence_var.get()
            )
            messagebox.showinfo("Success", "Correction recorded successfully!")
            self._clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record correction: {str(e)}")

    def _submit_approval(self) -> None:
        """Submit approval from GUI"""
        try:
            self.record_approval_decision(
                user_id=self.user_id_var.get(),
                paragraph_index=0,
                approved=True,
                reasoning=self.reasoning_text.get("1.0", tk.END).strip(),
                confidence=self.confidence_var.get()
            )
            messagebox.showinfo("Success", "Approval recorded successfully!")
            self._clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record approval: {str(e)}")

    def _submit_rejection(self) -> None:
        """Submit rejection from GUI"""
        try:
            self.record_approval_decision(
                user_id=self.user_id_var.get(),
                paragraph_index=0,
                approved=False,
                reasoning=self.reasoning_text.get("1.0", tk.END).strip(),
                confidence=self.confidence_var.get()
            )
            messagebox.showinfo("Success", "Rejection recorded successfully!")
            self._clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record rejection: {str(e)}")

    def _clear_form(self) -> None:
        """Clear the GUI form"""
        self.original_text.delete("1.0", tk.END)
        self.corrected_text.delete("1.0", tk.END)
        self.reasoning_text.delete("1.0", tk.END)
        self.original_style_var.set("")
        self.corrected_style_var.set("")
        self.confidence_var.set(0.8)

    def show_gui(self) -> None:
        """Show the GUI for feedback collection"""
        if self.root:
            self.root.mainloop()

# Integration with existing formatters
def create_interactive_formatter():
    """Create a formatter that accepts real-time user feedback"""
    
    from multi_stage_formatter import MultiStageFormatter
    
    class InteractiveTeamFormatter(MultiStageFormatter):
        def __init__(self, team_tracker: TeamInteractionTracker = None):
            super().__init__()
            self.team_tracker = team_tracker or TeamInteractionTracker()
        
        def format_document_with_team_feedback(self, input_path: str, output_path: str,
                                             team_members: List[str], 
                                             interactive: bool = False) -> Dict[str, Any]:
            """Format document with team feedback collection"""
            
            # Start team session
            session_id = self.team_tracker.start_team_session(team_members, input_path)
            
            try:
                # Run initial formatting
                processed, filtered, style_counts = self.format_document(input_path, output_path)
                
                if interactive:
                    # Show GUI for feedback
                    print("Opening feedback interface...")
                    print("Please provide feedback on the formatted document.")
                    print("Close the feedback window when done.")
                    
                    # In a real implementation, this would show the formatted document
                    # alongside the feedback interface
                    if self.team_tracker.enable_gui:
                        feedback_thread = threading.Thread(target=self.team_tracker.show_gui)
                        feedback_thread.daemon = True
                        feedback_thread.start()
                        
                        # Wait for feedback (in practice, this would be event-driven)
                        input("Press Enter after providing feedback...")
                
                # End session with approval
                summary = self.team_tracker.end_team_session(
                    final_approval=True,
                    session_notes=f"Processed {processed} paragraphs, filtered {filtered}"
                )
                
                return {
                    "formatting_results": {
                        "processed": processed,
                        "filtered": filtered,
                        "style_counts": dict(style_counts)
                    },
                    "team_session": summary,
                    "session_id": session_id
                }
                
            except Exception as e:
                self.team_tracker.end_team_session(
                    final_approval=False,
                    session_notes=f"Error occurred: {str(e)}"
                )
                raise

if __name__ == "__main__":
    # Demo usage
    tracker = TeamInteractionTracker(enable_gui=False)
    
    # Start a team session
    session_id = tracker.start_team_session(
        team_members=["alice", "bob", "charlie"],
        document_path="/path/to/document.docx"
    )
    
    # Record some interactions
    tracker.record_manual_correction(
        user_id="alice",
        paragraph_index=5,
        original_text="This is a normal paragraph.",
        corrected_text="This is a normal paragraph.",
        original_style="Normal",
        corrected_style="Body Text",
        reasoning="Should be Body Text for better structure",
        confidence=0.9
    )
    
    tracker.record_approval_decision(
        user_id="bob",
        paragraph_index=10,
        approved=True,
        reasoning="Formatting looks good",
        confidence=0.8
    )
    
    tracker.record_team_consensus(
        paragraph_index=15,
        consensus_decision={"style": "Heading 2", "rationale": "This is clearly a section header"},
        participating_users=["alice", "bob", "charlie"]
    )
    
    # End session
    summary = tracker.end_team_session(
        final_approval=True,
        session_notes="Good collaborative session with clear consensus"
    )
    
    print("Session summary:", summary)
    
    # Export training data
    training_data = tracker.export_team_training_data()
    print(f"Exported training data with {len(training_data['rl_trajectories'])} trajectories")
    
    # Show interaction patterns
    patterns = tracker.get_interaction_patterns()
    print("Interaction patterns:", patterns)