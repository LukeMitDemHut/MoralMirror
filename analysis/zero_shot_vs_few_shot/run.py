"""
Zero-Shot vs Few-Shot Analysis

This script analyzes the evaluation scores for completed participants,
comparing zero-shot and few-shot LLM generations.
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from database import get_db
from models import Participant, Evaluation, LLMGeneration

# Configure visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)


def load_completed_evaluations():
    """
    Load evaluation data for participants who completed the study.
    
    Returns:
        DataFrame with columns: participant_id, agreement_score, authenticity_score, 
                               is_zero_shot, shot_type
    """
    db = get_db()
    
    with db as session:
        # Query evaluations for completed participants only
        query = session.query(
            Evaluation.participant_id,
            Evaluation.agreement_score,
            Evaluation.authenticity_score,
            LLMGeneration.is_zero_shot,
            Participant.anonymous_id
        ).join(
            LLMGeneration,
            Evaluation.generation_id == LLMGeneration.id
        ).join(
            Participant,
            Evaluation.participant_id == Participant.id
        ).filter(
            Participant.current_phase == 'completed'
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(
            query.all(),
            columns=['participant_id', 'agreement_score', 'authenticity_score', 
                    'is_zero_shot', 'anonymous_id']
        )
        
        # Add readable shot type column
        df['shot_type'] = df['is_zero_shot'].map({
            True: 'Zero-Shot',
            False: 'Few-Shot'
        })
        
        return df


def print_statistics(df):
    """
    Print descriptive statistics for both shot types.
    
    Args:
        df: DataFrame with evaluation data
    """
    print("="*80)
    print(" ZERO-SHOT vs FEW-SHOT ANALYSIS - COMPLETED PARTICIPANTS")
    print("="*80)
    print()
    
    # Overall counts
    print(f"Total evaluations: {len(df)}")
    print(f"Unique participants: {df['participant_id'].nunique()}")
    print()
    
    # Counts by shot type
    print("Evaluations by type:")
    print(df['shot_type'].value_counts())
    print()
    
    # Descriptive statistics by shot type
    print("-"*80)
    print("AGREEMENT SCORES")
    print("-"*80)
    agreement_stats = df.groupby('shot_type')['agreement_score'].describe()
    print(agreement_stats.round(3))
    print()
    
    print("-"*80)
    print("AUTHENTICITY SCORES")
    print("-"*80)
    authenticity_stats = df.groupby('shot_type')['authenticity_score'].describe()
    print(authenticity_stats.round(3))
    print()
    
    # Statistical tests
    print("-"*80)
    print("STATISTICAL TESTS (Mann-Whitney U Test)")
    print("-"*80)
    
    few_shot_agreement = df[df['shot_type'] == 'Few-Shot']['agreement_score']
    zero_shot_agreement = df[df['shot_type'] == 'Zero-Shot']['agreement_score']
    
    few_shot_authenticity = df[df['shot_type'] == 'Few-Shot']['authenticity_score']
    zero_shot_authenticity = df[df['shot_type'] == 'Zero-Shot']['authenticity_score']
    
    # Agreement test
    u_stat_agreement, p_val_agreement = stats.mannwhitneyu(
        few_shot_agreement, 
        zero_shot_agreement, 
        alternative='two-sided'
    )
    
    print(f"Agreement Scores:")
    print(f"  Few-Shot mean: {few_shot_agreement.mean():.3f} (SD: {few_shot_agreement.std():.3f})")
    print(f"  Zero-Shot mean: {zero_shot_agreement.mean():.3f} (SD: {zero_shot_agreement.std():.3f})")
    print(f"  Difference: {few_shot_agreement.mean() - zero_shot_agreement.mean():.3f}")
    print(f"  U-statistic: {u_stat_agreement:.2f}, p-value: {p_val_agreement:.4f}")
    
    if p_val_agreement < 0.001:
        print(f"  Result: Highly significant difference (p < 0.001) ***")
    elif p_val_agreement < 0.01:
        print(f"  Result: Very significant difference (p < 0.01) **")
    elif p_val_agreement < 0.05:
        print(f"  Result: Significant difference (p < 0.05) *")
    else:
        print(f"  Result: No significant difference (p >= 0.05)")
    print()
    
    # Authenticity test
    u_stat_authenticity, p_val_authenticity = stats.mannwhitneyu(
        few_shot_authenticity, 
        zero_shot_authenticity, 
        alternative='two-sided'
    )
    
    print(f"Authenticity Scores:")
    print(f"  Few-Shot mean: {few_shot_authenticity.mean():.3f} (SD: {few_shot_authenticity.std():.3f})")
    print(f"  Zero-Shot mean: {zero_shot_authenticity.mean():.3f} (SD: {zero_shot_authenticity.std():.3f})")
    print(f"  Difference: {few_shot_authenticity.mean() - zero_shot_authenticity.mean():.3f}")
    print(f"  U-statistic: {u_stat_authenticity:.2f}, p-value: {p_val_authenticity:.4f}")
    
    if p_val_authenticity < 0.001:
        print(f"  Result: Highly significant difference (p < 0.001) ***")
    elif p_val_authenticity < 0.01:
        print(f"  Result: Very significant difference (p < 0.01) **")
    elif p_val_authenticity < 0.05:
        print(f"  Result: Significant difference (p < 0.05) *")
    else:
        print(f"  Result: No significant difference (p >= 0.05)")
    print()


def create_visualizations(df):
    """
    Create boxplot visualizations comparing zero-shot and few-shot.
    
    Args:
        df: DataFrame with evaluation data
    """
    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Define colors
    colors = {'Few-Shot': '#2ecc71', 'Zero-Shot': '#e74c3c'}
    
    # Agreement scores boxplot
    sns.boxplot(
        data=df, 
        x='shot_type', 
        y='agreement_score', 
        ax=axes[0],
        hue='shot_type',
        palette=colors,
        order=['Few-Shot', 'Zero-Shot'],
        legend=False
    )
    axes[0].set_title('Agreement Scores by Generation Type', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Generation Type', fontsize=12)
    axes[0].set_ylabel('Agreement Score (1-7)', fontsize=12)
    axes[0].set_ylim(0.5, 7.5)
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add mean markers
    means_agreement = df.groupby('shot_type')['agreement_score'].mean()
    for i, shot_type in enumerate(['Few-Shot', 'Zero-Shot']):
        axes[0].plot(i, means_agreement[shot_type], 'D', color='white', 
                    markeredgecolor='black', markersize=8, zorder=3,
                    label='Mean' if i == 0 else '')
    
    # Authenticity scores boxplot
    sns.boxplot(
        data=df, 
        x='shot_type', 
        y='authenticity_score', 
        ax=axes[1],
        hue='shot_type',
        palette=colors,
        order=['Few-Shot', 'Zero-Shot'],
        legend=False
    )
    axes[1].set_title('Authenticity Scores by Generation Type', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Generation Type', fontsize=12)
    axes[1].set_ylabel('Authenticity Score (1-7)', fontsize=12)
    axes[1].set_ylim(0.5, 7.5)
    axes[1].grid(axis='y', alpha=0.3)
    
    # Add mean markers
    means_authenticity = df.groupby('shot_type')['authenticity_score'].mean()
    for i, shot_type in enumerate(['Few-Shot', 'Zero-Shot']):
        axes[1].plot(i, means_authenticity[shot_type], 'D', color='white', 
                    markeredgecolor='black', markersize=8, zorder=3,
                    label='Mean' if i == 0 else '')
    
    # Add legend to first plot
    axes[0].legend(loc='lower left', fontsize=10)
    
    # Add sample size annotations
    for ax in axes:
        y_pos = 0.8
        for i, shot_type in enumerate(['Few-Shot', 'Zero-Shot']):
            n = len(df[df['shot_type'] == shot_type])
            ax.text(i, y_pos, f'n={n}', ha='center', va='center',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                   fontsize=9)
    
    plt.tight_layout()
    
    # Save figure
    output_file = 'zero_shot_vs_few_shot_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_file}")
    
    # Also create a combined distribution plot
    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
    
    # Agreement violin plot
    sns.violinplot(
        data=df, 
        x='shot_type', 
        y='agreement_score', 
        ax=axes2[0, 0],
        hue='shot_type',
        palette=colors,
        order=['Few-Shot', 'Zero-Shot'],
        legend=False
    )
    axes2[0, 0].set_title('Agreement Score Distribution', fontsize=12, fontweight='bold')
    axes2[0, 0].set_xlabel('')
    axes2[0, 0].set_ylabel('Agreement Score (1-7)')
    axes2[0, 0].grid(axis='y', alpha=0.3)
    
    # Authenticity violin plot
    sns.violinplot(
        data=df, 
        x='shot_type', 
        y='authenticity_score', 
        ax=axes2[0, 1],
        hue='shot_type',
        palette=colors,
        order=['Few-Shot', 'Zero-Shot'],
        legend=False
    )
    axes2[0, 1].set_title('Authenticity Score Distribution', fontsize=12, fontweight='bold')
    axes2[0, 1].set_xlabel('')
    axes2[0, 1].set_ylabel('Authenticity Score (1-7)')
    axes2[0, 1].grid(axis='y', alpha=0.3)
    
    # Agreement histogram
    for shot_type in ['Few-Shot', 'Zero-Shot']:
        data = df[df['shot_type'] == shot_type]['agreement_score']
        axes2[1, 0].hist(data, bins=7, alpha=0.6, label=shot_type, 
                        color=colors[shot_type], edgecolor='black')
    axes2[1, 0].set_title('Agreement Score Frequency', fontsize=12, fontweight='bold')
    axes2[1, 0].set_xlabel('Agreement Score')
    axes2[1, 0].set_ylabel('Count')
    axes2[1, 0].legend()
    axes2[1, 0].grid(axis='y', alpha=0.3)
    
    # Authenticity histogram
    for shot_type in ['Few-Shot', 'Zero-Shot']:
        data = df[df['shot_type'] == shot_type]['authenticity_score']
        axes2[1, 1].hist(data, bins=7, alpha=0.6, label=shot_type, 
                        color=colors[shot_type], edgecolor='black')
    axes2[1, 1].set_title('Authenticity Score Frequency', fontsize=12, fontweight='bold')
    axes2[1, 1].set_xlabel('Authenticity Score')
    axes2[1, 1].set_ylabel('Count')
    axes2[1, 1].legend()
    axes2[1, 1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    output_file2 = 'zero_shot_vs_few_shot_distributions.png'
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"✓ Distribution plots saved to: {output_file2}")
    
    print()


def main():
    """Main analysis function."""
    print("\nLoading data for completed participants...")
    df = load_completed_evaluations()
    
    if len(df) == 0:
        print("No data found for completed participants.")
        return
    
    print(f"✓ Loaded {len(df)} evaluations from {df['participant_id'].nunique()} completed participants\n")
    
    # Print statistics
    print_statistics(df)
    
    # Create visualizations
    print("-"*80)
    print("CREATING VISUALIZATIONS")
    print("-"*80)
    create_visualizations(df)
    
    print()
    print("="*80)
    print(" ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
