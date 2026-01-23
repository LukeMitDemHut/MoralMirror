"""
Completion Time Analysis

This script analyzes the time participants took to complete the study,
measured from consent given to study completion.
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
from database import get_db
from models import Participant

# Configure visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)


def load_completion_data():
    """
    Load completion time data for participants who completed the study.
    
    Returns:
        DataFrame with columns: participant_id, anonymous_id, consent_date,
                               completed_at, duration_seconds, duration_minutes,
                               duration_hours, duration_days
    """
    db = get_db()
    
    with db as session:
        # Query participants who completed the study
        query = session.query(
            Participant.id,
            Participant.anonymous_id,
            Participant.consent_date,
            Participant.completed_at,
            Participant.age,
            Participant.gender,
            Participant.nationality
        ).filter(
            Participant.current_phase == 'completed',
            Participant.completed_at.isnot(None)
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(
            query.all(),
            columns=['participant_id', 'anonymous_id', 'consent_date', 
                    'completed_at', 'age', 'gender', 'nationality']
        )
        
        # Calculate time differences
        df['duration'] = df['completed_at'] - df['consent_date']
        df['duration_seconds'] = df['duration'].dt.total_seconds()
        df['duration_minutes'] = df['duration_seconds'] / 60
        df['duration_hours'] = df['duration_minutes'] / 60
        df['duration_days'] = df['duration_hours'] / 24
        
        return df


def format_duration(seconds):
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "2d 5h 30m")
    """
    td = timedelta(seconds=seconds)
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 and days == 0 and hours == 0:
        parts.append(f"{seconds}s")
    
    return " ".join(parts) if parts else "0s"


def print_statistics(df):
    """
    Print descriptive statistics for completion times.
    
    Args:
        df: DataFrame with completion time data
    """
    print("="*80)
    print(" COMPLETION TIME ANALYSIS")
    print("="*80)
    print()
    
    # Overall counts
    print(f"Total completed participants: {len(df)}")
    print()
    
    # Time statistics
    print("-"*80)
    print("COMPLETION TIME STATISTICS")
    print("-"*80)
    print()
    
    print("In different units:")
    print(f"  Minutes: mean={df['duration_minutes'].mean():.2f}, "
          f"median={df['duration_minutes'].median():.2f}, "
          f"std={df['duration_minutes'].std():.2f}")
    print(f"  Hours:   mean={df['duration_hours'].mean():.2f}, "
          f"median={df['duration_hours'].median():.2f}, "
          f"std={df['duration_hours'].std():.2f}")
    print(f"  Days:    mean={df['duration_days'].mean():.2f}, "
          f"median={df['duration_days'].median():.2f}, "
          f"std={df['duration_days'].std():.2f}")
    print()
    
    print("Detailed statistics (in hours):")
    print(df['duration_hours'].describe().to_string())
    print()
    
    # Human readable
    print("-"*80)
    print("HUMAN-READABLE SUMMARY")
    print("-"*80)
    print()
    
    mean_seconds = df['duration_seconds'].mean()
    median_seconds = df['duration_seconds'].median()
    min_seconds = df['duration_seconds'].min()
    max_seconds = df['duration_seconds'].max()
    
    print(f"Mean completion time:   {format_duration(mean_seconds)}")
    print(f"Median completion time: {format_duration(median_seconds)}")
    print(f"Fastest completion:     {format_duration(min_seconds)}")
    print(f"Slowest completion:     {format_duration(max_seconds)}")
    print()
    
    # Distribution categories
    print("-"*80)
    print("COMPLETION TIME DISTRIBUTION")
    print("-"*80)
    print()
    
    # Categorize by time
    under_1h = len(df[df['duration_hours'] < 1])
    between_1_6h = len(df[(df['duration_hours'] >= 1) & (df['duration_hours'] < 6)])
    between_6_24h = len(df[(df['duration_hours'] >= 6) & (df['duration_hours'] < 24)])
    between_1_7d = len(df[(df['duration_days'] >= 1) & (df['duration_days'] < 7)])
    over_7d = len(df[df['duration_days'] >= 7])
    
    total = len(df)
    
    print(f"Under 1 hour:        {under_1h:3d} ({under_1h/total*100:5.1f}%)")
    print(f"1-6 hours:           {between_1_6h:3d} ({between_1_6h/total*100:5.1f}%)")
    print(f"6-24 hours:          {between_6_24h:3d} ({between_6_24h/total*100:5.1f}%)")
    print(f"1-7 days:            {between_1_7d:3d} ({between_1_7d/total*100:5.1f}%)")
    print(f"Over 7 days:         {over_7d:3d} ({over_7d/total*100:5.1f}%)")
    print()
    
    # By demographics
    print("-"*80)
    print("COMPLETION TIME BY DEMOGRAPHICS")
    print("-"*80)
    print()
    
    # By gender
    if df['gender'].nunique() > 1:
        print("By Gender:")
        gender_stats = df.groupby('gender')['duration_hours'].agg(['count', 'mean', 'median', 'std'])
        for gender, row in gender_stats.iterrows():
            print(f"  {gender}: n={int(row['count'])}, "
                  f"mean={row['mean']:.2f}h, median={row['median']:.2f}h, std={row['std']:.2f}h")
        print()
    
    # By nationality (top 5)
    nationality_counts = df['nationality'].value_counts()
    if len(nationality_counts) > 1:
        print("By Nationality (top 5):")
        top_nationalities = nationality_counts.head(5).index
        nat_stats = df[df['nationality'].isin(top_nationalities)].groupby('nationality')['duration_hours'].agg(['count', 'mean', 'median'])
        for nat, row in nat_stats.iterrows():
            print(f"  {nat}: n={int(row['count'])}, "
                  f"mean={row['mean']:.2f}h, median={row['median']:.2f}h")
        print()
    
    # Outliers
    print("-"*80)
    print("OUTLIER DETECTION")
    print("-"*80)
    print()
    
    q1 = df['duration_hours'].quantile(0.25)
    q3 = df['duration_hours'].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = df[(df['duration_hours'] < lower_bound) | (df['duration_hours'] > upper_bound)]
    
    print(f"IQR method (1.5 × IQR):")
    print(f"  Lower bound: {lower_bound:.2f}h")
    print(f"  Upper bound: {upper_bound:.2f}h")
    print(f"  Number of outliers: {len(outliers)} ({len(outliers)/len(df)*100:.1f}%)")
    
    if len(outliers) > 0:
        print(f"\nOutlier participants:")
        for _, row in outliers.iterrows():
            print(f"  {row['anonymous_id']}: {format_duration(row['duration_seconds'])} "
                  f"({row['duration_hours']:.2f}h)")
    print()


def create_visualizations(df):
    """
    Create visualizations for completion time analysis.
    
    Args:
        df: DataFrame with completion time data
    """
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # 1. Histogram with KDE
    ax1 = fig.add_subplot(gs[0, :])
    ax1.hist(df['duration_hours'], bins=30, alpha=0.7, color='#3498db', edgecolor='black')
    ax1.axvline(df['duration_hours'].mean(), color='red', linestyle='--', 
               linewidth=2, label=f"Mean: {df['duration_hours'].mean():.2f}h")
    ax1.axvline(df['duration_hours'].median(), color='green', linestyle='--', 
               linewidth=2, label=f"Median: {df['duration_hours'].median():.2f}h")
    ax1.set_xlabel('Completion Time (hours)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Participants', fontsize=12, fontweight='bold')
    ax1.set_title('Distribution of Study Completion Times', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Box plot
    ax2 = fig.add_subplot(gs[1, 0])
    bp = ax2.boxplot([df['duration_hours']], widths=0.6, patch_artist=True,
                     boxprops=dict(facecolor='#2ecc71', alpha=0.7),
                     medianprops=dict(color='red', linewidth=2),
                     whiskerprops=dict(linewidth=1.5),
                     capprops=dict(linewidth=1.5))
    ax2.set_ylabel('Completion Time (hours)', fontsize=12, fontweight='bold')
    ax2.set_title('Completion Time Box Plot', fontsize=12, fontweight='bold')
    ax2.set_xticklabels(['All Participants'])
    ax2.grid(axis='y', alpha=0.3)
    
    # Add statistics annotations
    stats_text = f"Mean: {df['duration_hours'].mean():.2f}h\n"
    stats_text += f"Median: {df['duration_hours'].median():.2f}h\n"
    stats_text += f"Std: {df['duration_hours'].std():.2f}h\n"
    stats_text += f"Min: {df['duration_hours'].min():.2f}h\n"
    stats_text += f"Max: {df['duration_hours'].max():.2f}h"
    ax2.text(1.3, ax2.get_ylim()[1] * 0.7, stats_text, fontsize=10,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 3. Cumulative distribution
    ax3 = fig.add_subplot(gs[1, 1])
    sorted_hours = sorted(df['duration_hours'])
    cumulative = [i / len(sorted_hours) * 100 for i in range(1, len(sorted_hours) + 1)]
    ax3.plot(sorted_hours, cumulative, linewidth=2, color='#e74c3c')
    ax3.axhline(50, color='green', linestyle='--', alpha=0.5, label='50th percentile')
    ax3.axhline(95, color='orange', linestyle='--', alpha=0.5, label='95th percentile')
    ax3.set_xlabel('Completion Time (hours)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Cumulative Percentage (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Cumulative Distribution of Completion Times', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=10)
    
    # Add percentile markers
    p50 = df['duration_hours'].quantile(0.50)
    p95 = df['duration_hours'].quantile(0.95)
    ax3.axvline(p50, color='green', linestyle='--', alpha=0.5)
    ax3.axvline(p95, color='orange', linestyle='--', alpha=0.5)
    ax3.text(p50, 5, f'{p50:.1f}h', fontsize=9, rotation=90)
    ax3.text(p95, 5, f'{p95:.1f}h', fontsize=9, rotation=90)
    
    # 4. Completion time by gender (if multiple genders)
    ax4 = fig.add_subplot(gs[2, 0])
    if df['gender'].nunique() > 1:
        gender_data = [df[df['gender'] == g]['duration_hours'].values 
                      for g in df['gender'].unique()]
        bp = ax4.boxplot(gender_data, labels=df['gender'].unique(), patch_artist=True)
        for patch, color in zip(bp['boxes'], ['#3498db', '#e74c3c', '#2ecc71']):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax4.set_xlabel('Gender', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Completion Time (hours)', fontsize=12, fontweight='bold')
        ax4.set_title('Completion Time by Gender', fontsize=12, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)
    else:
        ax4.text(0.5, 0.5, 'Insufficient gender diversity\nfor comparison', 
                ha='center', va='center', fontsize=12, transform=ax4.transAxes)
        ax4.set_title('Completion Time by Gender', fontsize=12, fontweight='bold')
    
    # 5. Time categories pie chart
    ax5 = fig.add_subplot(gs[2, 1])
    
    categories = []
    counts = []
    colors_pie = []
    
    under_1h = len(df[df['duration_hours'] < 1])
    if under_1h > 0:
        categories.append('< 1h')
        counts.append(under_1h)
        colors_pie.append('#2ecc71')
    
    between_1_6h = len(df[(df['duration_hours'] >= 1) & (df['duration_hours'] < 6)])
    if between_1_6h > 0:
        categories.append('1-6h')
        counts.append(between_1_6h)
        colors_pie.append('#3498db')
    
    between_6_24h = len(df[(df['duration_hours'] >= 6) & (df['duration_hours'] < 24)])
    if between_6_24h > 0:
        categories.append('6-24h')
        counts.append(between_6_24h)
        colors_pie.append('#f39c12')
    
    between_1_7d = len(df[(df['duration_days'] >= 1) & (df['duration_days'] < 7)])
    if between_1_7d > 0:
        categories.append('1-7d')
        counts.append(between_1_7d)
        colors_pie.append('#e74c3c')
    
    over_7d = len(df[df['duration_days'] >= 7])
    if over_7d > 0:
        categories.append('> 7d')
        counts.append(over_7d)
        colors_pie.append('#9b59b6')
    
    wedges, texts, autotexts = ax5.pie(counts, labels=categories, autopct='%1.1f%%',
                                        colors=colors_pie, startangle=90)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    ax5.set_title('Completion Time Categories', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    # Save figure
    output_file = 'completion_time_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_file}")
    plt.close()


def export_data(df):
    """
    Export completion time data to CSV.
    
    Args:
        df: DataFrame with completion time data
    """
    # Select relevant columns
    export_df = df[[
        'participant_id', 'anonymous_id', 'consent_date', 'completed_at',
        'duration_seconds', 'duration_minutes', 'duration_hours', 'duration_days',
        'age', 'gender', 'nationality'
    ]].copy()
    
    # Add human-readable duration
    export_df['duration_formatted'] = df['duration_seconds'].apply(format_duration)
    
    output_file = 'completion_times.csv'
    export_df.to_csv(output_file, index=False)
    print(f"✓ Completion time data exported to: {output_file}")


def main():
    """
    Main execution function.
    """
    print("\n")
    print("="*80)
    print(" Loading data...")
    print("="*80)
    
    # Load data
    df = load_completion_data()
    
    if len(df) == 0:
        print("✗ No completed participants found.")
        return
    
    print(f"✓ Loaded data for {len(df)} completed participants")
    print()
    
    # Print statistics
    print_statistics(df)
    
    # Create visualizations
    print("="*80)
    print(" Creating visualizations...")
    print("="*80)
    create_visualizations(df)
    print()
    
    # Export data
    print("="*80)
    print(" Exporting data...")
    print("="*80)
    export_data(df)
    print()
    
    print("="*80)
    print(" Analysis complete!")
    print("="*80)
    print()


if __name__ == "__main__":
    main()
