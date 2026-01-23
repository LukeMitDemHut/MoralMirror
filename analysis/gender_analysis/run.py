"""
Gender Analysis - LLM Performance by Participant Gender

This script analyzes whether the LLM performs differently when generating
responses for participants of different genders.
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
plt.rcParams['figure.figsize'] = (16, 10)


def load_gender_evaluations():
    """
    Load evaluation data with participant gender for completed participants.
    
    Returns:
        DataFrame with columns: participant_id, gender, agreement_score, 
                               authenticity_score, is_zero_shot, shot_type
    """
    db = get_db()
    
    with db as session:
        # Query evaluations with participant gender for completed participants only
        query = session.query(
            Evaluation.participant_id,
            Participant.gender,
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
            columns=['participant_id', 'gender', 'anonymous_id', 'agreement_score', 
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
    Print descriptive statistics by gender and shot type.
    
    Args:
        df: DataFrame with evaluation data
    """
    print("="*80)
    print(" GENDER ANALYSIS - LLM PERFORMANCE BY PARTICIPANT GENDER")
    print("="*80)
    print()
    
    # Overall counts
    print(f"Total evaluations: {len(df)}")
    print(f"Unique participants: {df['participant_id'].nunique()}")
    print()
    
    # Gender distribution
    print("Participants by gender:")
    gender_counts = df.groupby('gender')['participant_id'].nunique()
    for gender, count in gender_counts.items():
        print(f"  {gender}: {count} participants")
    print()
    
    # Evaluations by gender and shot type
    print("Evaluations by gender and shot type:")
    eval_counts = df.groupby(['gender', 'shot_type']).size().unstack(fill_value=0)
    print(eval_counts)
    print()
    
    # Statistics by gender
    print("-"*80)
    print("AGREEMENT SCORES BY GENDER")
    print("-"*80)
    agreement_by_gender = df.groupby('gender')['agreement_score'].describe()
    print(agreement_by_gender.round(3))
    print()
    
    print("-"*80)
    print("AUTHENTICITY SCORES BY GENDER")
    print("-"*80)
    authenticity_by_gender = df.groupby('gender')['authenticity_score'].describe()
    print(authenticity_by_gender.round(3))
    print()
    
    # Statistics by gender AND shot type
    print("-"*80)
    print("AGREEMENT SCORES BY GENDER AND SHOT TYPE")
    print("-"*80)
    agreement_detailed = df.groupby(['gender', 'shot_type'])['agreement_score'].agg(['mean', 'std', 'count'])
    print(agreement_detailed.round(3))
    print()
    
    print("-"*80)
    print("AUTHENTICITY SCORES BY GENDER AND SHOT TYPE")
    print("-"*80)
    authenticity_detailed = df.groupby(['gender', 'shot_type'])['authenticity_score'].agg(['mean', 'std', 'count'])
    print(authenticity_detailed.round(3))
    print()
    
    # Statistical tests - comparing genders
    print("-"*80)
    print("STATISTICAL TESTS - GENDER COMPARISON (Mann-Whitney U Test)")
    print("-"*80)
    
    genders = df['gender'].unique()
    if len(genders) == 2:
        gender1, gender2 = sorted(genders)
        
        # Agreement scores by gender (overall)
        g1_agreement = df[df['gender'] == gender1]['agreement_score']
        g2_agreement = df[df['gender'] == gender2]['agreement_score']
        
        u_stat_agreement, p_val_agreement = stats.mannwhitneyu(
            g1_agreement, g2_agreement, alternative='two-sided'
        )
        
        print(f"\nAgreement Scores (Overall):")
        print(f"  {gender1}: mean={g1_agreement.mean():.3f}, SD={g1_agreement.std():.3f}, n={len(g1_agreement)}")
        print(f"  {gender2}: mean={g2_agreement.mean():.3f}, SD={g2_agreement.std():.3f}, n={len(g2_agreement)}")
        print(f"  Difference: {g1_agreement.mean() - g2_agreement.mean():.3f}")
        print(f"  U-statistic: {u_stat_agreement:.2f}, p-value: {p_val_agreement:.4f}")
        
        if p_val_agreement < 0.001:
            print(f"  Result: Highly significant difference (p < 0.001) ***")
        elif p_val_agreement < 0.01:
            print(f"  Result: Very significant difference (p < 0.01) **")
        elif p_val_agreement < 0.05:
            print(f"  Result: Significant difference (p < 0.05) *")
        else:
            print(f"  Result: No significant difference (p >= 0.05)")
        
        # Authenticity scores by gender (overall)
        g1_authenticity = df[df['gender'] == gender1]['authenticity_score']
        g2_authenticity = df[df['gender'] == gender2]['authenticity_score']
        
        u_stat_authenticity, p_val_authenticity = stats.mannwhitneyu(
            g1_authenticity, g2_authenticity, alternative='two-sided'
        )
        
        print(f"\nAuthenticity Scores (Overall):")
        print(f"  {gender1}: mean={g1_authenticity.mean():.3f}, SD={g1_authenticity.std():.3f}, n={len(g1_authenticity)}")
        print(f"  {gender2}: mean={g2_authenticity.mean():.3f}, SD={g2_authenticity.std():.3f}, n={len(g2_authenticity)}")
        print(f"  Difference: {g1_authenticity.mean() - g2_authenticity.mean():.3f}")
        print(f"  U-statistic: {u_stat_authenticity:.2f}, p-value: {p_val_authenticity:.4f}")
        
        if p_val_authenticity < 0.001:
            print(f"  Result: Highly significant difference (p < 0.001) ***")
        elif p_val_authenticity < 0.01:
            print(f"  Result: Very significant difference (p < 0.01) **")
        elif p_val_authenticity < 0.05:
            print(f"  Result: Significant difference (p < 0.05) *")
        else:
            print(f"  Result: No significant difference (p >= 0.05)")
        
        # Test within each shot type
        print(f"\n{'-'*40}")
        print("BY SHOT TYPE:")
        print('-'*40)
        
        for shot_type in ['Few-Shot', 'Zero-Shot']:
            df_shot = df[df['shot_type'] == shot_type]
            
            g1_agreement_shot = df_shot[df_shot['gender'] == gender1]['agreement_score']
            g2_agreement_shot = df_shot[df_shot['gender'] == gender2]['agreement_score']
            
            if len(g1_agreement_shot) > 0 and len(g2_agreement_shot) > 0:
                u_stat, p_val = stats.mannwhitneyu(
                    g1_agreement_shot, g2_agreement_shot, alternative='two-sided'
                )
                
                print(f"\n{shot_type} - Agreement:")
                print(f"  {gender1}: {g1_agreement_shot.mean():.3f} ± {g1_agreement_shot.std():.3f} (n={len(g1_agreement_shot)})")
                print(f"  {gender2}: {g2_agreement_shot.mean():.3f} ± {g2_agreement_shot.std():.3f} (n={len(g2_agreement_shot)})")
                print(f"  p-value: {p_val:.4f}", end="")
                if p_val < 0.05:
                    print(" *" if p_val < 0.05 else "", end="")
                print()
    
    print()


def create_visualizations(df):
    """
    Create visualizations comparing LLM performance across genders.
    
    Args:
        df: DataFrame with evaluation data
    """
    # Create figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Define colors for genders
    gender_colors = {'male': '#3498db', 'female': '#e91e63'}
    shot_colors = {'Few-Shot': '#2ecc71', 'Zero-Shot': '#e74c3c'}
    
    # 1. Agreement scores by gender (overall)
    sns.boxplot(
        data=df, 
        x='gender', 
        y='agreement_score', 
        ax=axes[0, 0],
        hue='gender',
        palette=gender_colors,
        legend=False
    )
    axes[0, 0].set_title('Agreement Scores by Gender (All Generations)', 
                         fontsize=14, fontweight='bold')
    axes[0, 0].set_xlabel('Participant Gender', fontsize=12)
    axes[0, 0].set_ylabel('Agreement Score (1-7)', fontsize=12)
    axes[0, 0].set_ylim(0.5, 7.5)
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Add means
    for i, gender in enumerate(sorted(df['gender'].unique())):
        mean = df[df['gender'] == gender]['agreement_score'].mean()
        n = len(df[df['gender'] == gender])
        axes[0, 0].plot(i, mean, 'D', color='white', markeredgecolor='black', 
                       markersize=8, zorder=3)
        axes[0, 0].text(i, 0.8, f'n={n}', ha='center', va='center',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                       fontsize=9)
    
    # 2. Authenticity scores by gender (overall)
    sns.boxplot(
        data=df, 
        x='gender', 
        y='authenticity_score', 
        ax=axes[0, 1],
        hue='gender',
        palette=gender_colors,
        legend=False
    )
    axes[0, 1].set_title('Authenticity Scores by Gender (All Generations)', 
                         fontsize=14, fontweight='bold')
    axes[0, 1].set_xlabel('Participant Gender', fontsize=12)
    axes[0, 1].set_ylabel('Authenticity Score (1-7)', fontsize=12)
    axes[0, 1].set_ylim(0.5, 7.5)
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Add means
    for i, gender in enumerate(sorted(df['gender'].unique())):
        mean = df[df['gender'] == gender]['authenticity_score'].mean()
        n = len(df[df['gender'] == gender])
        axes[0, 1].plot(i, mean, 'D', color='white', markeredgecolor='black', 
                       markersize=8, zorder=3)
        axes[0, 1].text(i, 0.8, f'n={n}', ha='center', va='center',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                       fontsize=9)
    
    # 3. Agreement scores by gender AND shot type
    df_for_plot = df.copy()
    df_for_plot['gender_shot'] = df_for_plot['gender'] + '\n' + df_for_plot['shot_type']
    
    # Create grouped data
    order = []
    for gender in sorted(df['gender'].unique()):
        order.append(f'{gender}\nFew-Shot')
        order.append(f'{gender}\nZero-Shot')
    
    sns.boxplot(
        data=df_for_plot, 
        x='gender_shot', 
        y='agreement_score', 
        ax=axes[1, 0],
        order=order
    )
    axes[1, 0].set_title('Agreement Scores by Gender and Shot Type', 
                         fontsize=14, fontweight='bold')
    axes[1, 0].set_xlabel('Participant Gender & Generation Type', fontsize=12)
    axes[1, 0].set_ylabel('Agreement Score (1-7)', fontsize=12)
    axes[1, 0].set_ylim(0.5, 7.5)
    axes[1, 0].grid(axis='y', alpha=0.3)
    axes[1, 0].tick_params(axis='x', rotation=0)
    
    # Add means and sample sizes
    for i, combo in enumerate(order):
        gender, shot = combo.split('\n')
        subset = df[(df['gender'] == gender) & (df['shot_type'] == shot)]
        if len(subset) > 0:
            mean = subset['agreement_score'].mean()
            n = len(subset)
            axes[1, 0].plot(i, mean, 'D', color='white', markeredgecolor='black', 
                           markersize=8, zorder=3)
            axes[1, 0].text(i, 0.8, f'n={n}', ha='center', va='center',
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                           fontsize=8)
    
    # 4. Authenticity scores by gender AND shot type
    sns.boxplot(
        data=df_for_plot, 
        x='gender_shot', 
        y='authenticity_score', 
        ax=axes[1, 1],
        order=order
    )
    axes[1, 1].set_title('Authenticity Scores by Gender and Shot Type', 
                         fontsize=14, fontweight='bold')
    axes[1, 1].set_xlabel('Participant Gender & Generation Type', fontsize=12)
    axes[1, 1].set_ylabel('Authenticity Score (1-7)', fontsize=12)
    axes[1, 1].set_ylim(0.5, 7.5)
    axes[1, 1].grid(axis='y', alpha=0.3)
    axes[1, 1].tick_params(axis='x', rotation=0)
    
    # Add means and sample sizes
    for i, combo in enumerate(order):
        gender, shot = combo.split('\n')
        subset = df[(df['gender'] == gender) & (df['shot_type'] == shot)]
        if len(subset) > 0:
            mean = subset['authenticity_score'].mean()
            n = len(subset)
            axes[1, 1].plot(i, mean, 'D', color='white', markeredgecolor='black', 
                           markersize=8, zorder=3)
            axes[1, 1].text(i, 0.8, f'n={n}', ha='center', va='center',
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                           fontsize=8)
    
    plt.tight_layout()
    
    # Save figure
    output_file = 'gender_analysis_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Main visualization saved to: {output_file}")
    
    # Create interaction plot
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))
    
    # Agreement interaction plot
    for gender in sorted(df['gender'].unique()):
        gender_data = df[df['gender'] == gender]
        means = gender_data.groupby('shot_type')['agreement_score'].mean()
        stds = gender_data.groupby('shot_type')['agreement_score'].std()
        
        shot_types = ['Few-Shot', 'Zero-Shot']
        x = [0, 1]
        y = [means['Few-Shot'], means['Zero-Shot']]
        yerr = [stds['Few-Shot'], stds['Zero-Shot']]
        
        axes2[0].errorbar(x, y, yerr=yerr, marker='o', markersize=10, 
                         label=gender, linewidth=2, capsize=5, capthick=2)
    
    axes2[0].set_xticks([0, 1])
    axes2[0].set_xticklabels(['Few-Shot', 'Zero-Shot'])
    axes2[0].set_ylabel('Mean Agreement Score', fontsize=12)
    axes2[0].set_xlabel('Generation Type', fontsize=12)
    axes2[0].set_title('Agreement Scores: Gender × Shot Type Interaction', 
                       fontsize=14, fontweight='bold')
    axes2[0].legend(title='Participant Gender', fontsize=11)
    axes2[0].grid(True, alpha=0.3)
    axes2[0].set_ylim(3, 7)
    
    # Authenticity interaction plot
    for gender in sorted(df['gender'].unique()):
        gender_data = df[df['gender'] == gender]
        means = gender_data.groupby('shot_type')['authenticity_score'].mean()
        stds = gender_data.groupby('shot_type')['authenticity_score'].std()
        
        shot_types = ['Few-Shot', 'Zero-Shot']
        x = [0, 1]
        y = [means['Few-Shot'], means['Zero-Shot']]
        yerr = [stds['Few-Shot'], stds['Zero-Shot']]
        
        axes2[1].errorbar(x, y, yerr=yerr, marker='o', markersize=10, 
                         label=gender, linewidth=2, capsize=5, capthick=2)
    
    axes2[1].set_xticks([0, 1])
    axes2[1].set_xticklabels(['Few-Shot', 'Zero-Shot'])
    axes2[1].set_ylabel('Mean Authenticity Score', fontsize=12)
    axes2[1].set_xlabel('Generation Type', fontsize=12)
    axes2[1].set_title('Authenticity Scores: Gender × Shot Type Interaction', 
                       fontsize=14, fontweight='bold')
    axes2[1].legend(title='Participant Gender', fontsize=11)
    axes2[1].grid(True, alpha=0.3)
    axes2[1].set_ylim(3, 7)
    
    plt.tight_layout()
    
    output_file2 = 'gender_interaction_plot.png'
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"✓ Interaction plot saved to: {output_file2}")
    
    print()


def print_summary(df):
    """
    Print a summary of key findings.
    
    Args:
        df: DataFrame with evaluation data
    """
    print("-"*80)
    print("KEY FINDINGS SUMMARY")
    print("-"*80)
    
    genders = sorted(df['gender'].unique())
    if len(genders) == 2:
        gender1, gender2 = genders
        
        # Overall performance
        g1_agreement = df[df['gender'] == gender1]['agreement_score'].mean()
        g2_agreement = df[df['gender'] == gender2]['agreement_score'].mean()
        
        g1_authenticity = df[df['gender'] == gender1]['authenticity_score'].mean()
        g2_authenticity = df[df['gender'] == gender2]['authenticity_score'].mean()
        
        print(f"\n1. Overall LLM Performance by Gender:")
        print(f"   {gender1.capitalize()}: Agreement={g1_agreement:.2f}, Authenticity={g1_authenticity:.2f}")
        print(f"   {gender2.capitalize()}: Agreement={g2_agreement:.2f}, Authenticity={g2_authenticity:.2f}")
        
        if abs(g1_agreement - g2_agreement) > 0.3:
            better_gender = gender1 if g1_agreement > g2_agreement else gender2
            print(f"   → LLM performs better for {better_gender} participants (Δ={abs(g1_agreement - g2_agreement):.2f})")
        else:
            print(f"   → LLM performance is similar across genders (Δ={abs(g1_agreement - g2_agreement):.2f})")
        
        # By shot type
        print(f"\n2. Performance by Generation Type:")
        for shot_type in ['Few-Shot', 'Zero-Shot']:
            print(f"\n   {shot_type}:")
            for gender in genders:
                subset = df[(df['gender'] == gender) & (df['shot_type'] == shot_type)]
                agr_mean = subset['agreement_score'].mean()
                auth_mean = subset['authenticity_score'].mean()
                print(f"     {gender}: Agreement={agr_mean:.2f}, Authenticity={auth_mean:.2f}")
        
        print(f"\n3. Few-Shot vs Zero-Shot Improvement:")
        for gender in genders:
            few_shot = df[(df['gender'] == gender) & (df['shot_type'] == 'Few-Shot')]['agreement_score'].mean()
            zero_shot = df[(df['gender'] == gender) & (df['shot_type'] == 'Zero-Shot')]['agreement_score'].mean()
            improvement = few_shot - zero_shot
            print(f"   {gender.capitalize()}: +{improvement:.2f} points (Few-Shot advantage)")
    
    print()


def main():
    """Main analysis function."""
    print("\nLoading data for completed participants...")
    df = load_gender_evaluations()
    
    if len(df) == 0:
        print("No data found for completed participants.")
        return
    
    print(f"✓ Loaded {len(df)} evaluations from {df['participant_id'].nunique()} completed participants\n")
    
    # Print statistics
    print_statistics(df)
    
    # Print summary
    print_summary(df)
    
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
