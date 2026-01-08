# MoralMirror - Personalized Moral Reasoning Survey Platform

A Symfony-based research platform for testing personalized moral reasoning simulations using Large Language Models.

## Overview

This application implements a three-phase study design investigating how accurately state-of-the-art LLMs can generate individualized ethical assessments from minimal examples.

### Study Phases

1. **Phase 1 - Moral Baseline Collection**: Participants respond to 10 EMCS vignettes with detailed moral justifications (50-100 words each)
2. **Phase 2 - LLM Generation** (Automatic): System generates 6 few-shot and 6 zero-shot personalized responses using Gemini 3 Pro
3. **Phase 3 - Evaluation**: Participants rate generated responses on agreement and authenticity using 7-point Likert scales

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenRouter API Key (https://openrouter.ai/)

### Setup

```bash
# Start containers
docker compose up -d --build

# Install dependencies
docker compose exec web composer install

# Create database
docker compose exec web php bin/console doctrine:database:create
docker compose exec web php bin/console doctrine:schema:create

# Seed vignettes
docker compose exec web php bin/console app:seed-vignettes

# Workers start automatically with docker compose up (10 replicas)
# To view worker logs:
docker compose logs -f worker

# Configure API
# Edit .env and set:
# LLM_API_KEY=your_openrouter_api_key
# LLM_API_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
# LLM_MODEL=anthropic/claude-3.5-sonnet
```

> **⚡ Workers**: The Docker setup now includes 10 worker replicas that automatically start with `docker compose up`. These process LLM generation requests in parallel. See [ASYNC_WORKER_SETUP.md](ASYNC_WORKER_SETUP.md) for details.

### Access

- Application: http://localhost:8080
- Database: localhost:3306 (user: symfony, password: symfony)

## Architecture

### Technology Stack

- **Backend**: Symfony 7.1 (PHP 8.2)
- **Database**: MySQL 8.0 with Doctrine ORM
- **Message Queue**: Symfony Messenger with Doctrine transport
- **Frontend**: Twig templates with embedded CSS/JavaScript
- **AI**: OpenRouter API (supports multiple LLM providers)
- **Deployment**: Docker

### Key Features

✅ **Complete Survey Flow**

- Informed consent with AI processing disclosure
- Demographic data collection
- 10-vignette response collection with LLM-as-judge validation
- **Async parallel LLM response generation (8-10x faster)**
- Blind evaluation with dual-dimension Likert scales

✅ **Research Compliance**

- IRB-compliant consent management
- Anonymous participant tracking
- Data encryption in transit and at rest
- Session-based state management

✅ **LLM Integration**

- OpenRouter API with OpenAI-compatible format
- Configurable model selection (Claude, GPT-4, Llama, etc.)
- Temperature-controlled generation (0.3 for responses, 0.1 for validation)
- Shuffled few-shot examples to mitigate recency bias
- Zero-shot control group for baseline comparison

✅ **Data Collection**

- Participant responses with word counts
- LLM generations with reasoning traces
- Example order tracking for reproducibility
- Evaluation scores on two dimensions (agreement & authenticity)

## Project Structure

```
├── src/
│   ├── Command/           # CLI commands (seed vignettes)
│   ├── Controller/        # Survey flow & routing
│   ├── Entity/           # Database models (Doctrine ORM)
│   └── Service/          # Business logic (Gemini API, Survey orchestration)
├── templates/            # Twig views
│   ├── home/            # Landing page
│   └── survey/          # Survey phase templates
├── config/              # Symfony configuration
│   └── packages/        # Package-specific configs
├── public/              # Web root (index.php)
└── var/                 # Logs, cache, sessions
```

## Database Schema

### Core Entities

- **Participant**: Anonymous participant data, consent, demographics, current phase
- **Vignette**: EMCS moral scenarios with social proximity classification
- **ParticipantResponse**: Phase 1 responses with validation status
- **LLMGeneration**: AI-generated responses with reasoning and metadata
- **Evaluation**: Phase 3 Likert scale ratings

## Configuration

### Environment Variables (.env)

```env
APP_ENV=dev
APP_SECRET=<symfony_secret>
DATABASE_URL=mysql://symfony:symfony@db:3306/symfony
LLM_API_KEY=<your_openrouter_api_key>
LLM_API_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
LLM_MODEL=anthropic/claude-3.5-sonnet
```

### Important Settings

- **Temperature**: 0.3 for generation, 0.1 for validation
- **Word Count**: 50-100 words for participant responses
- **Likert Scale**: 1-7 for both agreement and authenticity
- **Vignette Distribution**: 5 close + 5 distant protagonists per phase

## Usage

### Running the Survey

1. Navigate to http://localhost:8080
2. Click "Begin Study"
3. Read and accept informed consent
4. Provide demographics
5. Complete Phase 1: Respond to 10 vignettes
6. System auto-generates Phase 2 responses
7. Complete Phase 3: Evaluate 12 generated responses
8. View completion screen with anonymous ID

### Administrative Commands

```bash
# Seed vignettes
docker compose exec web php bin/console app:seed-vignettes

# Clear cache
docker compose exec web php bin/console cache:clear

# View database schema
docker compose exec web php bin/console doctrine:schema:update --dump-sql

# Export data (SQL examples in DOCUMENTATION.md)
docker compose exec db mysql -u symfony -psymfony symfony
```

## Data Export & Analysis

### Example SQL Queries

**Participant responses:**

```sql
SELECT p.anonymous_id, v.title, pr.response, pr.word_count
FROM participants p
JOIN participant_responses pr ON p.id = pr.participant_id
JOIN vignettes v ON pr.vignette_id = v.id;
```

**Few-shot vs Zero-shot comparison:**

```sql
SELECT g.is_zero_shot,
       AVG(e.agreement_score) as avg_agreement,
       AVG(e.authenticity_score) as avg_authenticity
FROM evaluations e
JOIN llm_generations g ON e.generation_id = g.id
GROUP BY g.is_zero_shot;
```

## Security & Ethics

- ✅ Anonymous participant IDs (cryptographic randomness)
- ✅ No PII beyond basic demographics
- ✅ Informed consent with AI processing disclosure
- ✅ Session-based tracking (cleared on completion)
- ✅ Database encryption (MySQL 8.0)
- ✅ HTTPS enforced in production

## Extending the Platform

### Add New Vignettes

Edit `src/Command/SeedVignettesCommand.php` and add to vignettes array:

```php
[
    'title' => 'Your Title',
    'content' => 'Your scenario description',
    'socialProximity' => 'close', // or 'distant'
    'protagonist' => 'friend' // or other relationship
]
```

### Change LLM Provider

Edit `.env` and change the model:

```env
# Use Claude (recommended for research)
LLM_MODEL=anthropic/claude-3.5-sonnet

# Use GPT-4
LLM_MODEL=openai/gpt-4-turbo

# Use Llama (cost-effective)
LLM_MODEL=meta-llama/llama-3.1-70b-instruct
```

No code changes needed! See `OPENROUTER_MIGRATION.md` for all available models.

### Customize Evaluation Scale

Edit `templates/survey/phase3_evaluate.html.twig`:

```twig
{% for i in 1..5 %}  {# Change to 5-point scale #}
```

## Troubleshooting

**Database connection failed**: Check docker compose status and DATABASE_URL
**Gemini API errors**: Verify API key and quota in Google Cloud Console
**Session issues**: Clear browser cookies and check var/sessions/ permissions
**Word count mismatch**: JS counter uses whitespace split, may differ slightly

## Testing

Run the application with test data:

```bash
# Create test participant
# Navigate through full survey flow
# Verify data in database
docker compose exec db mysql -u symfony -psymfony symfony
> SELECT * FROM participants;
```

## Documentation

See `DOCUMENTATION.md` for comprehensive technical documentation including:

- Detailed architecture explanation
- API integration details
- Database schema with relationships
- Research data export queries
- Performance optimization strategies
- Contributing guidelines

## Research Context

This platform implements the study design outlined in `Paper.txt`, investigating:

> "How accurately can state of the art large language models generate individualized ethical assessments from minimal examples?"

Based on research showing:

- LLMs have intrinsic moral understanding (Schramowski et al., 2022)
- Moral judgments follow psychologically stable patterns (Forsyth, 2019)
- Few-shot learning excels with minimal examples (Brown et al., 2020)
- EMCS scale measures everyday moral decisions (Singer et al., 2019)

## License

Proprietary - Research Use Only

## Support

For technical issues or research questions, contact the research team.

## References

- Study Protocol: `Paper.txt`
- OpenRouter Migration: `OPENROUTER_MIGRATION.md`
- Symfony: https://symfony.com/doc/current/
- OpenRouter API: https://openrouter.ai/docs
- Doctrine ORM: https://www.doctrine-project.org/
