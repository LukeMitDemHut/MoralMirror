"""
Social Proximity Analysis - LLM Performance by Vignette Social Proximity

This script analyzes whether the LLM performs differently when generating
responses for vignettes with socially close vs socially distant protagonists.
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
from models import Participant, Evaluation, LLMGeneration, Vignette

# Configure visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)


def load_proximity_evaluations():
    """
    Load evaluation data with vignette social proximity for completed participants.
    
    Returns:
        DataFrame with columns: participant_id, social_proximity, agreement_score, 
                               authenticity_score, is_zero_shot, shot_type
    """
    db = get_db()
    
    with db as session:
        # Query evaluations with vignette social proximity for completed participants only
        query = session.query(
            Evaluation.participant_id,
            Vignette.social_proximity,
            Vignette.id.label('vignette_id'),
            Evaluation.agreement_score,
            Evaluation.authenticity_score,
            LLMGeneration.is_zero_shot
        ).join(
            LLMGeneration,
            Evaluation.generation_id == LLMGeneration.id
        ).join(
            Vignette,
            LLMGeneration.vignette_id == Vignette.id
        ).join(
            Participant,
            Evaluation.participant_id == Participant.id
        ).filter(
            Participant.current_phase == 'completed'
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(
            query.all(),
            columns=['participant_id', 'social_proximity', 'vignette_id', 
                    'agreement_score', 'authenticity_score', 'is_zero_shot']
        )
        
        # Add readable shot type column
        df['shot_type'] = df['is_zero_shot'].map({
            True: 'Zero-Shot',
            False: 'Few-Shot'
        })
        
        return df


def print_statistics(df):
    """
    Print descriptive statistics by social proximity and shot type.
    
    Args:
        df: DataFrame with evaluation data
    """
    print("="*80)
    print(" SOCIAL PROXIMITY ANALYSIS - LLM PERFORMANCE BY VIGNETTE TYPE")
    print("="*80)
    print()
    
    # Overall counts
    print(f"Total evaluations: {len(df)}")
    print(f"Unique participants: {df['participant_id'].nunique()}")
    print(f"Unique vignettes: {df['vignette_id'].nunique()}")
    print()
    
    # Social proximity distribution
    print("Vignettes by social proximity:")
    proximity_counts = df.groupby('social_proximity')['vignette_id'].nunique()
    for proximity, count in proximity_counts.items():
        print(f"  {proximity}: {count} vignettes")
    print()
    
    # Evaluations by social proximity and shot type
    print("Evaluations by social proximity and shot type:")
    eval_counts = df.groupby(['social_proximity', 'shot_type']).size().unstack(fill_value=0)
    print(eval_counts)
    print()
    
    # Statistics by social proximity
    print("-"*80)
    print("AGREEMENT SCORES BY SOCIAL PROXIMITY")
    print("-"*80)
    agreement_by_proximity = df.groupby('social_proximity')['agreement_score'].describe()
    print(agreement_by_proximity.round(3))
    print()
    
    print("-"*80)
    print("AUTHENTICITY SCORES BY SOCIAL PROXIMITY")
    print("-"*80)
    authenticity_by_proximity = df.groupby('social_proximity')['authenticity_score'].describe()
    print(authenticity_by_proximity.round(3))
    print()
    
    # Statistics by social proximity AND shot type
    print("-"*80)
    print("AGREEMENT SCORES BY SOCIAL PROXIMITY AND SHOT TYPE")
    print("-"*80)
    agreement_detailed = df.groupby(['social_proximity', 'shot_type'])['agreement_score'].agg(['mean', 'std', 'count'])
    print(agreement_detailed.round(3))
    print()
    
    print("-"*80)
    print("AUTHENTICITY SCORES BY SOCIAL PROXIMITY AND SHOT TYPE")
    print("-"*80)
    authenticity_detailed = df.groupby(['social_proximity', 'shot_type'])['authenticity_score'].agg(['mean', 'std', 'count'])
    print(authenticity_detailed.round(3))
    print()
    
    # Statistical tests - comparing social proximity
    print("-"*80)
    print("STATISTICAL TESTS - SOCIAL PROXIMITY COMPARISON (Mann-Whitney U Test)")
    print("-"*80)
    
    proximities = sorted(df['social_proximity'].unique())
    if len(proximities) == 2:
        prox1, prox2 = proximities
        
        # Agreement scores by proximity (overall)
        p1_agreement = df[df['social_proximity'] == prox1]['agreement_score']
        p2_agreement = df[df['social_proximity'] == prox2]['agreement_score']
        
        u_stat_agreement, p_val_agreement = stats.mannwhitneyu(
            p1_agreement, p2_agreement, alternative='two-sided'
        )
        
        print(f"\nAgreement Scores (Overall):")
        print(f"  {prox1}: mean={p1_agreement.mean():.3f}, SD={p1_agreement.std():.3f}, n={len(p1_agreement)}")
        print(f"  {prox2}: mean={p2_agreement.mean():.3f}, SD={p2_agreement.std():.3f}, n={len(p2_agreement)}")
        print(f"  Difference: {p1_agreement.mean() - p2_agreement.mean():.3f}")
        print(f"  U-statistic: {u_stat_agreement:.2f}, p-value: {p_val_agreement:.4f}")
        
        if p_val_agreement < 0.001:
            print(f"  Result: Highly significant difference (p < 0.001) ***")
        elif p_val_agreement < 0.01:
            print(f"  Result: Very significant difference (p < 0.01) **")
        elif p_val_agreement < 0.05:
            print(f"  Result: Significant difference (p < 0.05) *")
        else:
            print(f"  Result: No significant difference (p >= 0.05)")
        
        # Authenticity scores by proximity (overall)
        p1_authenticity = df[df['social_proximity'] == prox1]['authenticity_score']
        p2_authenticity = df[df['social_proximity'] == prox2]['authenticity_score']
        
        u_stat_authenticity, p_val_authenticity = stats.mannwhitneyu(
            p1_authenticity, p2_authenticity, alternative='two-sided'
        )
        
        print(f"\nAuthenticity Scores (Overall):")
        print(f"  {prox1}: mean={p1_authenticity.mean():.3f}, SD={p1_authenticity.std():.3f}, n={len(p1_authenticity)}")
        print(f"  {prox2}: mean={p2_authenticity.mean():.3f}, SD={p2_authenticity.std():.3f}, n={len(p2_authenticity)}")
        print(f"  Difference: {p1_authenticity.mean() - p2_authenticity.mean():.3f}")
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
            
            p1_agreement_shot = df_shot[df_shot['social_proximity'] == prox1]['agreement_score']
            p2_agreement_shot = df_shot[df_shot['social_proximity'] == prox2]['agreement_score']
            
            if len(p1_agreement_shot) > 0 and len(p2_agreement_shot) > 0:
                u_stat, p_val = stats.mannwhitneyu(
                    p1_agreement_shot, p2_agreement_shot, alternative='two-sided'
                )
                
                print(f"\n{shot_type} - Agreement:")
                print(f"  {prox1}: {p1_agreement_shot.mean():.3f} ± {p1_agreement_shot.std():.3f} (n={len(p1_agreement_shot)})")
                print(f"  {prox2}: {p2_agreement_shot.mean():.3f} ± {p2_agreement_shot.std():.3f} (n={len(p2_agreement_shot)})")
                print(f"  p-value: {p_val:.4f}", end="")
                if p_val < 0.05:
                    print(" *" if p_val < 0.05 else "", end="")
                print()
    
    print()


def create_visualizations(df):
    """
    Create visualizations comparing LLM performance across social proximity levels.
    
    Args:
        df: DataFrame with evaluation data
    """
    # Create figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Define colors for social proximity
    proximity_colors = {'close': '#3498db', 'distant': '#e74c3c'}
    
    # 1. Agreement scores by social proximity (overall)
    sns.boxplot(
        data=df, 
        x='social_proximity', 
        y='agreement_score', 
        ax=axes[0, 0],
        hue='social_proximity',
        palette=proximity_colors,
        legend=False
    )
    axes[0, 0].set_title('Agreement Scores by Social Proximity (All Generations)', 
                         fontsize=14, fontweight='bold')
    axes[0, 0].set_xlabel('Vignette Social Proximity', fontsize=12)
    axes[0, 0].set_ylabel('Agreement Score (1-7)', fontsize=12)
    axes[0, 0].set_ylim(0.5, 7.5)
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Add means
    for i, proximity in enumerate(sorted(df['social_proximity'].unique())):
        mean = df[df['social_proximity'] == proximity]['agreement_score'].mean()
        n = len(df[df['social_proximity'] == proximity])
        axes[0, 0].plot(i, mean, 'D', color='white', markeredgecolor='black', 
                       markersize=8, zorder=3)
        axes[0, 0].text(i, 0.8, f'n={n}', ha='center', va='center',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                       fontsize=9)
    
    # 2. Authenticity scores by social proximity (overall)
    sns.boxplot(
        data=df, 
        x='social_proximity', 
        y='authenticity_score', 
        ax=axes[0, 1],
        hue='social_proximity',
        palette=proximity_colors,
        legend=False
    )
    axes[0, 1].set_title('Authenticity Scores by Social Proximity (All Generations)', 
                         fontsize=14, fontweight='bold')
    axes[0, 1].set_xlabel('Vignette Social Proximity', fontsize=12)
    axes[0, 1].set_ylabel('Authenticity Score (1-7)', fontsize=12)
    axes[0, 1].set_ylim(0.5, 7.5)
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Add means
    for i, proximity in enumerate(sorted(df['social_proximity'].unique())):
        mean = df[df['social_proximity'] == proximity]['authenticity_score'].mean()
        n = len(df[df['social_proximity'] == proximity])
        axes[0, 1].plot(i, mean, 'D', color='white', markeredgecolor='black', 
                       markersize=8, zorder=3)
        axes[0, 1].text(i, 0.8, f'n={n}', ha='center', va='center',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                       fontsize=9)
    
    # 3. Agreement scores by social proximity AND shot type
    df_for_plot = df.copy()
    df_for_plot['proximity_shot'] = df_for_plot['social_proximity'] + '\n' + df_for_plot['shot_type']
    
    # Create grouped data
    order = []
    for proximity in sorted(df['social_proximity'].unique()):
        order.append(f'{proximity}\nFew-Shot')
        order.append(f'{proximity}\nZero-Shot')
    
    sns.boxplot(
        data=df_for_plot, 
        x='proximity_shot', 
        y='agreement_score', 
        ax=axes[1, 0],
        order=order
    )
    axes[1, 0].set_title('Agreement Scores by Social Proximity and Shot Type', 
                         fontsize=14, fontweight='bold')
    axes[1, 0].set_xlabel('Vignette Social Proximity & Generation Type', fontsize=12)
    axes[1, 0].set_ylabel('Agreement Score (1-7)', fontsize=12)
    axes[1, 0].set_ylim(0.5, 7.5)
    axes[1, 0].grid(axis='y', alpha=0.3)
    axes[1, 0].tick_params(axis='x', rotation=0)
    
    # Add means and sample sizes
    for i, combo in enumerate(order):
        proximity, shot = combo.split('\n')
        subset = df[(df['social_proximity'] == proximity) & (df['shot_type'] == shot)]
        if len(subset) > 0:
            mean = subset['agreement_score'].mean()
            n = len(subset)
            axes[1, 0].plot(i, mean, 'D', color='white', markeredgecolor='black', 
                           markersize=8, zorder=3)
            axes[1, 0].text(i, 0.8, f'n={n}', ha='center', va='center',
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                           fontsize=8)
    
    # 4. Authenticity scores by social proximity AND shot type
    sns.boxplot(
        data=df_for_plot, 
        x='proximity_shot', 
        y='authenticity_score', 
        ax=axes[1, 1],
        order=order
    )
    axes[1, 1].set_title('Authenticity Scores by Social Proximity and Shot Type', 
                         fontsize=14, fontweight='bold')
    axes[1, 1].set_xlabel('Vignette Social Proximity & Generation Type', fontsize=12)
    axes[1, 1].set_ylabel('Authenticity Score (1-7)', fontsize=12)
    axes[1, 1].set_ylim(0.5, 7.5)
    axes[1, 1].grid(axis='y', alpha=0.3)
    axes[1, 1].tick_params(axis='x', rotation=0)
    
    # Add means and sample sizes
    for i, combo in enumerate(order):
        proximity, shot = combo.split('\n')
        subset = df[(df['social_proximity'] == proximity) & (df['shot_type'] == shot)]
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
    output_file = 'social_proximity_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Main visualization saved to: {output_file}")
    
    # Create interaction plot
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6))
    
    # Agreement interaction plot
    for proximity in sorted(df['social_proximity'].unique()):
        proximity_data = df[df['social_proximity'] == proximity]
        means = proximity_data.groupby('shot_type')['agreement_score'].mean()
        stds = proximity_data.groupby('shot_type')['agreement_score'].std()
        
        shot_types = ['Few-Shot', 'Zero-Shot']
        x = [0, 1]
        y = [means['Few-Shot'], means['Zero-Shot']]
        yerr = [stds['Few-Shot'], stds['Zero-Shot']]
        
        axes2[0].errorbar(x, y, yerr=yerr, marker='o', markersize=10, 
                         label=proximity.capitalize(), linewidth=2, capsize=5, capthick=2)
    
    axes2[0].set_xticks([0, 1])
    axes2[0].set_xticklabels(['Few-Shot', 'Zero-Shot'])
    axes2[0].set_ylabel('Mean Agreement Score', fontsize=12)
    axes2[0].set_xlabel('Generation Type', fontsize=12)
    axes2[0].set_title('Agreement: Social Proximity × Shot Type Interaction', 
                       fontsize=14, fontweight='bold')
    axes2[0].legend(title='Social Proximity', fontsize=11)
    axes2[0].grid(True, alpha=0.3)
    axes2[0].set_ylim(3, 7)
    
    # Authenticity interaction plot
    for proximity in sorted(df['social_proximity'].unique()):
        proximity_data = df[df['social_proximity'] == proximity]
        means = proximity_data.groupby('shot_type')['authenticity_score'].mean()
        stds = proximity_data.groupby('shot_type')['authenticity_score'].std()
        
        shot_types = ['Few-Shot', 'Zero-Shot']
        x = [0, 1]
        y = [means['Few-Shot'], means['Zero-Shot']]
        yerr = [stds['Few-Shot'], stds['Zero-Shot']]
        
        axes2[1].errorbar(x, y, yerr=yerr, marker='o', markersize=10, 
                         label=proximity.capitalize(), linewidth=2, capsize=5, capthick=2)
    
    axes2[1].set_xticks([0, 1])
    axes2[1].set_xticklabels(['Few-Shot', 'Zero-Shot'])
    axes2[1].set_ylabel('Mean Authenticity Score', fontsize=12)
    axes2[1].set_xlabel('Generation Type', fontsize=12)
    axes2[1].set_title('Authenticity: Social Proximity × Shot Type Interaction', 
                       fontsize=14, fontweight='bold')
    axes2[1].legend(title='Social Proximity', fontsize=11)
    axes2[1].grid(True, alpha=0.3)
    axes2[1].set_ylim(3, 7)
    
    plt.tight_layout()
    
    output_file2 = 'social_proximity_interaction_plot.png'
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
    
    proximities = sorted(df['social_proximity'].unique())
    if len(proximities) == 2:
        prox1, prox2 = proximities
        
        # Overall performance
        p1_agreement = df[df['social_proximity'] == prox1]['agreement_score'].mean()
        p2_agreement = df[df['social_proximity'] == prox2]['agreement_score'].mean()
        
        p1_authenticity = df[df['social_proximity'] == prox1]['authenticity_score'].mean()
        p2_authenticity = df[df['social_proximity'] == prox2]['authenticity_score'].mean()
        
        print(f"\n1. Overall LLM Performance by Social Proximity:")
        print(f"   {prox1.capitalize()}: Agreement={p1_agreement:.2f}, Authenticity={p1_authenticity:.2f}")
        print(f"   {prox2.capitalize()}: Agreement={p2_agreement:.2f}, Authenticity={p2_authenticity:.2f}")
        
        if abs(p1_agreement - p2_agreement) > 0.3:
            better_prox = prox1 if p1_agreement > p2_agreement else prox2
            print(f"   → LLM performs better for {better_prox} vignettes (Δ={abs(p1_agreement - p2_agreement):.2f})")
        else:
            print(f"   → LLM performance is similar across proximity types (Δ={abs(p1_agreement - p2_agreement):.2f})")
        
        # By shot type
        print(f"\n2. Performance by Generation Type:")
        for shot_type in ['Few-Shot', 'Zero-Shot']:
            print(f"\n   {shot_type}:")
            for proximity in proximities:
                subset = df[(df['social_proximity'] == proximity) & (df['shot_type'] == shot_type)]
                agr_mean = subset['agreement_score'].mean()
                auth_mean = subset['authenticity_score'].mean()
                print(f"     {proximity}: Agreement={agr_mean:.2f}, Authenticity={auth_mean:.2f}")
        
        print(f"\n3. Few-Shot Improvement by Social Proximity:")
        for proximity in proximities:
            few_shot = df[(df['social_proximity'] == proximity) & (df['shot_type'] == 'Few-Shot')]['agreement_score'].mean()
            zero_shot = df[(df['social_proximity'] == proximity) & (df['shot_type'] == 'Zero-Shot')]['agreement_score'].mean()
            improvement = few_shot - zero_shot
            print(f"   {proximity.capitalize()}: +{improvement:.2f} points (Few-Shot advantage)")
    
    print()


def main():
    """Main analysis function."""
    print("\nLoading data for completed participants...")
    df = load_proximity_evaluations()
    
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
