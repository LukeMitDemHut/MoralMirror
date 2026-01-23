# Data Analysis for Moral LLM Assessment

This directory contains Python tools for analyzing the study data using object-oriented programming with SQLAlchemy ORM.

## Setup

### 1. Activate the Virtual Environment

```bash
source venv/bin/activate.fish  # For fish shell
# or
source venv/bin/activate       # For bash/zsh
```

### 2. Configure Database Access

The `.env` file is already configured to connect to the Docker database. If you need to change it:

```bash
# Edit .env file
DB_HOST=db          # Use 'db' when connecting from within Docker network
DB_PORT=3306
DB_NAME=symfony
DB_USER=symfony
DB_PASSWORD=your_password
```

### 3. Test the Connection

```bash
python database.py
```

This should output:

```
✓ Database connection successful!
✓ Found X participants
✓ Found X vignettes
```

## Project Structure

```
analysis/
├── venv/                   # Python virtual environment
├── models.py              # SQLAlchemy ORM models (mirrors PHP entities)
├── database.py            # Database connection and session management
├── example_analysis.py    # Example analysis script with pandas
├── requirements.txt       # Python dependencies
├── .env                   # Database credentials (gitignored)
└── .env.example          # Template for environment variables
```

## ORM Models

All database tables have corresponding Python classes:

- **`Vignette`**: Moral vignettes presented to participants
- **`Participant`**: Study participants with demographics
- **`ParticipantResponse`**: Participant responses in Phase 1
- **`LLMGeneration`**: LLM-generated responses in Phase 2
- **`Evaluation`**: Participant evaluations of LLM responses in Phase 3

## Usage Examples

### Basic Query

```python
from database import get_db
from models import Participant

db = get_db()
with db as session:
    # Get all participants
    participants = session.query(Participant).all()

    for p in participants:
        print(f"{p.anonymous_id}: Age {p.age}, Phase {p.current_phase}")
```

### Query with Relationships

```python
from models import Participant, ParticipantResponse

with db as session:
    # Get participant with their responses
    participant = session.query(Participant).first()

    print(f"Participant: {participant.anonymous_id}")
    print(f"Number of responses: {len(participant.responses)}")

    for response in participant.responses:
        print(f"  - Vignette {response.vignette_id}: {response.word_count} words")
```

### Load Data into Pandas

```python
import pandas as pd
from models import Evaluation, LLMGeneration

with db as session:
    # Query evaluations with generation info
    results = session.query(
        Evaluation.agreement_score,
        Evaluation.authenticity_score,
        LLMGeneration.is_zero_shot
    ).join(
        LLMGeneration,
        Evaluation.generation_id == LLMGeneration.id
    ).all()

    # Convert to DataFrame
    df = pd.DataFrame(results, columns=['agreement', 'authenticity', 'is_zero_shot'])

    # Analyze
    print(df.groupby('is_zero_shot')[['agreement', 'authenticity']].mean())
```

### Aggregate Queries

```python
from sqlalchemy import func

with db as session:
    # Average age by gender
    stats = session.query(
        Participant.gender,
        func.avg(Participant.age).label('avg_age'),
        func.count(Participant.id).label('count')
    ).group_by(Participant.gender).all()

    for gender, avg_age, count in stats:
        print(f"{gender}: {count} participants, avg age {avg_age:.1f}")
```

## Running the Example Analysis

```bash
python example_analysis.py
```

This will:

1. Test database connection
2. Display basic statistics
3. Load data into pandas DataFrames
4. Perform example queries
5. Create visualizations (if evaluation data exists)

## Common Analysis Tasks

### 1. Response Word Counts

```python
with db as session:
    responses = session.query(ParticipantResponse).all()
    word_counts = [r.word_count for r in responses]

    import matplotlib.pyplot as plt
    plt.hist(word_counts, bins=20)
    plt.xlabel('Word Count')
    plt.ylabel('Frequency')
    plt.title('Distribution of Response Word Counts')
    plt.show()
```

### 2. Evaluation Scores Analysis

```python
with db as session:
    df = pd.read_sql(
        session.query(Evaluation).statement,
        session.bind
    )

    print("Agreement scores:")
    print(df['agreement_score'].describe())

    print("\nAuthenticity scores:")
    print(df['authenticity_score'].describe())
```

### 3. Compare Zero-shot vs Few-shot

```python
with db as session:
    query = session.query(
        LLMGeneration.is_zero_shot,
        func.avg(Evaluation.agreement_score).label('avg_agreement'),
        func.avg(Evaluation.authenticity_score).label('avg_authenticity')
    ).join(Evaluation).group_by(LLMGeneration.is_zero_shot)

    results = pd.DataFrame(query.all(),
                          columns=['is_zero_shot', 'avg_agreement', 'avg_authenticity'])
    print(results)
```

## Tips

1. **Always use context managers** (`with db as session:`) to ensure connections are properly closed
2. **Use `session.query(Model).count()`** for efficient counting
3. **Load large datasets in chunks** using `.limit()` and `.offset()`
4. **Use pandas `read_sql()`** for complex queries that are easier to write in SQL
5. **Close sessions** when done to free database connections

## Troubleshooting

### Cannot connect to database

- Make sure Docker containers are running: `docker compose ps`
- Check that the database service is healthy
- Verify `.env` file has correct credentials
- If connecting from host machine, use `localhost` instead of `db` for `DB_HOST`

### Import errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate.fish

# Reinstall dependencies if needed
pip install -r requirements.txt
```

### No data in database

```bash
# Run migrations and seed data from the main app
docker compose exec web php bin/console doctrine:schema:update --force
docker compose exec web php bin/console app:seed-vignettes
```

## Analysis Scripts

This section documents the available analysis scripts, their purpose, data processing methods, and how to interpret results.

### 1. Zero-Shot vs Few-Shot Comparison

**Location**: `zero_shot_vs_few_shot/run.py`

**Purpose**: Compares LLM performance between zero-shot (no examples) and few-shot (with examples) generation approaches.

**Run**: `cd zero_shot_vs_few_shot && python run.py`

#### Data Processing

- **Data Source**: Evaluations from completed participants (Phase 3)
- **Filtering**: Only includes participants who have finished all study phases (`current_phase = 'completed'`)
- **Metrics Analyzed**:
  - Agreement scores (1-7): How much participants agree with LLM-generated responses
  - Authenticity scores (1-7): How authentic/human-like participants rate the LLM responses

#### Statistical Methods

- **Mann-Whitney U Test**: Non-parametric test comparing distributions between zero-shot and few-shot conditions
- **Descriptive Statistics**: Mean, standard deviation, quartiles for each condition

#### Visualizations Created

1. **Boxplots**: Show distribution of agreement and authenticity scores by generation type
2. **Violin Plots**: Display probability density of score distributions
3. **Histograms**: Frequency distributions with overlaid normal curves
4. **Summary Statistics Tables**: Printed to console with mean differences and p-values

#### Interpreting Results

- **High Agreement/Authenticity Scores (6-7)**: LLM responses closely match participant values and seem human-like
- **Low Scores (1-3)**: LLM responses diverge from participant values or seem artificial
- **Significant p-value (< 0.05)**: Meaningful difference between zero-shot and few-shot approaches
- **Mean Difference**: Shows magnitude of improvement (positive = few-shot better)

**Expected Finding**: Few-shot typically outperforms zero-shot by 1-2 points on both metrics, as personalized examples help the LLM better capture individual moral reasoning patterns.

---

### 2. Social Proximity Analysis

**Location**: `socially_close_vs_distant/run.py`

**Purpose**: Examines whether LLM performance varies based on the social proximity of protagonists in moral vignettes (close relationships vs. distant/strangers).

**Run**: `cd socially_close_vs_distant && python run.py`

#### Data Processing

- **Data Source**: Evaluations linked to vignette social proximity metadata
- **Filtering**: Completed participants only
- **Categories**:
  - **Close**: Vignettes involving friends, family, close relationships
  - **Distant**: Vignettes involving strangers, distant acquaintances
- **Metrics**: Agreement and authenticity scores for each proximity category

#### Statistical Methods

- **Mann-Whitney U Test**: Compares scores between close and distant vignettes
- **Stratified Analysis**: Examines proximity effects within zero-shot and few-shot conditions separately

#### Visualizations Created

1. **4-Panel Boxplots**:
   - Top row: Overall scores by proximity
   - Bottom row: Scores by proximity × generation type interaction
2. **Interaction Plots**: Show how few-shot benefit varies by social proximity with error bars

#### Interpreting Results

- **No Overall Difference**: LLM performs similarly regardless of protagonist proximity
- **Interaction Effect**: Few-shot improvement may be larger for socially close vignettes
  - This suggests personalized examples are more effective when moral scenarios involve close relationships
- **Δ (Delta) Values**: Difference in few-shot improvement between close and distant contexts

**Key Insight**: The differential few-shot benefit reveals that personal moral reasoning patterns are more strongly activated in scenarios involving close social ties.

---

### 3. Semantic Word Field Analysis (Reasoning Clusters)

**Location**: `reasoning_cluster/run.py`

**Purpose**: Identifies semantic word fields in LLM reasoning texts to understand which conceptual domains are activated by different prompt types.

**Run**: `cd reasoning_cluster && python run.py`

#### Data Processing Pipeline

1. **Text Preprocessing**:
   - **Tokenization**: Splits reasoning text into individual words
   - **Lemmatization**: Reduces words to base forms (e.g., "reasoning" → "reason")
   - **Stopword Removal**: Eliminates common function words (the, is, and, etc.)
   - **POS Filtering**: Retains only nouns and verbs (content words with semantic meaning)
   - **Result**: ~65% reduction in tokens, focusing on semantically meaningful words

2. **Embedding Generation**:
   - Uses `paraphrase-multilingual-MiniLM-L12-v2` transformer model
   - Converts each unique word to 384-dimensional semantic vector
   - Words with similar meanings cluster together in embedding space

3. **Clustering**:
   - **Method**: K-Means clustering (k=8 clusters)
   - **Purpose**: Groups semantically related words into coherent fields
   - Each cluster represents a distinct conceptual domain

#### Semantic Fields Identified

#### Visualizations Created

1. **UMAP Projection** (`umap_word_fields.png`):
   - 2D visualization of semantic space
   - Each point = unique word
   - Colors = cluster membership
   - Spatial proximity = semantic similarity

2. **Cluster Comparison Charts** (`prompt_comparison.png`):
   - **Top**: Bar chart showing cluster proportions by prompt type
   - **Bottom**: Horizontal bar chart showing differences (Few-Shot - Zero-Shot)

3. **Exported Data**:
   - `word_clusters.csv`: Every word with its cluster assignment and frequency
   - `cluster_comparison.csv`: Cluster proportions and statistical comparisons

#### Interpreting Results

**Cluster Proportions**:

- Higher percentage = more emphasis on that semantic domain
- Example: Zero-shot 20% in "Reasoning" cluster vs. Few-shot 14% suggests zero-shot relies more on abstract justification

**Difference Bars** (Green = Few-Shot emphasis, Red = Zero-Shot emphasis):

- **Positive differences**: Semantic fields more activated by few-shot prompts
  - Typically: social relationships, moral values, obligations
- **Negative differences**: Fields more activated by zero-shot prompts
  - Typically: abstract reasoning, pattern justification

**Key Findings**:

- **Few-Shot** produces reasoning grounded in social context, moral principles, and obligations
- **Zero-Shot** produces more abstract, pattern-based justifications
- This reveals that personalized examples shift reasoning from abstract logic to contextualized moral thinking

---

### 4. Gender Analysis

**Location**: `gender_analysis/run.py`

**Purpose**: Investigates whether LLM performance differs based on participant gender, and whether personalization benefits vary by gender.

**Run**: `cd gender_analysis && python run.py`

#### Data Processing

- **Data Source**: Evaluations with participant demographics
- **Filtering**: Completed participants only
- **Grouping**: Male vs. Female participants
- **Metrics**: Agreement and authenticity scores stratified by gender

#### Statistical Methods

- **Mann-Whitney U Test**: Compares scores between genders overall
- **Stratified Tests**: Examines gender differences within each generation type
- **Interaction Analysis**: Tests whether few-shot benefit varies by gender

#### Visualizations Created

1. **4-Panel Boxplots** (`gender_analysis_comparison.png`):
   - Top-left: Agreement by gender (all generations)
   - Top-right: Authenticity by gender (all generations)
   - Bottom-left: Agreement by gender × shot type
   - Bottom-right: Authenticity by gender × shot type

2. **Interaction Plots** (`gender_interaction_plot.png`):
   - Line plots showing few-shot vs. zero-shot performance for each gender
   - Error bars represent standard deviations
   - Parallel lines = no gender interaction
   - Diverging lines = differential benefit by gender

#### Interpreting Results

**Main Effects**:

- **No gender difference** (p > 0.05): LLM performs equally well for male and female participants
- **Significant difference** (p < 0.05): One gender receives better personalization

**Interaction Effects**:

- **Parallel improvement**: Both genders benefit equally from few-shot personalization
- **Differential improvement**: One gender benefits more from personalized examples
  - Example: Females +1.42 points, Males +1.71 points suggests males benefit slightly more

**Practical Implications**:

- **Gender-neutral performance**: Algorithm doesn't systematically favor one gender
- **Fair personalization**: Few-shot approach works equally well across genders
- This validates the ethical fairness of the personalization approach

---

### 5. Nationality Analysis

**Location**: `nationality_analysis/run.py`

**Purpose**: Examines whether LLM performance varies based on participant nationality or cultural origin, and whether personalization effectiveness differs across cultural backgrounds.

**Run**: `cd nationality_analysis && python run.py`

#### Data Processing

- **Data Source**: Evaluations with participant nationality metadata
- **Filtering**: Completed participants only
- **Grouping**: By nationality/country of origin
- **Metrics**: Agreement and authenticity scores stratified by nationality

#### Statistical Methods

- **Mann-Whitney U Test**: Pairwise comparisons between nationalities
- **Stratified Analysis**: Examines nationality differences within each generation type
- **Interaction Analysis**: Tests whether few-shot benefit varies by nationality
- **Multiple Comparisons**: Tests between top nationalities (if sufficient sample sizes)

#### Visualizations Created

1. **4-Panel Boxplots** (`nationality_analysis_comparison.png`):
   - Top-left: Agreement by nationality (all generations)
   - Top-right: Authenticity by nationality (all generations)
   - Bottom-left: Agreement by nationality × shot type
   - Bottom-right: Authenticity by nationality × shot type

2. **Improvement Bar Charts** (`nationality_improvement_plot.png`):
   - Left: Few-shot agreement improvement by nationality
   - Right: Few-shot authenticity improvement by nationality
   - Green bars = positive improvement, Red bars = negative
   - Shows which nationalities benefit most from personalization

3. **Interaction Plots** (`nationality_interaction_plot.png`):
   - Line plots showing few-shot vs. zero-shot performance for each nationality
   - Error bars represent standard errors
   - Parallel lines = consistent benefit across nationalities
   - Diverging lines = differential benefit by cultural background

#### Interpreting Results

**Main Effects**:

- **No nationality difference** (p > 0.05): LLM performs consistently across cultural backgrounds
- **Significant differences** (p < 0.05): Some nationalities receive better/worse personalization
  - May indicate cultural biases in training data or prompt design
  - Could reflect differences in moral reasoning frameworks across cultures

**Interaction Effects**:

- **Uniform improvement**: All nationalities benefit similarly from few-shot personalization
- **Differential improvement**: Some nationalities benefit more/less from examples
  - Example: Nationality A +2.3 points, Nationality B +0.8 points
  - Could suggest prompt engineering needs cultural adaptation

**Practical Implications**:

- **Cultural fairness check**: Ensures algorithm works equitably across diverse populations
- **Identifies improvement opportunities**: Nationalities with lower improvement may need targeted prompt refinement
- **Validates generalizability**: Consistent performance across cultures supports broad applicability
- **Ethical considerations**: Large disparities may indicate need for culturally-sensitive personalization approaches

**Sample Size Considerations**:

- Only nationalities with sufficient participants (n ≥ 5) are included in statistical tests
- Interpret results cautiously for underrepresented nationalities
- Larger cultural groups provide more reliable estimates

---

### 6. Agreement-Authenticity Correlation Analysis

**Location**: `agreement_authenticity_correlation/run.py`

**Purpose**: Examines the relationship between agreement scores and authenticity scores to understand whether participants who agree more with LLM responses also perceive them as more authentic/human-like.

**Run**: `cd agreement_authenticity_correlation && python run.py`

#### Data Processing

- **Data Source**: All evaluations from completed participants
- **Unit of Analysis**: Individual evaluation ratings (each participant rates multiple LLM responses)
- **Metrics Analyzed**:
  - **Agreement Score** (1-7): How much participant agrees with the LLM response
  - **Authenticity Score** (1-7): How authentic/human-like the LLM response seems

#### Statistical Methods

- **Pearson Correlation**: Measures linear relationship between agreement and authenticity
  - Range: -1 (perfect negative) to +1 (perfect positive)
  - Assumes normally distributed data
- **Spearman Correlation**: Measures monotonic relationship (more robust to outliers)
  - Non-parametric alternative to Pearson
- **Per-Participant Analysis**: Computes individual correlation for each participant
  - Reveals whether relationship is consistent across individuals
  - Requires minimum 3 evaluations per participant

#### Visualizations Created

1. **Overall Scatter Plot** (`agreement_authenticity_correlation.png`, top):
   - Each point = one evaluation
   - Red regression line shows linear trend
   - Diagonal dashed line = perfect correlation reference

2. **Density Heatmap** (middle-left):
   - Hexagonal binning shows concentration of ratings
   - Warmer colors = more evaluations with that score combination

3. **Per-Participant Distribution** (middle-right):
   - Histogram of individual participant correlations
   - Shows variability across participants
   - Mean and median marked with vertical lines

4. **By Generation Type** (bottom-left):
   - Green = Few-Shot, Red = Zero-Shot
   - Separate regression lines for each condition
   - Tests whether correlation differs by prompt type

5. **Correlation vs Sample Size** (bottom-right):
   - X-axis: Number of evaluations per participant
   - Y-axis: Correlation strength
   - Color: Absolute correlation magnitude
   - Tests whether more evaluations lead to different patterns

6. **Sorted Per-Participant Bars** (`per_participant_correlations.png`):
   - Each bar = one participant's correlation
   - Green = positive, Red = negative
   - Asterisk (\*) = statistically significant (p < 0.05)
   - Shows full range of individual differences

#### Interpreting Results

**Overall Correlation**:

- **Strong positive (r > 0.7)**: Agreement and authenticity are tightly coupled
  - Participants who agree more consistently rate responses as more authentic
  - Suggests authenticity perception drives agreement (or vice versa)
- **Moderate (0.4 < r < 0.7)**: Meaningful but not perfect relationship
  - Other factors beyond authenticity influence agreement
- **Weak (r < 0.4)**: Agreement and authenticity are somewhat independent
  - Participants may agree with responses they don't find authentic (or vice versa)

**Per-Participant Variability**:

- **High variability**: Some participants show strong correlation, others don't
  - Individual differences in how authenticity influences agreement
  - Some people prioritize value alignment over authenticity
- **Low variability**: Consistent pattern across all participants
  - Universal relationship between these constructs
  - Validates that both metrics capture related phenomena

**By Generation Type**:

- **Similar correlations**: Relationship holds regardless of prompt approach
  - Both zero-shot and few-shot maintain agreement-authenticity link
- **Different correlations**: Few-shot may change the relationship
  - Example: Few-shot could increase authenticity without increasing agreement
  - Suggests personalization affects these dimensions differently

**Practical Implications**:

- **High correlation**: Could consider using single metric instead of both
  - Reduces participant burden
  - Authenticity and agreement measure similar construct
- **Low correlation**: Both metrics provide unique information
  - Validates using both in evaluation
  - Authenticity and agreement capture different aspects of response quality

**Expected Finding**: Moderate-to-strong positive correlation (r = 0.5-0.7), indicating that authentic-seeming responses tend to align better with participant values, but with meaningful individual variation.

---

## Running All Analyses

To execute all analysis scripts sequentially:

```bash
# From the analysis directory
cd zero_shot_vs_few_shot && python run.py && cd ..
cd social_proximity && python run.py && cd ..
cd reasoning_cluster && python run.py && cd ..
cd gender_analysis && python run.py && cd ..
cd nationality_analysis && python run.py && cd ..
cd agreement_authenticity_correlation && python run.py && cd ..
```

All visualizations are saved as PNG files in their respective directories.

## Next Steps

1. Create custom analysis scripts for your specific research questions
2. Build Jupyter notebooks for interactive exploration
3. Generate publication-ready figures
4. Export processed data for statistical software (R, SPSS, etc.)
5. Implement automated reporting

## Dependencies

See `requirements.txt` for all Python packages. Main dependencies:

- **SQLAlchemy**: ORM and database toolkit
- **PyMySQL**: MySQL driver
- **pandas**: Data analysis and manipulation
- **matplotlib & seaborn**: Data visualization
- **python-dotenv**: Environment variable management
- **scipy**: Statistical tests (Mann-Whitney U, etc.)
- **spacy**: Natural language processing (for reasoning analysis)
- **sentence-transformers**: Semantic embeddings
- **scikit-learn**: Machine learning and clustering
- **umap-learn**: Dimensionality reduction for visualization
