"""
Semantic Word Field Analysis of LLM Reasoning Texts

This analysis investigates which semantic word fields are activated by different
system prompts (Few-Shot vs Zero-Shot).

Methodology:
1. Text preprocessing (Lemmatization, Stopword removal, POS filtering)
2. Embeddings with Sentence-Transformers
3. HDBSCAN Clustering for word field identification
4. UMAP Visualization
5. Quantitative comparisons between prompts
"""

import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from typing import List, Dict, Tuple

# NLP Libraries
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import umap

# Database
from database import get_db
from models import LLMGeneration, Participant

# Configure visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)


def load_reasoning_data():
    """
    Load LLM reasoning texts for completed participants.
    
    Returns:
        DataFrame with columns: generation_id, reasoning, is_zero_shot, shot_type
    """
    print("\n" + "="*80)
    print(" LOADING REASONING DATA")
    print("="*80)
    
    db = get_db()
    
    with db as session:
        query = session.query(
            LLMGeneration.id,
            LLMGeneration.reasoning,
            LLMGeneration.is_zero_shot,
            LLMGeneration.participant_id
        ).join(
            Participant,
            LLMGeneration.participant_id == Participant.id
        ).filter(
            Participant.current_phase == 'completed'
        )
        
        df = pd.DataFrame(
            query.all(),
            columns=['generation_id', 'reasoning', 'is_zero_shot', 'participant_id']
        )
        
        df['shot_type'] = df['is_zero_shot'].map({
            True: 'Zero-Shot',
            False: 'Few-Shot'
        })
        
    print(f"✓ Loaded {len(df)} reasoning texts")
    print(f"  - Few-Shot: {len(df[df['shot_type'] == 'Few-Shot'])}")
    print(f"  - Zero-Shot: {len(df[df['shot_type'] == 'Zero-Shot'])}")
    print()
    
    return df


def preprocess_texts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Linguistic normalization of texts.
    
    Steps:
    1. Tokenization
    2. Lemmatization
    3. Stopword removal
    4. POS filtering (only nouns and verbs)
    
    Args:
        df: DataFrame with reasoning column
        
    Returns:
        DataFrame with additional columns: tokens, lemmas, filtered_lemmas
    """
    print("="*80)
    print(" TEXT PREPROCESSING")
    print("="*80)
    print("\nLoading English language model...")
    
    try:
        nlp = spacy.load("en_core_web_sm")
        print("✓ Language model 'en_core_web_sm' loaded")
    except OSError:
        print("❌ Language model not found.")
        print("   Install with: python -m spacy download en_core_web_sm")
        raise
    
    print("\nProcessing texts...")
    
    all_tokens = []
    all_lemmas = []
    all_filtered = []
    
    for idx, text in enumerate(df['reasoning']):
        if idx % 50 == 0:
            print(f"  Processed: {idx}/{len(df)}", end='\r')
        
        doc = nlp(text)
        
        # 1. Tokenization
        tokens = [token.text for token in doc]
        
        # 2. Lemmatization
        lemmas = [token.lemma_.lower() for token in doc]
        
        # 3. Stopword removal + 4. POS filtering
        # Keep only nouns (NOUN) and verbs (VERB)
        # Remove stopwords and punctuation
        filtered = [
            token.lemma_.lower() 
            for token in doc 
            if token.pos_ in ['NOUN', 'VERB']  # POS filter
            and not token.is_stop                # Stopword filter
            and not token.is_punct               # Punctuation filter
            and not token.is_space               # Whitespace filter
            and len(token.text) > 2              # Minimum length
        ]
        
        all_tokens.append(tokens)
        all_lemmas.append(lemmas)
        all_filtered.append(filtered)
    
    print(f"  Processed: {len(df)}/{len(df)}")
    
    df['tokens'] = all_tokens
    df['lemmas'] = all_lemmas
    df['filtered_lemmas'] = all_filtered
    
    # Statistics
    total_tokens = sum(len(t) for t in all_tokens)
    total_filtered = sum(len(f) for f in all_filtered)
    reduction = (1 - total_filtered / total_tokens) * 100
    
    print(f"\n✓ Preprocessing complete")
    print(f"  - Original tokens: {total_tokens:,}")
    print(f"  - After filtering: {total_filtered:,}")
    print(f"  - Reduction: {reduction:.1f}%")
    print()
    
    return df


def create_word_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a DataFrame with one word per row.
    
    Args:
        df: DataFrame with filtered_lemmas
        
    Returns:
        DataFrame with columns: word, generation_id, shot_type
    """
    rows = []
    
    for idx, row in df.iterrows():
        for word in row['filtered_lemmas']:
            rows.append({
                'word': word,
                'generation_id': row['generation_id'],
                'shot_type': row['shot_type']
            })
    
    word_df = pd.DataFrame(rows)
    
    print(f"✓ Word DataFrame created: {len(word_df):,} words")
    print()
    
    return word_df


def compute_embeddings(word_df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Computes embeddings for all unique words.
    
    Args:
        word_df: DataFrame with words
        
    Returns:
        Tuple: (embeddings array, word_df with embeddings)
    """
    print("="*80)
    print(" COMPUTING EMBEDDINGS")
    print("="*80)
    print("\nLoading Sentence-Transformer model...")
    
    # Multilingual model for English texts
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("✓ Model 'paraphrase-multilingual-MiniLM-L12-v2' loaded")
    
    # Unique words
    unique_words = word_df['word'].unique()
    print(f"\nComputing embeddings for {len(unique_words):,} unique words...")
    
    # Compute embeddings
    embeddings = model.encode(
        unique_words,
        show_progress_bar=True,
        batch_size=64
    )
    
    # Create mapping word -> embedding
    word_to_embedding = dict(zip(unique_words, embeddings))
    
    # Add embeddings to DataFrame
    word_df['embedding'] = word_df['word'].map(word_to_embedding)
    
    print(f"\n✓ Embeddings computed: {embeddings.shape}")
    print(f"  - Dimensions: {embeddings.shape[1]}")
    print()
    
    return embeddings, word_df


def cluster_words(embeddings: np.ndarray, word_df: pd.DataFrame, 
                  n_clusters: int = 8) -> pd.DataFrame:
    """
    Performs K-Means clustering to identify word fields.
    
    Args:
        embeddings: Array with embeddings
        word_df: DataFrame with words
        n_clusters: Number of clusters to create
        
    Returns:
        word_df with cluster_label column
    """
    print("="*80)
    print(" CLUSTERING: IDENTIFYING WORD FIELDS")
    print("="*80)
    print(f"\nParameters: n_clusters={n_clusters}")
    
    # Unique words for clustering
    unique_words = word_df['word'].unique()
    unique_embeddings = np.array([
        word_df[word_df['word'] == word]['embedding'].iloc[0]
        for word in unique_words
    ])
    
    print(f"Clustering {len(unique_words):,} unique words...")
    
    # K-Means Clustering
    clusterer = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
        max_iter=300
    )
    
    cluster_labels = clusterer.fit_predict(unique_embeddings)
    
    # Create mapping word -> cluster_label
    word_to_cluster = dict(zip(unique_words, cluster_labels))
    
    # Add cluster labels to DataFrame
    word_df['cluster_label'] = word_df['word'].map(word_to_cluster)
    
    print(f"\n✓ Clustering complete")
    print(f"  - Word fields found: {n_clusters}")
    print()
    
    # Cluster sizes
    print("Cluster sizes:")
    cluster_sizes = Counter(cluster_labels)
    for cluster_id in sorted(cluster_sizes.keys()):
        print(f"  Cluster {cluster_id}: {cluster_sizes[cluster_id]} unique words")
    
    print()
    
    return word_df


def interpret_clusters(word_df: pd.DataFrame, top_n: int = 20) -> Dict[int, List[str]]:
    """
    Shows the most representative words per cluster for interpretation.
    
    Args:
        word_df: DataFrame with cluster labels
        top_n: Number of top words per cluster
        
    Returns:
        Dictionary: cluster_id -> [top_words]
    """
    print("="*80)
    print(" CLUSTER INTERPRETATION: WORD FIELDS")
    print("="*80)
    print()
    
    cluster_word_dict = {}
    
    # For each cluster
    clusters = sorted(word_df['cluster_label'].unique())
    
    for cluster_id in clusters:
        # Most frequent words in cluster
        cluster_data = word_df[word_df['cluster_label'] == cluster_id]
        word_counts = cluster_data['word'].value_counts().head(top_n)
        
        cluster_word_dict[cluster_id] = word_counts.index.tolist()
        
        print(f"📂 CLUSTER {cluster_id} ({len(cluster_data)} tokens)")
        print("   Top words:")
        for i, (word, count) in enumerate(word_counts.items(), 1):
            print(f"   {i:2d}. {word:20s} ({count:3d}x)")
        print()
    
    return cluster_word_dict


def create_umap_visualization(word_df: pd.DataFrame):
    """
    Creates UMAP visualization of word fields.
    
    Args:
        word_df: DataFrame with embeddings and cluster labels
    """
    print("="*80)
    print(" UMAP VISUALIZATION")
    print("="*80)
    print("\nComputing UMAP projection...")
    
    # Unique words for UMAP
    unique_words = word_df['word'].unique()
    unique_data = []
    
    for word in unique_words:
        word_data = word_df[word_df['word'] == word].iloc[0]
        unique_data.append({
            'word': word,
            'embedding': word_data['embedding'],
            'cluster_label': word_data['cluster_label']
        })
    
    unique_df = pd.DataFrame(unique_data)
    embeddings_array = np.vstack(unique_df['embedding'].values)
    
    # UMAP
    reducer = umap.UMAP(
        n_neighbors=15,
        min_dist=0.1,
        n_components=2,
        metric='cosine',
        random_state=42
    )
    
    embedding_2d = reducer.fit_transform(embeddings_array)
    
    unique_df['umap_x'] = embedding_2d[:, 0]
    unique_df['umap_y'] = embedding_2d[:, 1]
    
    print("✓ UMAP projection computed")
    
    # Visualization
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Colors for clusters
    clusters = unique_df['cluster_label'].unique()
    n_clusters = len(clusters)
    colors = plt.cm.tab20(np.linspace(0, 1, n_clusters))
    
    # Plot each cluster
    for i, cluster_id in enumerate(sorted(clusters)):
        cluster_data = unique_df[unique_df['cluster_label'] == cluster_id]
        ax.scatter(
            cluster_data['umap_x'],
            cluster_data['umap_y'],
            c=[colors[i]],
            s=80,
            alpha=0.7,
            label=f'Cluster {cluster_id}',
            edgecolors='black',
            linewidth=0.5
        )
    
    ax.set_xlabel('UMAP Dimension 1', fontsize=14)
    ax.set_ylabel('UMAP Dimension 2', fontsize=14)
    ax.set_title('Semantic Word Fields in Embedding Space (UMAP Projection)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_file = 'umap_word_fields.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved: {output_file}")
    print()
    
    return unique_df


def quantify_prompt_differences(word_df: pd.DataFrame):
    """
    Quantifies differences between Few-Shot and Zero-Shot prompts.
    
    Args:
        word_df: DataFrame with cluster labels and shot_type
    """
    print("="*80)
    print(" QUANTIFICATION: PROMPT DIFFERENCES")
    print("="*80)
    print()
    
    # All clusters (K-Means assigns all points)
    clustered_df = word_df.copy()
    
    # Cluster proportions per prompt
    print("📊 CLUSTER PROPORTIONS BY PROMPT TYPE")
    print("-" * 80)
    
    # Total words per prompt type
    few_shot_total = len(clustered_df[clustered_df['shot_type'] == 'Few-Shot'])
    zero_shot_total = len(clustered_df[clustered_df['shot_type'] == 'Zero-Shot'])
    
    print(f"\nTotal clustered words:")
    print(f"  Few-Shot:  {few_shot_total:,} words")
    print(f"  Zero-Shot: {zero_shot_total:,} words")
    print()
    
    # Anteile pro Cluster
    clusters = sorted(clustered_df['cluster_label'].unique())
    
    results = []
    
    for cluster_id in clusters:
        cluster_data = clustered_df[clustered_df['cluster_label'] == cluster_id]
        
        few_shot_count = len(cluster_data[cluster_data['shot_type'] == 'Few-Shot'])
        zero_shot_count = len(cluster_data[cluster_data['shot_type'] == 'Zero-Shot'])
        
        few_shot_pct = (few_shot_count / few_shot_total * 100) if few_shot_total > 0 else 0
        zero_shot_pct = (zero_shot_count / zero_shot_total * 100) if zero_shot_total > 0 else 0
        
        diff = few_shot_pct - zero_shot_pct
        
        results.append({
            'cluster': cluster_id,
            'few_shot_pct': few_shot_pct,
            'zero_shot_pct': zero_shot_pct,
            'difference': diff
        })
    
    results_df = pd.DataFrame(results)
    
    print("Cluster proportions (% of clustered words):")
    print()
    print(f"{'Cluster':<10} {'Few-Shot':<12} {'Zero-Shot':<12} {'Difference':<12}")
    print("-" * 50)
    
    for _, row in results_df.iterrows():
        print(f"{row['cluster']:<10} {row['few_shot_pct']:>10.1f}% "
              f"{row['zero_shot_pct']:>10.1f}% {row['difference']:>+10.1f}%")
    
    print()
    
    # Visualization
    create_prompt_comparison_plot(results_df, clustered_df)
    
    return results_df


def create_prompt_comparison_plot(results_df: pd.DataFrame, word_df: pd.DataFrame):
    """
    Creates comparison visualization between prompt types.
    
    Args:
        results_df: DataFrame with cluster proportions
        word_df: Original word DataFrame
    """
    if len(results_df) == 0:
        print("⚠ No clusters available for visualization")
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # 1. Stacked bar chart
    x = results_df['cluster'].astype(str)
    width = 0.35
    x_pos = np.arange(len(x))
    
    axes[0].bar(x_pos - width/2, results_df['few_shot_pct'], width, 
                label='Few-Shot', color='#2ecc71', alpha=0.8)
    axes[0].bar(x_pos + width/2, results_df['zero_shot_pct'], width, 
                label='Zero-Shot', color='#e74c3c', alpha=0.8)
    
    axes[0].set_xlabel('Cluster (Word Field)', fontsize=12)
    axes[0].set_ylabel('Proportion (%)', fontsize=12)
    axes[0].set_title('Cluster Proportions by Prompt Type', fontsize=14, fontweight='bold')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(x)
    axes[0].legend(fontsize=11)
    axes[0].grid(axis='y', alpha=0.3)
    
    # 2. Difference plot
    colors = ['#2ecc71' if d > 0 else '#e74c3c' for d in results_df['difference']]
    
    axes[1].barh(x, results_df['difference'], color=colors, alpha=0.7)
    axes[1].axvline(x=0, color='black', linestyle='--', linewidth=1)
    axes[1].set_xlabel('Difference: Few-Shot - Zero-Shot (%)', fontsize=12)
    axes[1].set_ylabel('Cluster', fontsize=12)
    axes[1].set_title('Cluster Preference by Prompt Type', fontsize=14, fontweight='bold')
    axes[1].grid(axis='x', alpha=0.3)
    
    # Annotations
    for i, (cluster, diff) in enumerate(zip(x, results_df['difference'])):
        axes[1].text(diff + (0.5 if diff > 0 else -0.5), i, f'{diff:+.1f}%',
                     ha='left' if diff > 0 else 'right', va='center', fontsize=9)
    
    plt.tight_layout()
    
    output_file = 'prompt_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Comparison visualization saved: {output_file}")
    print()


def print_summary(word_df: pd.DataFrame, cluster_words: Dict[int, List[str]]):
    """
    Prints summary of main results.
    
    Args:
        word_df: DataFrame with all data
        cluster_words: Dictionary with cluster words
    """
    print("="*80)
    print(" SUMMARY: MAIN RESULTS")
    print("="*80)
    print()
    
    n_clusters = len([c for c in word_df['cluster_label'].unique()])
    
    print(f"📌 Identified word fields: {n_clusters}")
    print()
    
    print("🔍 Semantic domains (examples):")
    print()
    
    for cluster_id, words in cluster_words.items():
        print(f"   Cluster {cluster_id}: {', '.join(words[:5])}...")
    
    print()
    print("💡 Interpretation:")
    print("   - Each cluster represents a coherent semantic field")
    print("   - Different proportions show prompt-specific emphases")
    print("   - Few-Shot vs Zero-Shot activate different semantic spaces")
    print()


def main():
    """Main function for semantic word field analysis."""
    
    print("\n" + "="*80)
    print(" SEMANTIC WORD FIELD ANALYSIS - LLM REASONING")
    print("="*80)
    print()
    
    # 1. Load data
    df = load_reasoning_data()
    
    # 2. Text preprocessing
    df = preprocess_texts(df)
    
    # 3. Create word DataFrame
    word_df = create_word_dataframe(df)
    
    # 4. Compute embeddings
    embeddings, word_df = compute_embeddings(word_df)
    
    # 5. Clustering
    word_df = cluster_words(embeddings, word_df, n_clusters=8)
    
    # 6. Interpret clusters
    cluster_word_dict = interpret_clusters(word_df, top_n=20)
    
    # 7. UMAP visualization
    umap_df = create_umap_visualization(word_df)
    
    # 8. Quantify differences
    results_df = quantify_prompt_differences(word_df)
    
    # 9. Summary
    print_summary(word_df, cluster_word_dict)
    
    print("="*80)
    print(" ANALYSIS COMPLETE")
    print("="*80)
    print()
    
    # Export results
    print("Exporting results...")
    word_df.to_csv('word_clusters.csv', index=False)
    results_df.to_csv('cluster_comparison.csv', index=False)
    print("✓ Results exported:")
    print("  - word_clusters.csv")
    print("  - cluster_comparison.csv")
    print()


if __name__ == "__main__":
    main()
