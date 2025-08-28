# RL Data Collection Guide for Document Formatting System

## 🎯 Overview

This guide explains how to collect team actions as State-Action-Reward (SAR) trajectories for training reinforcement learning models on document formatting tasks. The system captures real-time team interactions, manual corrections, and quality feedback to create high-quality training data.

## 📊 System Architecture

### Core Components

1. **`rl_data_collector.py`** - Main data collection engine
   - Captures SAR trajectories in standard RL format
   - Records document states, formatting actions, and quality rewards
   - Handles episode management and data persistence

2. **`team_interaction_tracker.py`** - Team collaboration capture
   - Records manual corrections and user feedback
   - Tracks approval/rejection decisions
   - Captures team disagreements and consensus
   - Optional GUI for real-time feedback collection

3. **`rl_training_validator.py`** - Data quality validation
   - Validates trajectory completeness and consistency
   - Calculates quality metrics and recommendations
   - Generates quality reports and visualizations

## 🚀 Quick Start

### 1. Basic Data Collection
```python
from rl_data_collector import RLDataCollector

# Initialize collector
collector = RLDataCollector()

# Start episode
episode_id = collector.start_episode(
    user_id="team_lead",
    document_path="/path/to/document.docx",
    method_used="multi_stage"
)

# Record actions during formatting
collector.record_action(
    action_type="filter_navigation",
    parameters={"filtered_count": 25},
    confidence=0.9,
    method_used="rule_based"
)

# Record quality feedback
collector.record_reward(
    quality_score=0.85,
    compliance_score=0.9,
    efficiency_metric=0.8
)

# End episode
summary = collector.end_episode(
    output_document_path="/path/to/formatted.docx",
    final_quality_score=0.85
)
```

### 2. Team Collaboration Tracking
```python
from team_interaction_tracker import TeamInteractionTracker

# Initialize tracker
tracker = TeamInteractionTracker()

# Start team session
session_id = tracker.start_team_session(
    team_members=["alice", "bob", "charlie"],
    document_path="/path/to/document.docx"
)

# Record manual correction
tracker.record_manual_correction(
    user_id="alice",
    paragraph_index=5,
    original_text="Original paragraph text",
    corrected_text="Corrected paragraph text",
    original_style="Normal",
    corrected_style="Body Text",
    reasoning="Better semantic structure",
    confidence=0.9
)

# End session
summary = tracker.end_team_session(
    final_approval=True,
    session_notes="Good collaborative session"
)
```

### 3. Data Quality Validation
```python
from rl_training_validator import RLTrainingValidator

# Initialize validator
validator = RLTrainingValidator()

# Validate collected data
result = validator.validate_training_data()

print(f"Data Quality: {result.quality_score:.2f}")
print(f"Issues: {len(result.issues)}")
print(f"Recommendations: {len(result.recommendations)}")

# Generate report
report = validator.generate_quality_report()
print(report)
```

## 📋 Data Structure

### State Representation
```python
DocumentState = {
    "paragraph_count": int,
    "style_distribution": Dict[str, int],
    "filtered_content_count": int,
    "document_complexity": float,
    "current_stage": str,
    "formatting_rules_applied": List[str],
    "user_preferences": Dict[str, Any],
    "document_type": str,
    "timestamp": str
}
```

### Action Representation
```python
FormattingAction = {
    "action_type": str,  # 'filter', 'classify', 'style_change', 'manual_correction'
    "parameters": Dict[str, Any],
    "confidence": float,
    "method_used": str,  # 'rule_based', 'llm', 'pattern_match', 'manual'
    "paragraph_index": int,
    "original_text": str,
    "applied_style": str,
    "timestamp": str
}
```

### Reward Representation
```python
Reward = {
    "quality_score": float,  # 0.0 to 1.0
    "user_satisfaction": Optional[float],
    "compliance_score": float,
    "efficiency_metric": float,
    "error_reduction": float,
    "manual_corrections_needed": int,
    "timestamp": str
}
```

## 🔧 Integration with Existing Formatters

### Multi-Stage Formatter Integration
```python
from rl_data_collector import RLDataCollector, integrate_with_multi_stage_formatter

# Create RL-enabled formatter
rl_formatter = integrate_with_multi_stage_formatter().RLEnabledMultiStageFormatter()

# Format document with data collection
processed, filtered, style_counts, rl_summary = rl_formatter.format_document_with_rl(
    input_path="original.docx",
    output_path="formatted.docx",
    user_id="system",
    known_path="target.docx"
)

print(f"RL Data Summary: {rl_summary}")
```

### Team Interactive Formatter
```python
from team_interaction_tracker import create_interactive_formatter

# Create interactive formatter
interactive_formatter = create_interactive_formatter().InteractiveTeamFormatter()

# Format with team feedback
results = interactive_formatter.format_document_with_team_feedback(
    input_path="original.docx",
    output_path="formatted.docx",
    team_members=["alice", "bob"],
    interactive=True
)

print(f"Team Session Results: {results['team_session']}")
```

## 📊 Data Types to Collect

### 1. Automatic System Actions
- **Content Filtering**: Navigation removal, header/footer filtering
- **Style Classification**: Heading detection, paragraph categorization
- **Template Application**: Style rule application
- **Quality Validation**: Compliance checking

### 2. Manual Team Actions
- **Corrections**: Style changes, text modifications
- **Approvals**: Quality acceptance/rejection
- **Feedback**: Satisfaction ratings, improvement suggestions
- **Consensus**: Team agreement on formatting decisions

### 3. Quality Metrics
- **Compliance Scores**: Adherence to formatting standards
- **User Satisfaction**: Team member satisfaction ratings
- **Efficiency Metrics**: Time saved vs. manual formatting
- **Error Reduction**: Decrease in formatting errors

## 🎯 Reward Design Strategies

### 1. Verifiable Rewards
- **Compliance Gates**: Pass/fail on style guidelines
- **Template Matching**: Similarity to known good formats
- **User Approval**: Direct team feedback scores

### 2. Efficiency Rewards
- **Time Savings**: Processing speed vs. manual formatting
- **Correction Reduction**: Fewer manual fixes needed
- **Consistency**: Uniform formatting across documents

### 3. Quality Rewards
- **Professional Appearance**: Visual formatting quality
- **Structure Clarity**: Logical document organization
- **Accessibility**: Compliance with accessibility standards

## 📈 Training Data Export Formats

### 1. Trajectory Format (Standard RL)
```python
trajectory = {
    "episode_id": "episode_123",
    "states": [state1, state2, state3, ...],
    "actions": [action1, action2, ...],
    "rewards": [reward1, reward2, ...],
    "metadata": {"user_preferences": {...}}
}
```

### 2. State-Action Pairs
```python
pairs = [
    {
        "state": state1,
        "action": action1,
        "reward": reward1,
        "next_state": state2,
        "episode_id": "episode_123"
    },
    ...
]
```

### 3. Team Collaboration Data
```python
team_data = {
    "session_id": "team_session_456",
    "interactions": [interaction1, interaction2, ...],
    "consensus_decisions": [...],
    "disagreements": [...],
    "collaboration_metrics": {...}
}
```

## 🔍 Quality Validation

### Quality Thresholds
- **Minimum trajectory length**: 3 actions
- **Minimum reward variance**: 0.05
- **Maximum missing rewards**: 10%
- **Minimum action diversity**: 2 unique types
- **Minimum quality score**: 0.6

### Validation Checks
1. **Completeness**: All SAR sequences complete
2. **Consistency**: Actions align with states
3. **Informativeness**: Rewards provide learning signal
4. **Diversity**: Varied action types and methods

### Quality Reports
- Automatic validation on data collection
- Visual quality reports with charts
- Recommendations for improvement
- Export summaries for monitoring

## 📁 Data Storage Structure

```
rl_training_data/
├── episodes.jsonl          # Complete episode data
├── states.jsonl           # Individual states
├── actions.jsonl          # Individual actions
├── rewards.jsonl          # Individual rewards
├── metadata.json          # Overall statistics
└── events.log             # Processing events

team_interaction_data/
├── interactions.jsonl     # User interactions
├── team_sessions.jsonl    # Complete sessions
└── events.log            # Team events

rl_validation_results/
├── validation_result_TIMESTAMP.json
├── latest_validation_summary.json
├── quality_report_TIMESTAMP.txt
└── training_data_visualization_TIMESTAMP.png
```

## 🚦 Usage Guidelines

### Best Practices
1. **Start with simple scenarios** - Single user, short documents
2. **Gradually add complexity** - Multi-user, complex documents
3. **Monitor data quality** - Regular validation checks
4. **Balance action types** - Ensure diverse training data
5. **Capture user context** - Document preferences and constraints

### Common Pitfalls
- **Insufficient trajectory length** - Need multiple actions per episode
- **Biased action distribution** - Oversampling certain action types
- **Poor reward design** - Uninformative or constant rewards
- **Missing user feedback** - Lack of ground truth quality scores

### Debugging Tips
- Use validation reports to identify data quality issues
- Monitor action diversity and reward variance
- Check for missing state-action-reward alignments
- Verify user interaction capture completeness

## 🔄 Continuous Improvement

### Data Collection Optimization
1. **Iterative refinement** of reward functions
2. **Active learning** to focus on challenging cases
3. **User feedback incorporation** for reward calibration
4. **Automated quality monitoring** with alerts

### Training Data Enhancement
1. **Data augmentation** for rare scenarios
2. **Synthetic trajectory generation** for edge cases
3. **Multi-modal data integration** (text + visual feedback)
4. **Cross-validation** with held-out test sets

## 📚 Advanced Features

### Real-time GUI Feedback
- Optional tkinter interface for team feedback
- Real-time action capture during formatting
- Instant quality score collection
- Team collaboration visualization

### Batch Processing
- Bulk episode processing for large document sets
- Automated quality validation pipelines
- Scheduled data collection and validation
- Integration with existing CI/CD workflows

### Analytics Dashboard
- Training data quality monitoring
- Team performance metrics
- Action type distribution analysis
- Reward function effectiveness tracking

## 🎉 Expected Outcomes

### Training Data Quality
- **High-quality trajectories** with clear SAR sequences
- **Diverse action coverage** across formatting scenarios
- **Meaningful rewards** that drive learning
- **Team collaboration insights** for system improvement

### Model Training Benefits
- **Faster convergence** with quality training data
- **Better generalization** across document types
- **Human-aligned preferences** from team feedback
- **Continuous improvement** through ongoing data collection

## 📞 Support and Troubleshooting

### Common Issues
1. **Import errors** - Ensure all dependencies installed
2. **File path issues** - Use absolute paths for documents
3. **GUI problems** - tkinter may not be available on all systems
4. **Data validation failures** - Check trajectory completeness

### Getting Help
1. Check validation reports for specific issues
2. Review generated quality recommendations
3. Examine event logs for processing errors
4. Test with simple examples before complex scenarios

This comprehensive system provides everything needed to collect high-quality RL training data from team document formatting workflows!