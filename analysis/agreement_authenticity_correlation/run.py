"""
Agreement-Authenticity Correlation Analysis

This script analyzes the correlation between agreement scores and authenticity scores
for individual participants' evaluations. It examines whether participants who agree more
with LLM responses also rate them as more authentic.
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from database import get_db
from models import Participant, Evaluation, LLMGeneration

# Configure visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)


def load_evaluation_data():
    """
    Load evaluation data for completed participants.
    
    Returns:
        DataFrame with columns: participant_id, anonymous_id, evaluation_id,
                               agreement_score, authenticity_score, is_zero_shot, shot_type
    """
    db = get_db()
    
    with db as session:
        # Query evaluations for completed participants only
        query = session.query(
            Evaluation.id.label('evaluation_id'),
            Evaluation.participant_id,
            Participant.anonymous_id,
            Evaluation.agreement_score,
            Evaluation.authenticity_score,
            LLMGeneration.is_zero_shot,
            LLMGeneration.vignette_id
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
            columns=['evaluation_id', 'participant_id', 'anonymous_id', 'agreement_score', 
                    'authenticity_score', 'is_zero_shot', 'vignette_id']
        )
        
        # Add readable shot type column
        df['shot_type'] = df['is_zero_shot'].map({
            True: 'Zero-Shot',
            False: 'Few-Shot'
        })
        
        return df


def compute_overall_correlation(df):
    """
    Compute overall correlation between agreement and authenticity scores.
    
    Args:
        df: DataFrame with evaluation data
    
    Returns:
        Tuple of (pearson_r, pearson_p, spearman_r, spearman_p)
    """
    # Pearson correlation (linear relationship)
    pearson_r, pearson_p = stats.pearsonr(df['agreement_score'], df['authenticity_score'])
    
    # Spearman correlation (monotonic relationship, more robust to outliers)
    spearman_r, spearman_p = stats.spearmanr(df['agreement_score'], df['authenticity_score'])
    
    return pearson_r, pearson_p, spearman_r, spearman_p


def compute_per_participant_correlations(df):
    """
    Compute correlation for each participant individually.
    
    Args:
        df: DataFrame with evaluation data
    
    Returns:
        DataFrame with per-participant correlation coefficients
    """
    correlations = []
    
    for participant_id in df['participant_id'].unique():
        participant_data = df[df['participant_id'] == participant_id]
        
        # Need at least 3 data points for meaningful correlation
        if len(participant_data) < 3:
            continue
        
        # Compute correlations
        try:
            pearson_r, pearson_p = stats.pearsonr(
                participant_data['agreement_score'], 
                participant_data['authenticity_score']
            )
            spearman_r, spearman_p = stats.spearmanr(
                participant_data['agreement_score'], 
                participant_data['authenticity_score']
            )
        except:
            # Handle cases where variance is zero (all same values)
            pearson_r, pearson_p = np.nan, np.nan
            spearman_r, spearman_p = np.nan, np.nan
        
        correlations.append({
            'participant_id': participant_id,
            'anonymous_id': participant_data['anonymous_id'].iloc[0],
            'n_evaluations': len(participant_data),
            'pearson_r': pearson_r,
            'pearson_p': pearson_p,
            'spearman_r': spearman_r,
            'spearman_p': spearman_p,
            'mean_agreement': participant_data['agreement_score'].mean(),
            'mean_authenticity': participant_data['authenticity_score'].mean()
        })
    
    return pd.DataFrame(correlations)


def print_statistics(df, per_participant_df):
    """
    Print descriptive statistics for correlations.
    
    Args:
        df: DataFrame with all evaluation data
        per_participant_df: DataFrame with per-participant correlations
    """
    print("="*80)
    print(" AGREEMENT-AUTHENTICITY CORRELATION ANALYSIS")
    print("="*80)
    print()
    
    # Overall counts
    print(f"Total evaluations: {len(df)}")
    print(f"Unique participants: {df['participant_id'].nunique()}")
    print(f"Participants with ≥3 evaluations: {len(per_participant_df)}")
    print()
    
    # Overall correlation
    print("-"*80)
    print("OVERALL CORRELATION (All Evaluations)")
    print("-"*80)
    pearson_r, pearson_p, spearman_r, spearman_p = compute_overall_correlation(df)
    
    print(f"Pearson correlation:  r = {pearson_r:.4f}, p = {pearson_p:.6f}")
    if pearson_p < 0.001:
        print(f"  Result: Highly significant (p < 0.001) ***")
    elif pearson_p < 0.01:
        print(f"  Result: Very significant (p < 0.01) **")
    elif pearson_p < 0.05:
        print(f"  Result: Significant (p < 0.05) *")
    else:
        print(f"  Result: Not significant (p >= 0.05)")
    
    print(f"\nSpearman correlation: ρ = {spearman_r:.4f}, p = {spearman_p:.6f}")
    if spearman_p < 0.001:
        print(f"  Result: Highly significant (p < 0.001) ***")
    elif spearman_p < 0.01:
        print(f"  Result: Very significant (p < 0.01) **")
    elif spearman_p < 0.05:
        print(f"  Result: Significant (p < 0.05) *")
    else:
        print(f"  Result: Not significant (p >= 0.05)")
    print()
    
    # Interpretation
    print("Interpretation:")
    if abs(pearson_r) > 0.7:
        print("  Strong correlation - Agreement and authenticity are highly related")
    elif abs(pearson_r) > 0.4:
        print("  Moderate correlation - Agreement and authenticity are moderately related")
    elif abs(pearson_r) > 0.2:
        print("  Weak correlation - Agreement and authenticity are weakly related")
    else:
        print("  Very weak/negligible correlation")
    print()
    
    # Per-participant statistics
    print("-"*80)
    print("PER-PARTICIPANT CORRELATIONS")
    print("-"*80)
    
    # Filter out NaN correlations
    valid_correlations = per_participant_df.dropna(subset=['pearson_r'])
    
    print(f"Participants with valid correlations: {len(valid_correlations)}")
    print(f"\nPearson correlation distribution:")
    print(f"  Mean:   {valid_correlations['pearson_r'].mean():.4f}")
    print(f"  Median: {valid_correlations['pearson_r'].median():.4f}")
    print(f"  SD:     {valid_correlations['pearson_r'].std():.4f}")
    print(f"  Min:    {valid_correlations['pearson_r'].min():.4f}")
    print(f"  Max:    {valid_correlations['pearson_r'].max():.4f}")
    print()
    
    # Count significant correlations
    significant_positive = len(valid_correlations[
        (valid_correlations['pearson_p'] < 0.05) & 
        (valid_correlations['pearson_r'] > 0)
    ])
    significant_negative = len(valid_correlations[
        (valid_correlations['pearson_p'] < 0.05) & 
        (valid_correlations['pearson_r'] < 0)
    ])
    not_significant = len(valid_correlations[valid_correlations['pearson_p'] >= 0.05])
    
    print(f"Significant positive correlations (p < 0.05): {significant_positive} ({significant_positive/len(valid_correlations)*100:.1f}%)")
    print(f"Significant negative correlations (p < 0.05): {significant_negative} ({significant_negative/len(valid_correlations)*100:.1f}%)")
    print(f"Not significant (p ≥ 0.05):                   {not_significant} ({not_significant/len(valid_correlations)*100:.1f}%)")
    print()
    
    # By shot type
    print("-"*80)
    print("CORRELATION BY GENERATION TYPE")
    print("-"*80)
    
    for shot_type in ['Few-Shot', 'Zero-Shot']:
        subset = df[df['shot_type'] == shot_type]
        if len(subset) > 0:
            pearson_r, pearson_p, spearman_r, spearman_p = compute_overall_correlation(subset)
            print(f"\n{shot_type}:")
            print(f"  N = {len(subset)} evaluations")
            print(f"  Pearson:  r = {pearson_r:.4f}, p = {pearson_p:.6f}")
            print(f"  Spearman: ρ = {spearman_r:.4f}, p = {spearman_p:.6f}")


def create_visualizations(df, per_participant_df):
    """
    Create visualizations for correlation analysis.
    
    Args:
        df: DataFrame with all evaluation data
        per_participant_df: DataFrame with per-participant correlations
    """
    # Create main figure with 4 subplots
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # 1. Overall scatter plot with regression line
    ax1 = fig.add_subplot(gs[0, :])
    
    # Calculate regression line
    pearson_r, pearson_p, _, _ = compute_overall_correlation(df)
    z = np.polyfit(df['agreement_score'], df['authenticity_score'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['agreement_score'].min(), df['agreement_score'].max(), 100)
    
    # Scatter plot with alpha for overlapping points
    ax1.scatter(df['agreement_score'], df['authenticity_score'], 
               alpha=0.3, s=50, c='#3498db', edgecolors='white', linewidth=0.5)
    ax1.plot(x_line, p(x_line), 'r-', linewidth=2, label=f'Linear fit (r={pearson_r:.3f})')
    
    ax1.set_xlabel('Agreement Score (1-7)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Authenticity Score (1-7)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Overall Correlation: Agreement vs Authenticity\n(n={len(df)} evaluations, Pearson r={pearson_r:.4f}, p={pearson_p:.6f})', 
                 fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0.5, 7.5)
    ax1.set_ylim(0.5, 7.5)
    
    # Add diagonal reference line (perfect correlation)
    ax1.plot([1, 7], [1, 7], 'k--', alpha=0.3, linewidth=1, label='Perfect correlation')
    
    # 2. Hexbin density plot (better for many overlapping points)
    ax2 = fig.add_subplot(gs[1, 0])
    hexbin = ax2.hexbin(df['agreement_score'], df['authenticity_score'], 
                        gridsize=20, cmap='YlOrRd', mincnt=1)
    ax2.set_xlabel('Agreement Score (1-7)', fontsize=11)
    ax2.set_ylabel('Authenticity Score (1-7)', fontsize=11)
    ax2.set_title('Density Heatmap', fontsize=12, fontweight='bold')
    plt.colorbar(hexbin, ax=ax2, label='Count')
    ax2.set_xlim(0.5, 7.5)
    ax2.set_ylim(0.5, 7.5)
    
    # 3. Distribution of per-participant correlations
    ax3 = fig.add_subplot(gs[1, 1])
    valid_correlations = per_participant_df.dropna(subset=['pearson_r'])
    
    ax3.hist(valid_correlations['pearson_r'], bins=20, color='#2ecc71', 
            alpha=0.7, edgecolor='black')
    ax3.axvline(valid_correlations['pearson_r'].mean(), color='red', 
               linestyle='--', linewidth=2, label=f"Mean: {valid_correlations['pearson_r'].mean():.3f}")
    ax3.axvline(valid_correlations['pearson_r'].median(), color='blue', 
               linestyle='--', linewidth=2, label=f"Median: {valid_correlations['pearson_r'].median():.3f}")
    ax3.set_xlabel('Pearson Correlation Coefficient', fontsize=11)
    ax3.set_ylabel('Number of Participants', fontsize=11)
    ax3.set_title('Distribution of Per-Participant Correlations', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Scatter by shot type
    ax4 = fig.add_subplot(gs[2, 0])
    
    colors_shot = {'Few-Shot': '#2ecc71', 'Zero-Shot': '#e74c3c'}
    for shot_type in ['Few-Shot', 'Zero-Shot']:
        subset = df[df['shot_type'] == shot_type]
        ax4.scatter(subset['agreement_score'], subset['authenticity_score'],
                   alpha=0.4, s=40, c=colors_shot[shot_type], label=shot_type,
                   edgecolors='white', linewidth=0.5)
        
        # Add regression line
        if len(subset) > 1:
            z = np.polyfit(subset['agreement_score'], subset['authenticity_score'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(1, 7, 100)
            ax4.plot(x_line, p(x_line), '--', linewidth=2, color=colors_shot[shot_type], alpha=0.8)
    
    ax4.set_xlabel('Agreement Score (1-7)', fontsize=11)
    ax4.set_ylabel('Authenticity Score (1-7)', fontsize=11)
    ax4.set_title('Correlation by Generation Type', fontsize=12, fontweight='bold')
    ax4.legend(loc='lower right', fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0.5, 7.5)
    ax4.set_ylim(0.5, 7.5)
    
    # 5. Correlation strength vs number of evaluations
    ax5 = fig.add_subplot(gs[2, 1])
    valid_correlations = per_participant_df.dropna(subset=['pearson_r'])
    
    # Color by correlation strength
    scatter = ax5.scatter(valid_correlations['n_evaluations'], 
                         valid_correlations['pearson_r'],
                         c=np.abs(valid_correlations['pearson_r']),
                         cmap='RdYlGn', s=60, alpha=0.6, edgecolors='black', linewidth=0.5)
    ax5.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax5.set_xlabel('Number of Evaluations per Participant', fontsize=11)
    ax5.set_ylabel('Pearson Correlation Coefficient', fontsize=11)
    ax5.set_title('Correlation Strength vs Sample Size', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax5, label='|Correlation|')
    
    # Save figure
    output_file = 'agreement_authenticity_correlation.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Main visualization saved to: {output_file}")
    plt.close()
    
    # Create additional plot: per-participant correlation sorted
    fig2, ax = plt.subplots(1, 1, figsize=(14, 8))
    
    valid_correlations_sorted = valid_correlations.sort_values('pearson_r')
    colors = ['red' if r < 0 else 'green' for r in valid_correlations_sorted['pearson_r']]
    
    y_pos = np.arange(len(valid_correlations_sorted))
    bars = ax.barh(y_pos, valid_correlations_sorted['pearson_r'], color=colors, alpha=0.6)
    
    # Add significance markers
    for i, (idx, row) in enumerate(valid_correlations_sorted.iterrows()):
        if row['pearson_p'] < 0.05:
            ax.text(row['pearson_r'] + 0.02 if row['pearson_r'] > 0 else row['pearson_r'] - 0.02, 
                   i, '*', fontsize=12, fontweight='bold', 
                   ha='left' if row['pearson_r'] > 0 else 'right')
    
    ax.axvline(0, color='black', linewidth=1)
    ax.set_xlabel('Pearson Correlation Coefficient', fontsize=12, fontweight='bold')
    ax.set_ylabel('Participants (sorted)', fontsize=12, fontweight='bold')
    ax.set_title('Per-Participant Correlations (Sorted)\n* indicates p < 0.05', 
                fontsize=14, fontweight='bold')
    ax.set_yticks([])  # Hide y-axis labels (too many participants)
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim(-1, 1)
    
    # Add vertical lines for correlation strength categories
    ax.axvline(0.7, color='green', linestyle='--', alpha=0.3, linewidth=1)
    ax.axvline(-0.7, color='red', linestyle='--', alpha=0.3, linewidth=1)
    ax.axvline(0.4, color='orange', linestyle='--', alpha=0.3, linewidth=1)
    ax.axvline(-0.4, color='orange', linestyle='--', alpha=0.3, linewidth=1)
    
    # Add legend
    ax.text(0.75, 0.95, 'Strong', transform=ax.transAxes, fontsize=10, 
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    ax.text(0.45, 0.95, 'Moderate', transform=ax.transAxes, fontsize=10,
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    plt.tight_layout()
    output_file2 = 'per_participant_correlations.png'
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"✓ Per-participant visualization saved to: {output_file2}")
    plt.close()


def export_data(df, per_participant_df):
    """
    Export correlation data to CSV files.
    
    Args:
        df: DataFrame with all evaluation data
        per_participant_df: DataFrame with per-participant correlations
    """
    # Export per-participant correlations
    output_file1 = 'per_participant_correlations.csv'
    per_participant_df.to_csv(output_file1, index=False)
    print(f"✓ Per-participant correlations exported to: {output_file1}")
    
    # Export raw evaluation data
    output_file2 = 'evaluation_data.csv'
    df.to_csv(output_file2, index=False)
    print(f"✓ Raw evaluation data exported to: {output_file2}")


def main():
    """
    Main execution function.
    """
    print("\n")
    print("="*80)
    print(" Loading data...")
    print("="*80)
    
    # Load data
    df = load_evaluation_data()
    
    if len(df) == 0:
        print("✗ No evaluation data found. Make sure participants have completed the study.")
        return
    
    print(f"✓ Loaded {len(df)} evaluations from {df['participant_id'].nunique()} participants")
    print()
    
    # Compute per-participant correlations
    print("Computing per-participant correlations...")
    per_participant_df = compute_per_participant_correlations(df)
    print(f"✓ Computed correlations for {len(per_participant_df)} participants")
    print()
    
    # Print statistics
    print_statistics(df, per_participant_df)
    print()
    
    # Create visualizations
    print("="*80)
    print(" Creating visualizations...")
    print("="*80)
    create_visualizations(df, per_participant_df)
    print()
    
    # Export data
    print("="*80)
    print(" Exporting data...")
    print("="*80)
    export_data(df, per_participant_df)
    print()
    
    print("="*80)
    print(" Analysis complete!")
    print("="*80)
    print()


if __name__ == "__main__":
    main()
