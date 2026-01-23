"""
Age Analysis

This script analyzes participant data by age, examining age distribution,
LLM performance across age groups, and completion times by age.
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
plt.rcParams['figure.figsize'] = (16, 12)


def categorize_age(age):
    """
    Categorize age into groups.
    
    Args:
        age: Age in years
    
    Returns:
        Age category string
    """
    if age < 25:
        return "18-24"
    elif age < 35:
        return "25-34"
    elif age < 45:
        return "35-44"
    elif age < 55:
        return "45-54"
    elif age < 65:
        return "55-64"
    else:
        return "65+"


def load_age_data():
    """
    Load participant data with age information.
    
    Returns:
        DataFrame with participant demographics
    """
    db = get_db()
    
    with db as session:
        # Query completed participants
        query = session.query(
            Participant.id,
            Participant.anonymous_id,
            Participant.age,
            Participant.gender,
            Participant.nationality,
            Participant.consent_date,
            Participant.completed_at
        ).filter(
            Participant.current_phase == 'completed'
        )
        
        df = pd.DataFrame(
            query.all(),
            columns=['participant_id', 'anonymous_id', 'age', 'gender', 
                    'nationality', 'consent_date', 'completed_at']
        )
        
        # Add age categories
        df['age_category'] = df['age'].apply(categorize_age)
        
        # Calculate completion time
        df['completion_hours'] = (df['completed_at'] - df['consent_date']).dt.total_seconds() / 3600
        
        return df


def load_evaluation_data_with_age():
    """
    Load evaluation data with participant age information.
    
    Returns:
        DataFrame with evaluations and age
    """
    db = get_db()
    
    with db as session:
        query = session.query(
            Evaluation.participant_id,
            Participant.age,
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
        
        df = pd.DataFrame(
            query.all(),
            columns=['participant_id', 'age', 'anonymous_id', 'agreement_score', 
                    'authenticity_score', 'is_zero_shot']
        )
        
        df['age_category'] = df['age'].apply(categorize_age)
        df['shot_type'] = df['is_zero_shot'].map({
            True: 'Zero-Shot',
            False: 'Few-Shot'
        })
        
        return df


def print_statistics(participant_df, evaluation_df):
    """
    Print descriptive statistics for age analysis.
    
    Args:
        participant_df: DataFrame with participant data
        evaluation_df: DataFrame with evaluation data
    """
    print("="*80)
    print(" AGE ANALYSIS")
    print("="*80)
    print()
    
    # Overall statistics
    print(f"Total completed participants: {len(participant_df)}")
    print(f"Total evaluations: {len(evaluation_df)}")
    print()
    
    # Age statistics
    print("-"*80)
    print("AGE DISTRIBUTION")
    print("-"*80)
    print()
    
    print("Age statistics:")
    print(f"  Mean:   {participant_df['age'].mean():.2f} years")
    print(f"  Median: {participant_df['age'].median():.1f} years")
    print(f"  Std:    {participant_df['age'].std():.2f} years")
    print(f"  Min:    {participant_df['age'].min()} years")
    print(f"  Max:    {participant_df['age'].max()} years")
    print()
    
    print("Detailed statistics:")
    print(participant_df['age'].describe().to_string())
    print()
    
    # Age categories
    print("-"*80)
    print("PARTICIPANTS BY AGE CATEGORY")
    print("-"*80)
    print()
    
    age_counts = participant_df['age_category'].value_counts().sort_index()
    for category, count in age_counts.items():
        pct = count / len(participant_df) * 100
        print(f"  {category}: {count:2d} ({pct:5.1f}%)")
    print()
    
    # Completion time by age
    print("-"*80)
    print("COMPLETION TIME BY AGE")
    print("-"*80)
    print()
    
    # Correlation between age and completion time
    age_completion_corr = stats.pearsonr(participant_df['age'], participant_df['completion_hours'])
    print(f"Correlation (age vs completion time):")
    print(f"  Pearson r = {age_completion_corr[0]:.4f}, p = {age_completion_corr[1]:.6f}")
    if age_completion_corr[1] < 0.05:
        direction = "positively" if age_completion_corr[0] > 0 else "negatively"
        print(f"  Result: Age is {direction} correlated with completion time (p < 0.05) *")
    else:
        print(f"  Result: No significant correlation (p >= 0.05)")
    print()
    
    print("By age category:")
    completion_by_age = participant_df.groupby('age_category')['completion_hours'].agg(['count', 'mean', 'median', 'std'])
    for category, row in completion_by_age.iterrows():
        print(f"  {category}: n={int(row['count'])}, mean={row['mean']:.2f}h, "
              f"median={row['median']:.2f}h, std={row['std']:.2f}h")
    print()
    
    # Agreement scores by age
    print("-"*80)
    print("AGREEMENT SCORES BY AGE")
    print("-"*80)
    print()
    
    # Correlation
    age_agreement_corr = stats.pearsonr(evaluation_df['age'], evaluation_df['agreement_score'])
    print(f"Correlation (age vs agreement score):")
    print(f"  Pearson r = {age_agreement_corr[0]:.4f}, p = {age_agreement_corr[1]:.6f}")
    if age_agreement_corr[1] < 0.05:
        direction = "positively" if age_agreement_corr[0] > 0 else "negatively"
        print(f"  Result: Age is {direction} correlated with agreement (p < 0.05) *")
    else:
        print(f"  Result: No significant correlation (p >= 0.05)")
    print()
    
    print("By age category (overall):")
    agreement_by_age = evaluation_df.groupby('age_category')['agreement_score'].agg(['count', 'mean', 'median', 'std'])
    for category, row in agreement_by_age.iterrows():
        print(f"  {category}: n={int(row['count'])}, mean={row['mean']:.2f}, "
              f"median={row['median']:.2f}, std={row['std']:.2f}")
    print()
    
    # By shot type
    print("By age category and generation type:")
    for shot_type in ['Few-Shot', 'Zero-Shot']:
        print(f"\n  {shot_type}:")
        subset = evaluation_df[evaluation_df['shot_type'] == shot_type]
        agreement_by_age_shot = subset.groupby('age_category')['agreement_score'].agg(['count', 'mean'])
        for category, row in agreement_by_age_shot.iterrows():
            print(f"    {category}: n={int(row['count'])}, mean={row['mean']:.2f}")
    print()
    
    # Authenticity scores by age
    print("-"*80)
    print("AUTHENTICITY SCORES BY AGE")
    print("-"*80)
    print()
    
    # Correlation
    age_authenticity_corr = stats.pearsonr(evaluation_df['age'], evaluation_df['authenticity_score'])
    print(f"Correlation (age vs authenticity score):")
    print(f"  Pearson r = {age_authenticity_corr[0]:.4f}, p = {age_authenticity_corr[1]:.6f}")
    if age_authenticity_corr[1] < 0.05:
        direction = "positively" if age_authenticity_corr[0] > 0 else "negatively"
        print(f"  Result: Age is {direction} correlated with authenticity (p < 0.05) *")
    else:
        print(f"  Result: No significant correlation (p >= 0.05)")
    print()
    
    print("By age category (overall):")
    authenticity_by_age = evaluation_df.groupby('age_category')['authenticity_score'].agg(['count', 'mean', 'median', 'std'])
    for category, row in authenticity_by_age.iterrows():
        print(f"  {category}: n={int(row['count'])}, mean={row['mean']:.2f}, "
              f"median={row['median']:.2f}, std={row['std']:.2f}")
    print()
    
    # Few-shot improvement by age
    print("-"*80)
    print("FEW-SHOT IMPROVEMENT BY AGE")
    print("-"*80)
    print()
    
    improvement_data = []
    for age_cat in evaluation_df['age_category'].unique():
        subset = evaluation_df[evaluation_df['age_category'] == age_cat]
        
        few_shot = subset[subset['shot_type'] == 'Few-Shot']
        zero_shot = subset[subset['shot_type'] == 'Zero-Shot']
        
        if len(few_shot) > 0 and len(zero_shot) > 0:
            agreement_improvement = few_shot['agreement_score'].mean() - zero_shot['agreement_score'].mean()
            authenticity_improvement = few_shot['authenticity_score'].mean() - zero_shot['authenticity_score'].mean()
            
            improvement_data.append({
                'age_category': age_cat,
                'agreement_improvement': agreement_improvement,
                'authenticity_improvement': authenticity_improvement,
                'n_few_shot': len(few_shot),
                'n_zero_shot': len(zero_shot)
            })
    
    if improvement_data:
        improvement_df = pd.DataFrame(improvement_data).sort_values('age_category')
        
        print("Agreement improvement (Few-Shot - Zero-Shot):")
        for _, row in improvement_df.iterrows():
            sign = "+" if row['agreement_improvement'] > 0 else ""
            print(f"  {row['age_category']}: {sign}{row['agreement_improvement']:.3f} "
                  f"(n_few={int(row['n_few_shot'])}, n_zero={int(row['n_zero_shot'])})")
        print()
        
        print("Authenticity improvement (Few-Shot - Zero-Shot):")
        for _, row in improvement_df.iterrows():
            sign = "+" if row['authenticity_improvement'] > 0 else ""
            print(f"  {row['age_category']}: {sign}{row['authenticity_improvement']:.3f} "
                  f"(n_few={int(row['n_few_shot'])}, n_zero={int(row['n_zero_shot'])})")
        print()


def create_visualizations(participant_df, evaluation_df):
    """
    Create visualizations for age analysis.
    
    Args:
        participant_df: DataFrame with participant data
        evaluation_df: DataFrame with evaluation data
    """
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(4, 3, hspace=0.35, wspace=0.3)
    
    # 1. Age distribution histogram
    ax1 = fig.add_subplot(gs[0, :])
    ax1.hist(participant_df['age'], bins=20, alpha=0.7, color='#3498db', edgecolor='black')
    ax1.axvline(participant_df['age'].mean(), color='red', linestyle='--', 
               linewidth=2, label=f"Mean: {participant_df['age'].mean():.1f}")
    ax1.axvline(participant_df['age'].median(), color='green', linestyle='--', 
               linewidth=2, label=f"Median: {participant_df['age'].median():.1f}")
    ax1.set_xlabel('Age (years)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Participants', fontsize=12, fontweight='bold')
    ax1.set_title('Age Distribution of Participants', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Age categories bar chart
    ax2 = fig.add_subplot(gs[1, 0])
    age_counts = participant_df['age_category'].value_counts().sort_index()
    colors_bar = plt.cm.viridis(np.linspace(0.2, 0.8, len(age_counts)))
    age_counts.plot(kind='bar', ax=ax2, color=colors_bar, edgecolor='black')
    ax2.set_xlabel('Age Category', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Number of Participants', fontsize=11, fontweight='bold')
    ax2.set_title('Participants by Age Category', fontsize=12, fontweight='bold')
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add count labels on bars
    for i, (category, count) in enumerate(age_counts.items()):
        ax2.text(i, count + 0.3, str(count), ha='center', va='bottom', fontweight='bold')
    
    # 3. Age vs Completion Time scatter
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.scatter(participant_df['age'], participant_df['completion_hours'], 
               alpha=0.6, s=80, c='#e74c3c', edgecolors='black', linewidth=0.5)
    
    # Add regression line
    z = np.polyfit(participant_df['age'], participant_df['completion_hours'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(participant_df['age'].min(), participant_df['age'].max(), 100)
    
    corr, p_val = stats.pearsonr(participant_df['age'], participant_df['completion_hours'])
    ax3.plot(x_line, p(x_line), 'b--', linewidth=2, alpha=0.8, 
            label=f'r={corr:.3f}, p={p_val:.3f}')
    
    ax3.set_xlabel('Age (years)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Completion Time (hours)', fontsize=11, fontweight='bold')
    ax3.set_title('Age vs Completion Time', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 4. Completion time by age category
    ax4 = fig.add_subplot(gs[1, 2])
    age_categories_sorted = sorted(participant_df['age_category'].unique())
    completion_data = [participant_df[participant_df['age_category'] == cat]['completion_hours'].values 
                      for cat in age_categories_sorted]
    bp = ax4.boxplot(completion_data, tick_labels=age_categories_sorted, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('#2ecc71')
        patch.set_alpha(0.7)
    ax4.set_xlabel('Age Category', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Completion Time (hours)', fontsize=11, fontweight='bold')
    ax4.set_title('Completion Time by Age', fontsize=12, fontweight='bold')
    ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45)
    ax4.grid(axis='y', alpha=0.3)
    
    # 5. Age vs Agreement Score scatter
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.scatter(evaluation_df['age'], evaluation_df['agreement_score'], 
               alpha=0.3, s=40, c='#3498db', edgecolors='white', linewidth=0.3)
    
    z = np.polyfit(evaluation_df['age'], evaluation_df['agreement_score'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(evaluation_df['age'].min(), evaluation_df['age'].max(), 100)
    
    corr, p_val = stats.pearsonr(evaluation_df['age'], evaluation_df['agreement_score'])
    ax5.plot(x_line, p(x_line), 'r--', linewidth=2, alpha=0.8, 
            label=f'r={corr:.3f}, p={p_val:.3f}')
    
    ax5.set_xlabel('Age (years)', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Agreement Score (1-7)', fontsize=11, fontweight='bold')
    ax5.set_title('Age vs Agreement Score', fontsize=12, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3)
    ax5.set_ylim(0.5, 7.5)
    
    # 6. Age vs Authenticity Score scatter
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.scatter(evaluation_df['age'], evaluation_df['authenticity_score'], 
               alpha=0.3, s=40, c='#e74c3c', edgecolors='white', linewidth=0.3)
    
    z = np.polyfit(evaluation_df['age'], evaluation_df['authenticity_score'], 1)
    p = np.poly1d(z)
    
    corr, p_val = stats.pearsonr(evaluation_df['age'], evaluation_df['authenticity_score'])
    ax6.plot(x_line, p(x_line), 'b--', linewidth=2, alpha=0.8, 
            label=f'r={corr:.3f}, p={p_val:.3f}')
    
    ax6.set_xlabel('Age (years)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('Authenticity Score (1-7)', fontsize=11, fontweight='bold')
    ax6.set_title('Age vs Authenticity Score', fontsize=12, fontweight='bold')
    ax6.legend(fontsize=9)
    ax6.grid(True, alpha=0.3)
    ax6.set_ylim(0.5, 7.5)
    
    # 7. Agreement scores by age category
    ax7 = fig.add_subplot(gs[2, 2])
    age_categories_sorted = sorted(evaluation_df['age_category'].unique())
    agreement_data = [evaluation_df[evaluation_df['age_category'] == cat]['agreement_score'].values 
                     for cat in age_categories_sorted]
    bp = ax7.boxplot(agreement_data, tick_labels=age_categories_sorted, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('#3498db')
        patch.set_alpha(0.7)
    ax7.set_xlabel('Age Category', fontsize=11, fontweight='bold')
    ax7.set_ylabel('Agreement Score (1-7)', fontsize=11, fontweight='bold')
    ax7.set_title('Agreement by Age Category', fontsize=12, fontweight='bold')
    ax7.set_xticklabels(ax7.get_xticklabels(), rotation=45)
    ax7.grid(axis='y', alpha=0.3)
    ax7.set_ylim(0.5, 7.5)
    
    # 8. Authenticity scores by age category
    ax8 = fig.add_subplot(gs[3, 0])
    authenticity_data = [evaluation_df[evaluation_df['age_category'] == cat]['authenticity_score'].values 
                        for cat in age_categories_sorted]
    bp = ax8.boxplot(authenticity_data, tick_labels=age_categories_sorted, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('#e74c3c')
        patch.set_alpha(0.7)
    ax8.set_xlabel('Age Category', fontsize=11, fontweight='bold')
    ax8.set_ylabel('Authenticity Score (1-7)', fontsize=11, fontweight='bold')
    ax8.set_title('Authenticity by Age Category', fontsize=12, fontweight='bold')
    ax8.set_xticklabels(ax8.get_xticklabels(), rotation=45)
    ax8.grid(axis='y', alpha=0.3)
    ax8.set_ylim(0.5, 7.5)
    
    # 9. Few-shot improvement by age category
    ax9 = fig.add_subplot(gs[3, 1:])
    
    improvement_data = []
    for age_cat in age_categories_sorted:
        subset = evaluation_df[evaluation_df['age_category'] == age_cat]
        
        few_shot = subset[subset['shot_type'] == 'Few-Shot']
        zero_shot = subset[subset['shot_type'] == 'Zero-Shot']
        
        if len(few_shot) > 0 and len(zero_shot) > 0:
            agreement_improvement = few_shot['agreement_score'].mean() - zero_shot['agreement_score'].mean()
            authenticity_improvement = few_shot['authenticity_score'].mean() - zero_shot['authenticity_score'].mean()
            
            improvement_data.append({
                'age_category': age_cat,
                'agreement': agreement_improvement,
                'authenticity': authenticity_improvement
            })
    
    if improvement_data:
        improvement_df = pd.DataFrame(improvement_data)
        
        x = np.arange(len(improvement_df))
        width = 0.35
        
        bars1 = ax9.bar(x - width/2, improvement_df['agreement'], width, 
                       label='Agreement', color='#3498db', alpha=0.8, edgecolor='black')
        bars2 = ax9.bar(x + width/2, improvement_df['authenticity'], width, 
                       label='Authenticity', color='#e74c3c', alpha=0.8, edgecolor='black')
        
        ax9.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.3)
        ax9.set_xlabel('Age Category', fontsize=11, fontweight='bold')
        ax9.set_ylabel('Score Improvement (Few-Shot - Zero-Shot)', fontsize=11, fontweight='bold')
        ax9.set_title('Few-Shot Improvement by Age Category', fontsize=12, fontweight='bold')
        ax9.set_xticks(x)
        ax9.set_xticklabels(improvement_df['age_category'])
        ax9.legend(fontsize=10)
        ax9.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax9.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}',
                        ha='center', va='bottom' if height > 0 else 'top',
                        fontsize=8)
    
    plt.tight_layout()
    
    # Save figure
    output_file = 'age_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_file}")
    plt.close()


def export_data(participant_df, evaluation_df):
    """
    Export age analysis data to CSV.
    
    Args:
        participant_df: DataFrame with participant data
        evaluation_df: DataFrame with evaluation data
    """
    # Export participant summary by age
    age_summary = participant_df.groupby('age_category').agg({
        'participant_id': 'count',
        'age': ['mean', 'min', 'max'],
        'completion_hours': ['mean', 'median', 'std']
    }).round(2)
    age_summary.columns = ['_'.join(col).strip() for col in age_summary.columns.values]
    
    output_file1 = 'age_summary.csv'
    age_summary.to_csv(output_file1)
    print(f"✓ Age summary exported to: {output_file1}")
    
    # Export evaluation summary by age
    eval_summary = evaluation_df.groupby('age_category').agg({
        'agreement_score': ['count', 'mean', 'median', 'std'],
        'authenticity_score': ['mean', 'median', 'std']
    }).round(2)
    eval_summary.columns = ['_'.join(col).strip() for col in eval_summary.columns.values]
    
    output_file2 = 'age_evaluation_summary.csv'
    eval_summary.to_csv(output_file2)
    print(f"✓ Age evaluation summary exported to: {output_file2}")


def main():
    """
    Main execution function.
    """
    print("\n")
    print("="*80)
    print(" Loading data...")
    print("="*80)
    
    # Load data
    participant_df = load_age_data()
    evaluation_df = load_evaluation_data_with_age()
    
    if len(participant_df) == 0:
        print("✗ No completed participants found.")
        return
    
    print(f"✓ Loaded {len(participant_df)} participants")
    print(f"✓ Loaded {len(evaluation_df)} evaluations")
    print()
    
    # Print statistics
    print_statistics(participant_df, evaluation_df)
    
    # Create visualizations
    print("="*80)
    print(" Creating visualizations...")
    print("="*80)
    create_visualizations(participant_df, evaluation_df)
    print()
    
    # Export data
    print("="*80)
    print(" Exporting data...")
    print("="*80)
    export_data(participant_df, evaluation_df)
    print()
    
    print("="*80)
    print(" Analysis complete!")
    print("="*80)
    print()


if __name__ == "__main__":
    main()
