#!/usr/bin/env python3
"""
RL Training Data Validator and Quality Metrics System
Validates training data quality and provides metrics for RL training effectiveness
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter, defaultdict
import warnings

@dataclass
class ValidationResult:
    """Results of training data validation"""
    is_valid: bool
    quality_score: float
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]

@dataclass
class TrajectoryQuality:
    """Quality metrics for a single trajectory"""
    trajectory_id: str
    completeness_score: float  # How complete is the state-action-reward sequence
    consistency_score: float   # How consistent are the actions/rewards
    informativeness_score: float  # How informative is the data for learning
    diversity_score: float     # How diverse are the actions taken
    overall_quality: float

class RLTrainingValidator:
    """Validates and analyzes RL training data quality"""
    
    def __init__(self, data_dir: str = "rl_training_data"):
        self.data_dir = Path(data_dir)
        self.validation_dir = Path("rl_validation_results")
        self.validation_dir.mkdir(exist_ok=True)
        
        # Quality thresholds
        self.quality_thresholds = {
            "min_trajectory_length": 3,
            "min_reward_variance": 0.05,
            "max_missing_rewards": 0.1,  # 10% missing rewards allowed
            "min_action_diversity": 2,
            "min_state_feature_coverage": 0.7,
            "min_quality_score": 0.6
        }
        
        # Validation statistics
        self.validation_stats = {
            "total_trajectories": 0,
            "valid_trajectories": 0,
            "total_state_action_pairs": 0,
            "data_quality_score": 0.0,
            "last_validation": None
        }

    def validate_training_data(self, rl_collector_data: List[Dict[str, Any]] = None) -> ValidationResult:
        """Validate the complete RL training dataset"""
        
        print("🔍 Validating RL Training Data...")
        
        # Load data if not provided
        if rl_collector_data is None:
            rl_collector_data = self._load_training_data()
        
        if not rl_collector_data:
            return ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=["No training data found"],
                warnings=[],
                recommendations=["Collect training data first"],
                metrics={}
            )
        
        issues = []
        warnings = []
        recommendations = []
        metrics = {}
        
        # Validate each trajectory
        trajectory_qualities = []
        for i, trajectory in enumerate(rl_collector_data):
            tq = self._validate_trajectory(trajectory, i)
            trajectory_qualities.append(tq)
        
        # Overall validation metrics
        metrics = self._calculate_overall_metrics(rl_collector_data, trajectory_qualities)
        
        # Check data quality issues
        issues.extend(self._check_data_quality_issues(rl_collector_data, metrics))
        warnings.extend(self._check_data_quality_warnings(rl_collector_data, metrics))
        recommendations.extend(self._generate_recommendations(metrics, issues, warnings))
        
        # Calculate overall quality score
        overall_quality = self._calculate_overall_quality_score(metrics, trajectory_qualities)
        
        # Update validation stats
        self.validation_stats.update({
            "total_trajectories": len(rl_collector_data),
            "valid_trajectories": len([tq for tq in trajectory_qualities if tq.overall_quality >= 0.6]),
            "total_state_action_pairs": sum(len(t.get("states", [])) for t in rl_collector_data),
            "data_quality_score": overall_quality,
            "last_validation": datetime.now().isoformat()
        })
        
        # Save validation results
        self._save_validation_results(ValidationResult(
            is_valid=overall_quality >= self.quality_thresholds["min_quality_score"],
            quality_score=overall_quality,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metrics=metrics
        ))
        
        return ValidationResult(
            is_valid=overall_quality >= self.quality_thresholds["min_quality_score"],
            quality_score=overall_quality,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metrics=metrics
        )

    def _validate_trajectory(self, trajectory: Dict[str, Any], traj_index: int) -> TrajectoryQuality:
        """Validate a single trajectory"""
        
        states = trajectory.get("states", [])
        actions = trajectory.get("actions", [])
        rewards = trajectory.get("rewards", [])
        
        trajectory_id = trajectory.get("episode_id", f"trajectory_{traj_index}")
        
        # Completeness: How complete is the S-A-R sequence
        completeness = self._calculate_completeness_score(states, actions, rewards)
        
        # Consistency: How consistent are the actions and rewards
        consistency = self._calculate_consistency_score(states, actions, rewards)
        
        # Informativeness: How informative is this trajectory
        informativeness = self._calculate_informativeness_score(actions, rewards)
        
        # Diversity: How diverse are the actions
        diversity = self._calculate_diversity_score(actions)
        
        # Overall quality (weighted average)
        overall = (completeness * 0.3 + consistency * 0.25 + 
                  informativeness * 0.25 + diversity * 0.2)
        
        return TrajectoryQuality(
            trajectory_id=trajectory_id,
            completeness_score=completeness,
            consistency_score=consistency,
            informativeness_score=informativeness,
            diversity_score=diversity,
            overall_quality=overall
        )

    def _calculate_completeness_score(self, states: List, actions: List, rewards: List) -> float:
        """Calculate how complete the state-action-reward sequence is"""
        
        if not states and not actions and not rewards:
            return 0.0
        
        # Check trajectory length
        min_length = self.quality_thresholds["min_trajectory_length"]
        if len(actions) < min_length:
            length_score = len(actions) / min_length
        else:
            length_score = 1.0
        
        # Check S-A-R alignment
        expected_states = len(actions) + 1  # Should have one more state than actions
        state_alignment = min(1.0, len(states) / max(1, expected_states))
        
        expected_rewards = len(actions)  # Should have same number of rewards as actions
        reward_alignment = min(1.0, len(rewards) / max(1, expected_rewards))
        
        # Missing data penalty
        missing_penalty = 0.0
        if len(rewards) < len(actions):
            missing_ratio = (len(actions) - len(rewards)) / len(actions)
            if missing_ratio > self.quality_thresholds["max_missing_rewards"]:
                missing_penalty = missing_ratio * 0.5
        
        completeness = (length_score * 0.4 + state_alignment * 0.3 + 
                       reward_alignment * 0.3) - missing_penalty
        
        return max(0.0, min(1.0, completeness))

    def _calculate_consistency_score(self, states: List, actions: List, rewards: List) -> float:
        """Calculate consistency of actions and rewards"""
        
        if not actions or not rewards:
            return 0.0
        
        # Check reward consistency (should not be all the same unless truly consistent)
        reward_values = [r.get("quality_score", 0) if isinstance(r, dict) else r for r in rewards[:len(actions)]]
        
        if len(set(reward_values)) == 1 and len(reward_values) > 3:
            # All rewards are identical - suspicious
            reward_consistency = 0.3
        else:
            reward_variance = np.var(reward_values) if reward_values else 0
            min_variance = self.quality_thresholds["min_reward_variance"]
            reward_consistency = min(1.0, reward_variance / min_variance) if min_variance > 0 else 1.0
        
        # Check action consistency (actions should make sense given states)
        action_consistency = self._check_action_state_consistency(states, actions)
        
        return (reward_consistency * 0.6 + action_consistency * 0.4)

    def _calculate_informativeness_score(self, actions: List, rewards: List) -> float:
        """Calculate how informative the trajectory is for learning"""
        
        if not actions:
            return 0.0
        
        # High-quality actions should have clear rewards
        informative_pairs = 0
        total_pairs = min(len(actions), len(rewards))
        
        for i in range(total_pairs):
            action = actions[i]
            reward = rewards[i] if i < len(rewards) else {}
            
            # Check if action has good parameters
            action_quality = 0.0
            if isinstance(action, dict):
                if action.get("confidence", 0) > 0.7:
                    action_quality += 0.5
                if action.get("parameters"):
                    action_quality += 0.3
                if action.get("method_used") in ["rule_based", "llm", "pattern_match"]:
                    action_quality += 0.2
            
            # Check if reward is meaningful
            reward_quality = 0.0
            if isinstance(reward, dict):
                quality_score = reward.get("quality_score", 0)
                if quality_score != 0.5:  # Not default/neutral
                    reward_quality += 0.7
                if reward.get("user_satisfaction") is not None:
                    reward_quality += 0.3
            
            if action_quality > 0.5 and reward_quality > 0.5:
                informative_pairs += 1
        
        return informative_pairs / max(1, total_pairs)

    def _calculate_diversity_score(self, actions: List) -> float:
        """Calculate diversity of actions in the trajectory"""
        
        if not actions:
            return 0.0
        
        # Count unique action types
        action_types = []
        methods_used = []
        
        for action in actions:
            if isinstance(action, dict):
                action_types.append(action.get("action_type", "unknown"))
                methods_used.append(action.get("method_used", "unknown"))
        
        unique_action_types = len(set(action_types))
        unique_methods = len(set(methods_used))
        
        min_diversity = self.quality_thresholds["min_action_diversity"]
        
        type_diversity = min(1.0, unique_action_types / min_diversity)
        method_diversity = min(1.0, unique_methods / min_diversity)
        
        return (type_diversity * 0.7 + method_diversity * 0.3)

    def _check_action_state_consistency(self, states: List, actions: List) -> float:
        """Check if actions are consistent with states"""
        
        if not states or not actions:
            return 0.5  # Neutral if no data to check
        
        consistent_actions = 0
        total_actions = len(actions)
        
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                continue
                
            # Get corresponding state
            state = states[i] if i < len(states) else {}
            if not isinstance(state, dict):
                continue
            
            # Simple consistency checks
            action_type = action.get("action_type", "")
            current_stage = state.get("current_stage", "")
            
            # Heuristic consistency checks
            is_consistent = True
            
            if action_type == "filter_navigation" and "initialization" not in current_stage:
                is_consistent = False
            elif action_type == "classify_heading" and state.get("paragraph_count", 0) == 0:
                is_consistent = False
            # Add more consistency checks as needed
            
            if is_consistent:
                consistent_actions += 1
        
        return consistent_actions / max(1, total_actions)

    def _calculate_overall_metrics(self, trajectories: List[Dict[str, Any]], 
                                 qualities: List[TrajectoryQuality]) -> Dict[str, Any]:
        """Calculate overall dataset metrics"""
        
        if not trajectories:
            return {}
        
        # Basic statistics
        total_trajectories = len(trajectories)
        total_actions = sum(len(t.get("actions", [])) for t in trajectories)
        total_rewards = sum(len(t.get("rewards", [])) for t in trajectories)
        total_states = sum(len(t.get("states", [])) for t in trajectories)
        
        # Quality metrics
        avg_quality = np.mean([q.overall_quality for q in qualities]) if qualities else 0.0
        quality_std = np.std([q.overall_quality for q in qualities]) if qualities else 0.0
        
        # Coverage metrics
        action_types = Counter()
        method_usage = Counter()
        reward_distribution = []
        
        for trajectory in trajectories:
            for action in trajectory.get("actions", []):
                if isinstance(action, dict):
                    action_types[action.get("action_type", "unknown")] += 1
                    method_usage[action.get("method_used", "unknown")] += 1
            
            for reward in trajectory.get("rewards", []):
                if isinstance(reward, dict):
                    reward_distribution.append(reward.get("quality_score", 0.5))
        
        # Diversity metrics
        unique_action_types = len(action_types)
        unique_methods = len(method_usage)
        
        return {
            "dataset_size": {
                "trajectories": total_trajectories,
                "actions": total_actions,
                "rewards": total_rewards,
                "states": total_states,
                "avg_trajectory_length": total_actions / max(1, total_trajectories)
            },
            "quality_metrics": {
                "average_quality": avg_quality,
                "quality_std": quality_std,
                "high_quality_trajectories": len([q for q in qualities if q.overall_quality > 0.8]),
                "low_quality_trajectories": len([q for q in qualities if q.overall_quality < 0.4])
            },
            "diversity_metrics": {
                "unique_action_types": unique_action_types,
                "unique_methods": unique_methods,
                "action_type_distribution": dict(action_types),
                "method_usage_distribution": dict(method_usage)
            },
            "reward_metrics": {
                "average_reward": np.mean(reward_distribution) if reward_distribution else 0.0,
                "reward_std": np.std(reward_distribution) if reward_distribution else 0.0,
                "reward_range": (min(reward_distribution), max(reward_distribution)) if reward_distribution else (0, 0)
            }
        }

    def _check_data_quality_issues(self, trajectories: List[Dict[str, Any]], 
                                 metrics: Dict[str, Any]) -> List[str]:
        """Check for critical data quality issues"""
        
        issues = []
        
        # Check dataset size
        if metrics.get("dataset_size", {}).get("trajectories", 0) < 5:
            issues.append("Dataset too small - need at least 5 trajectories for meaningful training")
        
        # Check trajectory length
        avg_length = metrics.get("dataset_size", {}).get("avg_trajectory_length", 0)
        if avg_length < self.quality_thresholds["min_trajectory_length"]:
            issues.append(f"Average trajectory length ({avg_length:.1f}) below minimum ({self.quality_thresholds['min_trajectory_length']})")
        
        # Check action diversity
        unique_actions = metrics.get("diversity_metrics", {}).get("unique_action_types", 0)
        if unique_actions < self.quality_thresholds["min_action_diversity"]:
            issues.append(f"Low action diversity ({unique_actions} types) - need at least {self.quality_thresholds['min_action_diversity']}")
        
        # Check reward distribution
        reward_std = metrics.get("reward_metrics", {}).get("reward_std", 0)
        if reward_std < self.quality_thresholds["min_reward_variance"]:
            issues.append(f"Low reward variance ({reward_std:.3f}) - rewards may not be informative")
        
        # Check for missing data
        total_actions = metrics.get("dataset_size", {}).get("actions", 0)
        total_rewards = metrics.get("dataset_size", {}).get("rewards", 0)
        if total_rewards < total_actions * (1 - self.quality_thresholds["max_missing_rewards"]):
            missing_ratio = 1 - (total_rewards / max(1, total_actions))
            issues.append(f"Too many missing rewards ({missing_ratio:.1%}) - maximum allowed is {self.quality_thresholds['max_missing_rewards']:.1%}")
        
        return issues

    def _check_data_quality_warnings(self, trajectories: List[Dict[str, Any]], 
                                   metrics: Dict[str, Any]) -> List[str]:
        """Check for data quality warnings (non-critical)"""
        
        warnings = []
        
        # Check for imbalanced action types
        action_dist = metrics.get("diversity_metrics", {}).get("action_type_distribution", {})
        if action_dist:
            max_count = max(action_dist.values())
            min_count = min(action_dist.values())
            if max_count > min_count * 10:  # Very imbalanced
                warnings.append("Action types are highly imbalanced - consider collecting more diverse data")
        
        # Check for method bias
        method_dist = metrics.get("diversity_metrics", {}).get("method_usage_distribution", {})
        if method_dist and "human_correction" in method_dist:
            human_corrections = method_dist["human_correction"]
            total_actions = sum(method_dist.values())
            if human_corrections / total_actions > 0.5:
                warnings.append("High proportion of human corrections - system may need improvement")
        
        # Check reward range
        reward_range = metrics.get("reward_metrics", {}).get("reward_range", (0, 0))
        if reward_range[1] - reward_range[0] < 0.3:
            warnings.append("Narrow reward range - consider using more discriminative reward function")
        
        return warnings

    def _generate_recommendations(self, metrics: Dict[str, Any], 
                                issues: List[str], warnings: List[str]) -> List[str]:
        """Generate recommendations for improving data quality"""
        
        recommendations = []
        
        # Recommendations based on issues
        if any("Dataset too small" in issue for issue in issues):
            recommendations.append("Collect more training trajectories - aim for at least 50-100 episodes")
        
        if any("trajectory length" in issue for issue in issues):
            recommendations.append("Encourage longer formatting sessions with more steps and decisions")
        
        if any("action diversity" in issue for issue in issues):
            recommendations.append("Collect data from different formatting scenarios and document types")
        
        if any("reward variance" in issue for issue in issues):
            recommendations.append("Use more discriminative reward function with wider range of scores")
        
        # Recommendations based on warnings
        if any("imbalanced" in warning for warning in warnings):
            recommendations.append("Balance data collection across different action types")
        
        if any("human corrections" in warning for warning in warnings):
            recommendations.append("Improve automated formatting to reduce need for manual corrections")
        
        # General recommendations
        avg_quality = metrics.get("quality_metrics", {}).get("average_quality", 0)
        if avg_quality < 0.7:
            recommendations.append("Focus on collecting high-quality trajectories with clear rewards")
        
        if metrics.get("dataset_size", {}).get("trajectories", 0) < 20:
            recommendations.append("Continue data collection - larger datasets typically improve RL performance")
        
        return recommendations

    def _calculate_overall_quality_score(self, metrics: Dict[str, Any], 
                                       qualities: List[TrajectoryQuality]) -> float:
        """Calculate overall quality score for the dataset"""
        
        if not qualities:
            return 0.0
        
        # Weighted combination of different quality aspects
        avg_trajectory_quality = np.mean([q.overall_quality for q in qualities])
        
        # Dataset size factor (larger datasets get bonus up to a point)
        size_factor = min(1.0, metrics.get("dataset_size", {}).get("trajectories", 0) / 20.0)
        
        # Diversity factor
        diversity_factor = min(1.0, 
                             metrics.get("diversity_metrics", {}).get("unique_action_types", 0) / 5.0)
        
        # Completeness factor (based on missing data)
        total_actions = metrics.get("dataset_size", {}).get("actions", 0)
        total_rewards = metrics.get("dataset_size", {}).get("rewards", 0)
        completeness_factor = min(1.0, total_rewards / max(1, total_actions))
        
        # Overall score
        overall_score = (avg_trajectory_quality * 0.5 + 
                        size_factor * 0.2 + 
                        diversity_factor * 0.15 + 
                        completeness_factor * 0.15)
        
        return max(0.0, min(1.0, overall_score))

    def _load_training_data(self) -> List[Dict[str, Any]]:
        """Load training data from files"""
        
        from rl_data_collector import RLDataCollector
        
        try:
            collector = RLDataCollector(str(self.data_dir))
            return collector.get_training_data("trajectory")
        except Exception as e:
            print(f"Error loading training data: {e}")
            return []

    def _save_validation_results(self, result: ValidationResult) -> None:
        """Save validation results to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.validation_dir / f"validation_result_{timestamp}.json"
        
        result_dict = {
            "timestamp": datetime.now().isoformat(),
            "is_valid": result.is_valid,
            "quality_score": result.quality_score,
            "issues": result.issues,
            "warnings": result.warnings,
            "recommendations": result.recommendations,
            "metrics": result.metrics
        }
        
        with open(result_file, "w") as f:
            json.dump(result_dict, f, indent=2)
        
        # Also save summary
        summary_file = self.validation_dir / "latest_validation_summary.json"
        summary = {
            "timestamp": datetime.now().isoformat(),
            "quality_score": result.quality_score,
            "is_valid": result.is_valid,
            "num_issues": len(result.issues),
            "num_warnings": len(result.warnings),
            "num_recommendations": len(result.recommendations),
            "validation_stats": self.validation_stats
        }
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

    def generate_quality_report(self) -> str:
        """Generate a human-readable quality report"""
        
        # Run validation
        result = self.validate_training_data()
        
        report = []
        report.append("=" * 50)
        report.append("RL TRAINING DATA QUALITY REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Overall status
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        report.append(f"Overall Status: {status}")
        report.append(f"Quality Score: {result.quality_score:.2f}/1.00")
        report.append("")
        
        # Dataset statistics
        if result.metrics:
            dataset_size = result.metrics.get("dataset_size", {})
            report.append("📊 DATASET STATISTICS")
            report.append(f"  Trajectories: {dataset_size.get('trajectories', 0)}")
            report.append(f"  Total Actions: {dataset_size.get('actions', 0)}")
            report.append(f"  Total Rewards: {dataset_size.get('rewards', 0)}")
            report.append(f"  Avg Trajectory Length: {dataset_size.get('avg_trajectory_length', 0):.1f}")
            report.append("")
            
            # Quality metrics
            quality_metrics = result.metrics.get("quality_metrics", {})
            report.append("🎯 QUALITY METRICS")
            report.append(f"  Average Quality: {quality_metrics.get('average_quality', 0):.2f}")
            report.append(f"  High Quality Trajectories: {quality_metrics.get('high_quality_trajectories', 0)}")
            report.append(f"  Low Quality Trajectories: {quality_metrics.get('low_quality_trajectories', 0)}")
            report.append("")
            
            # Diversity metrics
            diversity = result.metrics.get("diversity_metrics", {})
            report.append("🌈 DIVERSITY METRICS")
            report.append(f"  Unique Action Types: {diversity.get('unique_action_types', 0)}")
            report.append(f"  Unique Methods: {diversity.get('unique_methods', 0)}")
            report.append("")
        
        # Issues
        if result.issues:
            report.append("❌ CRITICAL ISSUES")
            for issue in result.issues:
                report.append(f"  • {issue}")
            report.append("")
        
        # Warnings
        if result.warnings:
            report.append("⚠️ WARNINGS")
            for warning in result.warnings:
                report.append(f"  • {warning}")
            report.append("")
        
        # Recommendations
        if result.recommendations:
            report.append("💡 RECOMMENDATIONS")
            for rec in result.recommendations:
                report.append(f"  • {rec}")
            report.append("")
        
        report.append("=" * 50)
        
        # Save report
        report_text = "\n".join(report)
        report_file = self.validation_dir / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w") as f:
            f.write(report_text)
        
        return report_text

    def visualize_training_data(self, save_plots: bool = True) -> Dict[str, Any]:
        """Create visualizations of the training data"""
        
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Load data and validate
            result = self.validate_training_data()
            
            if not result.metrics:
                return {"error": "No data to visualize"}
            
            # Create visualizations
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('RL Training Data Analysis', fontsize=16)
            
            # 1. Quality distribution
            trajectories = self._load_training_data()
            qualities = [self._validate_trajectory(t, i) for i, t in enumerate(trajectories)]
            quality_scores = [q.overall_quality for q in qualities]
            
            axes[0, 0].hist(quality_scores, bins=20, alpha=0.7, color='skyblue')
            axes[0, 0].axvline(np.mean(quality_scores), color='red', linestyle='--', 
                             label=f'Mean: {np.mean(quality_scores):.2f}')
            axes[0, 0].set_title('Trajectory Quality Distribution')
            axes[0, 0].set_xlabel('Quality Score')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].legend()
            
            # 2. Action type distribution
            action_dist = result.metrics.get("diversity_metrics", {}).get("action_type_distribution", {})
            if action_dist:
                actions, counts = zip(*action_dist.items())
                axes[0, 1].bar(range(len(actions)), counts, color='lightgreen')
                axes[0, 1].set_title('Action Type Distribution')
                axes[0, 1].set_xlabel('Action Type')
                axes[0, 1].set_ylabel('Count')
                axes[0, 1].set_xticks(range(len(actions)))
                axes[0, 1].set_xticklabels(actions, rotation=45, ha='right')
            
            # 3. Reward distribution
            all_rewards = []
            for traj in trajectories:
                for reward in traj.get("rewards", []):
                    if isinstance(reward, dict):
                        all_rewards.append(reward.get("quality_score", 0.5))
            
            if all_rewards:
                axes[1, 0].hist(all_rewards, bins=20, alpha=0.7, color='orange')
                axes[1, 0].axvline(np.mean(all_rewards), color='red', linestyle='--', 
                                 label=f'Mean: {np.mean(all_rewards):.2f}')
                axes[1, 0].set_title('Reward Distribution')
                axes[1, 0].set_xlabel('Reward Score')
                axes[1, 0].set_ylabel('Frequency')
                axes[1, 0].legend()
            
            # 4. Trajectory length distribution
            lengths = [len(t.get("actions", [])) for t in trajectories]
            axes[1, 1].hist(lengths, bins=15, alpha=0.7, color='purple')
            axes[1, 1].axvline(np.mean(lengths), color='red', linestyle='--', 
                             label=f'Mean: {np.mean(lengths):.1f}')
            axes[1, 1].set_title('Trajectory Length Distribution')
            axes[1, 1].set_xlabel('Number of Actions')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].legend()
            
            plt.tight_layout()
            
            if save_plots:
                plot_file = self.validation_dir / f"training_data_visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                print(f"📈 Visualization saved to: {plot_file}")
            
            plt.show()
            
            return {"visualization_created": True, "quality_scores": quality_scores}
            
        except ImportError:
            return {"error": "matplotlib/seaborn not available for visualization"}
        except Exception as e:
            return {"error": f"Visualization failed: {str(e)}"}

if __name__ == "__main__":
    # Demo usage
    validator = RLTrainingValidator()
    
    print("Running RL Training Data Validation...")
    
    # Validate data
    result = validator.validate_training_data()
    
    # Generate report
    report = validator.generate_quality_report()
    print(report)
    
    # Create visualizations (if matplotlib available)
    try:
        viz_result = validator.visualize_training_data()
        if "error" not in viz_result:
            print("📈 Visualizations created successfully!")
    except Exception as e:
        print(f"Visualization not available: {e}")