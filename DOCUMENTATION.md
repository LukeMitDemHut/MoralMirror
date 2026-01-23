# Comprehensive Documentation: Personalized Moral Reasoning Survey Platform

## Overview

This platform implements a research study examining how large language models can generate individualized ethical assessments based on minimal examples. The system collects participant moral reasoning, uses AI to simulate personalized responses, and evaluates the quality of those simulations.

## Architecture

### Technology Stack

- **Backend**: Symfony 7.1 (PHP 8.2)
- **Database**: MySQL 8.0 with Doctrine ORM
- **Frontend**: Twig templates with embedded CSS/JavaScript
- **AI Integration**: OpenAI compatible API (OpenRouter)
- **Deployment**: Docker containers (Web + Database)

### Core Components

#### 1. Entities (Database Models)

**Participant**

- Stores anonymized participant data
- Fields: anonymous_id, nationality, age, gender, consent information
- Tracks current phase of study
- Related to responses, generations, and evaluations

**Vignette**

- EMCS-based moral scenarios
- Fields: title, content, social_proximity (close/distant), protagonist
- 40 pre-loaded scenarios covering various moral dilemmas

**ParticipantResponse**

- Participant's responses to vignettes in Phase 1
- Fields: response text, word_count, validation status, feedback
- Links participant to specific vignette

**LLMGeneration**

- AI-generated personalized responses
- Fields: simulated_response, reasoning, is_zero_shot, temperature
- Stores example order for few-shot generations
- Model version tracking

**Evaluation**

- Participant ratings of generated responses
- Fields: agreement_score (1-7), authenticity_score (1-7)
- Tracks presentation order for analysis

#### 2. Services

**GeminiService**

- Interfaces with Google Gemini API
- Methods:
  - `validateResponse()`: LLM-as-judge quality check
  - `generatePersonalizedResponse()`: Creates simulated responses
- Implements structured output with JSON schemas
- Configurable temperature settings

**SurveyService**

- Orchestrates survey logic
- Methods:
  - `selectVignettesForPhase1()`: Randomly selects 10 vignettes (5 close, 5 distant)
  - `selectVignettesForPhase2()`: Selects unused vignettes for generation
  - `generateLLMResponses()`: Creates 6 few-shot + 6 zero-shot responses
  - `getRandomizedGenerationsForEvaluation()`: Shuffles for blind evaluation

#### 3. Controllers

**HomeController**

- Landing page with study introduction

**SurveyController**

- Complete survey flow management
- Routes:
  - `/survey/start`: Initialize participant session
  - `/survey/consent`: Informed consent collection
  - `/survey/demographics`: Demographic data collection
  - `/survey/phase1`: Baseline response collection (10 vignettes)
  - `/survey/phase1/complete`: Trigger LLM generation
  - `/survey/phase3`: Response evaluation (10 evaluations)
  - `/survey/complete`: Thank you and debrief

#### 4. Templates

**base.html.twig**

- Responsive layout with embedded CSS
- Alert system for flash messages
- Progress bars for multi-step processes
- Likert scale components

**Phase-specific templates**

- consent.html.twig: IRB-compliant informed consent
- demographics.html.twig: Basic demographic collection
- phase1_response.html.twig: Open-ended response form with word counter
- phase3_evaluate.html.twig: Dual Likert scale evaluation

## Study Protocol Implementation

### Phase 1: Moral Baseline Collection

1. Participant sees 10 randomized EMCS vignettes
2. For each, provides 50-100 word moral justification
3. LLM judge validates response quality
4. Invalid responses trigger revision request
5. Validated responses become few-shot examples

### Phase 2: LLM Generation (Automatic)

1. System selects 12 new vignettes (6 few-shot + 6 zero-shot: 3 close/3 distant for each type)
2. For few-shot: shuffles 10 baseline responses to mitigate recency bias
3. Gemini API generates responses at temperature 0.3
4. Each generation includes:
   - simulated_response: What participant sees
   - reasoning: Internal model justification
5. Zero-shot control generates without examples

### Phase 3: Subjective Evaluation

1. Participant evaluates all 12 generated responses
2. Blind presentation (randomized order)
3. Two dimensions:
   - Agreement (1-7): Content alignment with participant's views
   - Authenticity (1-7): Style matching participant's reasoning pattern
4. No indication of few-shot vs zero-shot origin

## Configuration

### Environment Variables (.env)

```
APP_ENV=dev
APP_SECRET=<symfony_secret>
DATABASE_URL=mysql://user:pass@host:port/dbname
GEMINI_API_KEY=<your_google_api_key>
```

### Service Configuration (config/services.yaml)

- Autowiring enabled for dependency injection
- GeminiService receives API key via parameter injection
- All services auto-configured

### Database Configuration (config/packages/doctrine.yaml)

- Doctrine ORM with attribute-based mapping
- Automatic proxy generation in dev mode
- Query/result caching in production

## Setup Instructions

### 1. Prerequisites

- Docker and Docker Compose
- PHP 8.2+ (if running locally)
- Composer

### 2. Installation

```bash
# Clone repository
git clone <repository_url>
cd moralllmassessment

# Start Docker containers
docker compose up -d --build

# Install dependencies
docker compose exec web composer install

# Create database schema
docker compose exec web php bin/console doctrine:database:create
docker compose exec web php bin/console doctrine:schema:create

# Seed vignettes
docker compose exec web php bin/console app:seed-vignettes

# Set Gemini API key in .env
# Edit .env and add: GEMINI_API_KEY=your_actual_key
```

### 3. Access

- Web interface: http://localhost:8080
- MySQL: localhost:3306 (user: symfony, pass: symfony)

## Data Security & Ethics

### Privacy Implementation

- Anonymous IDs generated with cryptographic randomness
- No PII collected beyond basic demographics
- Session-based tracking (cleared on completion)
- Database encryption at rest (MySQL 8.0)
- HTTPS enforced in production

### Consent Management

- IRB-compliant informed consent form
- Explicit AI processing disclosure
- Right to withdraw documented
- Consent timestamp recorded

### Data Retention

- Participant table separates identity from responses
- Anonymous export capability
- GDPR-compliant deletion support

## API Integration Details

### Gemini API Structure

**Validation Prompt Template**

```
Task: Evaluate moral reasoning quality
Input: Vignette + Response
Output: {is_valid: boolean, feedback: string}
Temperature: 0.1 (deterministic)
```

**Generation Prompt Template**

```
Task: Simulate individual's moral reasoning
Input: Target vignette + Few-shot examples (shuffled)
Output: {simulated_response: string, reasoning: string}
Temperature: 0.3 (balanced creativity)
```

### Error Handling

- API timeout: 60 seconds
- Retry logic: Not implemented (manual retry via participant)
- Invalid JSON: Exception thrown with logging

## Extending the Platform

### Adding New Vignettes

1. Edit `SeedVignettesCommand.php`
2. Add vignette array with: title, content, socialProximity, protagonist
3. Run: `php bin/console app:seed-vignettes`

### Changing LLM Provider

1. Create new service implementing same interface
2. Update `config/services.yaml` to inject different API key
3. Modify prompt templates in new service

### Customizing Likert Scale

1. Edit `phase3_evaluate.html.twig`
2. Change loop range: `{% for i in 1..5 %}` (for 5-point scale)
3. Update database validation in controller

### Adding New Study Phases

1. Create new entity if storing new data type
2. Add controller route and method
3. Create corresponding Twig template
4. Update `Participant::currentPhase` logic

## Research Data Export

### Database Queries

**Export all participant responses:**

```sql
SELECT p.anonymous_id, p.age, p.gender, p.nationality,
       v.title, pr.response, pr.word_count, pr.validated
FROM participants p
JOIN participant_responses pr ON p.id = pr.participant_id
JOIN vignettes v ON pr.vignette_id = v.id
ORDER BY p.id, pr.response_order;
```

**Export evaluation results:**

```sql
SELECT p.anonymous_id,
       v.title, v.social_proximity,
       g.is_zero_shot, g.temperature,
       e.agreement_score, e.authenticity_score,
       e.presentation_order
FROM evaluations e
JOIN participants p ON e.participant_id = p.id
JOIN llm_generations g ON e.generation_id = g.id
JOIN vignettes v ON g.vignette_id = v.id
ORDER BY p.id, e.presentation_order;
```

**Compare few-shot vs zero-shot performance:**

```sql
SELECT g.is_zero_shot,
       AVG(e.agreement_score) as avg_agreement,
       AVG(e.authenticity_score) as avg_authenticity,
       COUNT(*) as n
FROM evaluations e
JOIN llm_generations g ON e.generation_id = g.id
GROUP BY g.is_zero_shot;
```

## Troubleshooting

### Common Issues

**Database Connection Failed**

- Check Docker containers: `docker compose ps`
- Verify DATABASE_URL in .env
- Ensure MySQL container is healthy

**Gemini API Errors**

- Verify API key is valid
- Check quota limits in Google Cloud Console
- Review timeout settings (60s default)

**Session Issues**

- Clear browser cookies
- Check session configuration in framework.yaml
- Verify write permissions on var/sessions/

**Word Count Validation Failing**

- JavaScript word counter uses whitespace splitting
- Backend validation may differ slightly
- Ensure textarea updates trigger JS function

## Performance Considerations

### Optimization Strategies

1. **Database Indexes**: Add indexes on foreign keys
2. **Query Optimization**: Use Doctrine query builder efficiently
3. **Caching**: Enable Doctrine result cache in production
4. **API Rate Limiting**: Implement exponential backoff for Gemini
5. **Async Processing**: Consider queue for LLM generation phase

### Scalability

- Current design: ~100-200 concurrent participants
- For larger scale: Add Redis session handler, separate API worker queue
- Database connection pooling configured in doctrine.yaml

## Testing Recommendations

### Unit Tests

- Test GeminiService with mocked HTTP client
- Validate SurveyService selection logic
- Test word count calculations

### Integration Tests

- Full survey flow with test database
- Mock Gemini API responses
- Session persistence across requests

### User Acceptance Testing

- Pilot with 10-20 test participants
- Measure completion time (target: 25-35 minutes)
- Collect feedback on UI/UX

## Contributing

### Code Style

- Follow Symfony best practices
- PSR-12 coding standard
- Use PHP 8.2 features (attributes, readonly properties)

### Git Workflow

- Feature branches from main
- Pull requests required
- Semantic commit messages

## License

Proprietary - Research Use Only

## Contact

Research Team: [Contact Information]
IRB Reference: [IRB Number]

## References

- Symfony Documentation: https://symfony.com/doc/current/
- Gemini API: https://ai.google.dev/docs
- EMCS Scale: Singer et al. (2019)
- Study Protocol: See Paper.txt in repository root
