"""
Nationality Analysis - LLM Performance by Participant Nationality/Origin

This script analyzes whether the LLM performs differently when generating
responses for participants of different nationalities or origins.
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
plt.rcParams['figure.figsize'] = (16, 12)


def load_nationality_evaluations():
    """
    Load evaluation data with participant nationality for completed participants.
    
    Returns:
        DataFrame with columns: participant_id, nationality, agreement_score, 
                               authenticity_score, is_zero_shot, shot_type
    """
    db = get_db()
    
    with db as session:
        # Query evaluations with participant nationality for completed participants only
        query = session.query(
            Evaluation.participant_id,
            Participant.nationality,
            Participant.anonymous_id,
            Evaluation.agreement_score,
            Evaluation.authenticity_score,
            LLMGeneration.is_zero_shot
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
            columns=['participant_id', 'nationality', 'anonymous_id', 'agreement_score', 
                    'authenticity_score', 'is_zero_shot']
        )
        
        # Add readable shot type column
        df['shot_type'] = df['is_zero_shot'].map({
            True: 'Zero-Shot',
            False: 'Few-Shot'
        })
        
        return df


def print_statistics(df):
    """
    Print descriptive statistics by nationality and shot type.
    
    Args:
        df: DataFrame with evaluation data
    """
    print("="*80)
    print(" NATIONALITY ANALYSIS - LLM PERFORMANCE BY PARTICIPANT NATIONALITY")
    print("="*80)
    print()
    
    # Overall counts
    print(f"Total evaluations: {len(df)}")
    print(f"Unique participants: {df['participant_id'].nunique()}")
    print()
    
    # Nationality distribution
    print("Participants by nationality:")
    nationality_counts = df.groupby('nationality')['participant_id'].nunique().sort_values(ascending=False)
    for nationality, count in nationality_counts.items():
        print(f"  {nationality}: {count} participants")
    print()
    
    # Evaluations by nationality and shot type
    print("Evaluations by nationality and shot type:")
    eval_counts = df.groupby(['nationality', 'shot_type']).size().unstack(fill_value=0)
    print(eval_counts)
    print()
    
    # Statistics by nationality
    print("-"*80)
    print("AGREEMENT SCORES BY NATIONALITY")
    print("-"*80)
    agreement_by_nationality = df.groupby('nationality')['agreement_score'].describe()
    print(agreement_by_nationality.round(3))
    print()
    
    print("-"*80)
    print("AUTHENTICITY SCORES BY NATIONALITY")
    print("-"*80)
    authenticity_by_nationality = df.groupby('nationality')['authenticity_score'].describe()
    print(authenticity_by_nationality.round(3))
    print()
    
    # Statistics by nationality AND shot type
    print("-"*80)
    print("AGREEMENT SCORES BY NATIONALITY AND SHOT TYPE")
    print("-"*80)
    agreement_detailed = df.groupby(['nationality', 'shot_type'])['agreement_score'].agg(['mean', 'std', 'count'])
    print(agreement_detailed.round(3))
    print()
    
    print("-"*80)
    print("AUTHENTICITY SCORES BY NATIONALITY AND SHOT TYPE")
    print("-"*80)
    authenticity_detailed = df.groupby(['nationality', 'shot_type'])['authenticity_score'].agg(['mean', 'std', 'count'])
    print(authenticity_detailed.round(3))
    print()
    
    # Statistical tests - comparing nationalities (if there are 2 main groups)
    print("-"*80)
    print("STATISTICAL TESTS - NATIONALITY COMPARISON")
    print("-"*80)
    
    # Get the most common nationalities (for pairwise comparison if reasonable)
    top_nationalities = nationality_counts.head(5).index.tolist()
    
    if len(top_nationalities) >= 2:
        print("\nPairwise comparisons between top nationalities (Mann-Whitney U Test):")
        print()
        
        for i in range(len(top_nationalities)):
            for j in range(i + 1, len(top_nationalities)):
                nat1 = top_nationalities[i]
                nat2 = top_nationalities[j]
                
                n1_agreement = df[df['nationality'] == nat1]['agreement_score']
                n2_agreement = df[df['nationality'] == nat2]['agreement_score']
                
                if len(n1_agreement) >= 5 and len(n2_agreement) >= 5:  # Only test if sufficient data
                    u_stat, p_val = stats.mannwhitneyu(
                        n1_agreement, n2_agreement, alternative='two-sided'
                    )
                    
                    print(f"{nat1} vs {nat2} (Agreement):")
                    print(f"  {nat1}: mean={n1_agreement.mean():.3f}, SD={n1_agreement.std():.3f}, n={len(n1_agreement)}")
                    print(f"  {nat2}: mean={n2_agreement.mean():.3f}, SD={n2_agreement.std():.3f}, n={len(n2_agreement)}")
                    print(f"  Mean difference: {n1_agreement.mean() - n2_agreement.mean():.3f}")
                    print(f"  Mann-Whitney U: {u_stat:.1f}, p-value: {p_val:.4f}")
                    
                    if p_val < 0.05:
                        print(f"  → Significant difference (p < 0.05)")
                    else:
                        print(f"  → No significant difference")
                    print()
    
    # Few-shot improvement by nationality
    print("-"*80)
    print("FEW-SHOT IMPROVEMENT BY NATIONALITY")
    print("-"*80)
    print()
    
    for nationality in df['nationality'].unique():
        nat_df = df[df['nationality'] == nationality]
        
        zero_shot = nat_df[nat_df['is_zero_shot'] == True]['agreement_score']
        few_shot = nat_df[nat_df['is_zero_shot'] == False]['agreement_score']
        
        if len(zero_shot) > 0 and len(few_shot) > 0:
            improvement = few_shot.mean() - zero_shot.mean()
            
            # Test if improvement is significant
            u_stat, p_val = stats.mannwhitneyu(few_shot, zero_shot, alternative='greater')
            
            print(f"{nationality}:")
            print(f"  Zero-Shot: mean={zero_shot.mean():.3f}, SD={zero_shot.std():.3f}, n={len(zero_shot)}")
            print(f"  Few-Shot: mean={few_shot.mean():.3f}, SD={few_shot.std():.3f}, n={len(few_shot)}")
            print(f"  Improvement: {improvement:+.3f} points (p={p_val:.4f})")
            
            if p_val < 0.05:
                print(f"  → Significant improvement (p < 0.05)")
            else:
                print(f"  → No significant improvement")
            print()


def create_nationality_comparison_plot(df, output_file='nationality_analysis_comparison.png'):
    """
    Create comprehensive comparison visualization by nationality.
    
    Args:
        df: DataFrame with evaluation data
        output_file: Path to save the plot
    """
    # Sort nationalities by participant count
    nationality_order = df.groupby('nationality')['participant_id'].nunique().sort_values(ascending=False).index.tolist()
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.suptitle('LLM Performance by Participant Nationality', fontsize=16, fontweight='bold', y=0.995)
    
    # Use consistent colors
    colors_shot = {'Zero-Shot': '#FF6B6B', 'Few-Shot': '#4ECDC4'}
    
    # 1. Agreement scores by nationality (all shot types)
    ax1 = axes[0, 0]
    sns.boxplot(data=df, x='nationality', y='agreement_score', 
                ax=ax1, palette='Set2', order=nationality_order)
    ax1.set_title('Agreement Scores by Nationality (All Generation Types)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Nationality', fontsize=11)
    ax1.set_ylabel('Agreement Score (1-7)', fontsize=11)
    ax1.set_ylim(0, 8)
    ax1.grid(axis='y', alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Authenticity scores by nationality (all shot types)
    ax2 = axes[0, 1]
    sns.boxplot(data=df, x='nationality', y='authenticity_score', 
                ax=ax2, palette='Set2', order=nationality_order)
    ax2.set_title('Authenticity Scores by Nationality (All Generation Types)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Nationality', fontsize=11)
    ax2.set_ylabel('Authenticity Score (1-7)', fontsize=11)
    ax2.set_ylim(0, 8)
    ax2.grid(axis='y', alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Agreement by nationality and shot type
    ax3 = axes[1, 0]
    sns.boxplot(data=df, x='nationality', y='agreement_score', hue='shot_type',
                ax=ax3, palette=colors_shot, order=nationality_order)
    ax3.set_title('Agreement Scores by Nationality and Generation Type', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Nationality', fontsize=11)
    ax3.set_ylabel('Agreement Score (1-7)', fontsize=11)
    ax3.set_ylim(0, 8)
    ax3.legend(title='Generation Type', loc='lower right')
    ax3.grid(axis='y', alpha=0.3)
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. Authenticity by nationality and shot type
    ax4 = axes[1, 1]
    sns.boxplot(data=df, x='nationality', y='authenticity_score', hue='shot_type',
                ax=ax4, palette=colors_shot, order=nationality_order)
    ax4.set_title('Authenticity Scores by Nationality and Generation Type', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Nationality', fontsize=11)
    ax4.set_ylabel('Authenticity Score (1-7)', fontsize=11)
    ax4.set_ylim(0, 8)
    ax4.legend(title='Generation Type', loc='lower right')
    ax4.grid(axis='y', alpha=0.3)
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved comparison plot: {output_file}")
    plt.close()


def create_improvement_plot(df, output_file='nationality_improvement_plot.png'):
    """
    Create a plot showing few-shot improvement by nationality.
    
    Args:
        df: DataFrame with evaluation data
        output_file: Path to save the plot
    """
    # Calculate improvements for each nationality
    improvements = []
    
    for nationality in df['nationality'].unique():
        nat_df = df[df['nationality'] == nationality]
        
        zero_shot_agreement = nat_df[nat_df['is_zero_shot'] == True]['agreement_score'].mean()
        few_shot_agreement = nat_df[nat_df['is_zero_shot'] == False]['agreement_score'].mean()
        agreement_improvement = few_shot_agreement - zero_shot_agreement
        
        zero_shot_authenticity = nat_df[nat_df['is_zero_shot'] == True]['authenticity_score'].mean()
        few_shot_authenticity = nat_df[nat_df['is_zero_shot'] == False]['authenticity_score'].mean()
        authenticity_improvement = few_shot_authenticity - zero_shot_authenticity
        
        n_participants = nat_df['participant_id'].nunique()
        
        improvements.append({
            'nationality': nationality,
            'agreement_improvement': agreement_improvement,
            'authenticity_improvement': authenticity_improvement,
            'n_participants': n_participants
        })
    
    improvements_df = pd.DataFrame(improvements).sort_values('agreement_improvement', ascending=False)
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Few-Shot Improvement by Nationality', fontsize=16, fontweight='bold')
    
    # Agreement improvement
    colors_agreement = ['#4ECDC4' if x >= 0 else '#FF6B6B' for x in improvements_df['agreement_improvement']]
    ax1.barh(improvements_df['nationality'], improvements_df['agreement_improvement'], color=colors_agreement)
    ax1.axvline(x=0, color='black', linestyle='--', linewidth=1)
    ax1.set_xlabel('Few-Shot Improvement (points)', fontsize=11)
    ax1.set_ylabel('Nationality', fontsize=11)
    ax1.set_title('Agreement Score Improvement', fontsize=12, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (idx, row) in enumerate(improvements_df.iterrows()):
        value = row['agreement_improvement']
        ax1.text(value, i, f' {value:+.2f}', va='center', ha='left' if value >= 0 else 'right')
    
    # Authenticity improvement
    colors_authenticity = ['#4ECDC4' if x >= 0 else '#FF6B6B' for x in improvements_df['authenticity_improvement']]
    ax2.barh(improvements_df['nationality'], improvements_df['authenticity_improvement'], color=colors_authenticity)
    ax2.axvline(x=0, color='black', linestyle='--', linewidth=1)
    ax2.set_xlabel('Few-Shot Improvement (points)', fontsize=11)
    ax2.set_ylabel('Nationality', fontsize=11)
    ax2.set_title('Authenticity Score Improvement', fontsize=12, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (idx, row) in enumerate(improvements_df.iterrows()):
        value = row['authenticity_improvement']
        ax2.text(value, i, f' {value:+.2f}', va='center', ha='left' if value >= 0 else 'right')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved improvement plot: {output_file}")
    plt.close()


def create_interaction_plot(df, output_file='nationality_interaction_plot.png'):
    """
    Create interaction plots showing how shot type effect varies by nationality.
    
    Args:
        df: DataFrame with evaluation data
        output_file: Path to save the plot
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Shot Type × Nationality Interaction Effects', fontsize=16, fontweight='bold')
    
    # Calculate means and standard errors
    grouped = df.groupby(['nationality', 'shot_type']).agg({
        'agreement_score': ['mean', 'std', 'count'],
        'authenticity_score': ['mean', 'std', 'count']
    })
    
    # Agreement interaction
    for nationality in df['nationality'].unique():
        try:
            zero_mean = grouped.loc[(nationality, 'Zero-Shot'), ('agreement_score', 'mean')]
            few_mean = grouped.loc[(nationality, 'Few-Shot'), ('agreement_score', 'mean')]
            
            zero_std = grouped.loc[(nationality, 'Zero-Shot'), ('agreement_score', 'std')]
            few_std = grouped.loc[(nationality, 'Few-Shot'), ('agreement_score', 'std')]
            
            zero_n = grouped.loc[(nationality, 'Zero-Shot'), ('agreement_score', 'count')]
            few_n = grouped.loc[(nationality, 'Few-Shot'), ('agreement_score', 'count')]
            
            zero_se = zero_std / (zero_n ** 0.5)
            few_se = few_std / (few_n ** 0.5)
            
            ax1.plot(['Zero-Shot', 'Few-Shot'], [zero_mean, few_mean], 
                    marker='o', linewidth=2, markersize=8, label=nationality)
            ax1.errorbar(['Zero-Shot', 'Few-Shot'], [zero_mean, few_mean],
                        yerr=[zero_se, few_se], fmt='none', capsize=5, alpha=0.5)
        except KeyError:
            continue
    
    ax1.set_xlabel('Generation Type', fontsize=11)
    ax1.set_ylabel('Agreement Score (Mean ± SE)', fontsize=11)
    ax1.set_title('Agreement Score: Interaction Effect', fontsize=12, fontweight='bold')
    ax1.legend(title='Nationality', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(alpha=0.3)
    ax1.set_ylim(0, 8)
    
    # Authenticity interaction
    for nationality in df['nationality'].unique():
        try:
            zero_mean = grouped.loc[(nationality, 'Zero-Shot'), ('authenticity_score', 'mean')]
            few_mean = grouped.loc[(nationality, 'Few-Shot'), ('authenticity_score', 'mean')]
            
            zero_std = grouped.loc[(nationality, 'Zero-Shot'), ('authenticity_score', 'std')]
            few_std = grouped.loc[(nationality, 'Few-Shot'), ('authenticity_score', 'std')]
            
            zero_n = grouped.loc[(nationality, 'Zero-Shot'), ('authenticity_score', 'count')]
            few_n = grouped.loc[(nationality, 'Few-Shot'), ('authenticity_score', 'count')]
            
            zero_se = zero_std / (zero_n ** 0.5)
            few_se = few_std / (few_n ** 0.5)
            
            ax2.plot(['Zero-Shot', 'Few-Shot'], [zero_mean, few_mean], 
                    marker='o', linewidth=2, markersize=8, label=nationality)
            ax2.errorbar(['Zero-Shot', 'Few-Shot'], [zero_mean, few_mean],
                        yerr=[zero_se, few_se], fmt='none', capsize=5, alpha=0.5)
        except KeyError:
            continue
    
    ax2.set_xlabel('Generation Type', fontsize=11)
    ax2.set_ylabel('Authenticity Score (Mean ± SE)', fontsize=11)
    ax2.set_title('Authenticity Score: Interaction Effect', fontsize=12, fontweight='bold')
    ax2.legend(title='Nationality', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(alpha=0.3)
    ax2.set_ylim(0, 8)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved interaction plot: {output_file}")
    plt.close()


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print(" NATIONALITY ANALYSIS")
    print("="*80 + "\n")
    
    # Load data
    print("Loading evaluation data...")
    df = load_nationality_evaluations()
    print(f"✓ Loaded {len(df)} evaluations from {df['participant_id'].nunique()} participants")
    print()
    
    # Check if we have data
    if len(df) == 0:
        print("⚠ No evaluation data found for completed participants.")
        return
    
    # Print statistics
    print_statistics(df)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    create_nationality_comparison_plot(df)
    create_improvement_plot(df)
    create_interaction_plot(df)
    
    print("\n" + "="*80)
    print(" ANALYSIS COMPLETE")
    print("="*80)
    print("\nGenerated files:")
    print("  - nationality_analysis_comparison.png")
    print("  - nationality_improvement_plot.png")
    print("  - nationality_interaction_plot.png")
    print()


if __name__ == "__main__":
    main()
