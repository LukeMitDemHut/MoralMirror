# Quick Reference Guide - Moral Reasoning Survey Platform

## 🚀 Quick Start (5 minutes)

```bash
# 1. Run setup script
./setup.sh

# 2. Open browser
http://localhost:8080

# 3. Start testing!
```

## 📋 Essential Commands

### Docker Management

```bash
# Start application
docker compose up -d

# Stop application
docker compose down

# View logs
docker compose logs -f web

# Restart services
docker compose restart
```

### Database Operations

```bash
# Access MySQL shell
docker compose exec db mysql -u symfony -psymfony symfony

# Backup database
docker compose exec db mysqldump -u symfony -psymfony symfony > backup.sql

# Restore database
docker compose exec -T db mysql -u symfony -psymfony symfony < backup.sql
```

### Symfony Console Commands

```bash
# Seed vignettes
docker compose exec web php bin/console app:seed-vignettes

# Clear cache
docker compose exec web php bin/console cache:clear

# List all routes
docker compose exec web php bin/console debug:router

# Check database schema
docker compose exec web php bin/console doctrine:schema:validate
```

## 🗂️ File Locations

### Configuration

- **Environment**: `.env` (API keys, database URL)
- **Services**: `config/services.yaml` (dependency injection)
- **Routing**: `config/routes.yaml` (URL routes)
- **Database**: `config/packages/doctrine.yaml` (ORM config)

### Code

- **Entities**: `src/Entity/` (database models)
- **Controllers**: `src/Controller/` (request handlers)
- **Services**: `src/Service/` (business logic)
- **Commands**: `src/Command/` (CLI tools)

### Views

- **Base Template**: `templates/base.html.twig` (layout & CSS)
- **Survey Templates**: `templates/survey/*.html.twig` (all phases)
- **Home Template**: `templates/home/index.html.twig` (landing page)

## 🔑 Key Entities

```
Participant
├── anonymousId (string, unique)
├── nationality, age, gender
├── consentGiven, consentDate
├── currentPhase (demographic/phase1/phase3/completed)
└── Relations: responses, generations, evaluations

Vignette
├── title, content
├── socialProximity (close/distant)
└── protagonist (friend/stranger/etc)

ParticipantResponse
├── participant → Participant
├── vignette → Vignette
├── response (text)
├── wordCount, validated
└── responseOrder

LLMGeneration
├── participant → Participant
├── vignette → Vignette
├── simulatedResponse (text shown to participant)
├── reasoning (internal model justification)
├── isZeroShot (boolean)
└── exampleOrder (array)

Evaluation
├── participant → Participant
├── generation → LLMGeneration
├── agreementScore (1-7)
├── authenticityScore (1-7)
└── presentationOrder
```

## 🌐 Survey Routes

```
/                           → Welcome page
/survey/start              → Initialize session
/survey/consent            → Informed consent (POST)
/survey/demographics       → Demographics form
/survey/demographics/submit → Save demographics (POST)
/survey/phase1             → Baseline response collection
/survey/phase1/submit      → Submit response (POST)
/survey/phase1/complete    → Trigger LLM generation
/survey/phase3             → Evaluate responses
/survey/phase3/submit      → Submit evaluation (POST)
/survey/complete           → Thank you & debrief
```

## 🧪 Testing Workflow

### 1. Manual Test Run

1. Navigate to http://localhost:8080
2. Click "Begin Study"
3. Accept consent
4. Fill demographics
5. Complete 10 response forms (50-100 words each)
6. Wait for LLM generation (automatic)
7. Evaluate 12 generated responses
8. View completion screen

### 2. Verify Data

```sql
-- Check participants
SELECT * FROM participants ORDER BY created_at DESC LIMIT 5;

-- Check responses
SELECT COUNT(*) FROM participant_responses WHERE participant_id = 1;

-- Check generations
SELECT COUNT(*), is_zero_shot FROM llm_generations
WHERE participant_id = 1 GROUP BY is_zero_shot;

-- Check evaluations
SELECT AVG(agreement_score), AVG(authenticity_score)
FROM evaluations WHERE participant_id = 1;
```

## 📊 Data Export Queries

### Complete Participant Dataset

```sql
SELECT
    p.anonymous_id,
    p.age,
    p.gender,
    p.nationality,
    v.title AS vignette,
    v.social_proximity,
    pr.response,
    pr.word_count,
    g.simulated_response,
    g.is_zero_shot,
    e.agreement_score,
    e.authenticity_score
FROM participants p
JOIN participant_responses pr ON p.id = pr.participant_id
JOIN vignettes v ON pr.vignette_id = v.id
LEFT JOIN llm_generations g ON g.participant_id = p.id AND g.vignette_id != pr.vignette_id
LEFT JOIN evaluations e ON e.generation_id = g.id
WHERE p.current_phase = 'completed';
```

### Few-shot vs Zero-shot Analysis

```sql
SELECT
    g.is_zero_shot,
    COUNT(*) as n,
    AVG(e.agreement_score) as avg_agreement,
    AVG(e.authenticity_score) as avg_authenticity,
    STDDEV(e.agreement_score) as sd_agreement,
    STDDEV(e.authenticity_score) as sd_authenticity
FROM evaluations e
JOIN llm_generations g ON e.generation_id = g.id
GROUP BY g.is_zero_shot;
```

## 🔧 Configuration Variables

### Required Environment Variables (.env)

```bash
APP_ENV=dev                    # dev/prod
APP_SECRET=<random_string>     # Symfony secret
DATABASE_URL=mysql://...       # Database connection
GEMINI_API_KEY=<your_key>     # Google Gemini API key
```

### Important Settings

- **Temperature**: 0.3 (generation), 0.1 (validation)
- **Word Count**: 50-100 words
- **Vignettes**: 10 per phase (5 close + 5 distant)
- **Generations**: 6 few-shot (3 close + 3 distant) + 6 zero-shot (3 close + 3 distant)
- **Likert Scale**: 1-7 points
- **Timeout**: 60 seconds for API calls

## 🐛 Troubleshooting

### "Database connection failed"

```bash
# Check containers
docker compose ps

# Restart database
docker compose restart db

# Wait 10 seconds and try again
```

### "Gemini API error"

```bash
# Check API key in .env
cat .env | grep GEMINI_API_KEY

# Test API key manually
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY"
```

### "Word count validation failing"

- JavaScript counts words on space split
- Ensure response is between 50-100 words
- Try pasting into a word counter to verify

### "Session lost"

```bash
# Check var/sessions directory permissions
docker compose exec web ls -la var/sessions/

# Clear sessions
docker compose exec web rm -rf var/sessions/*
```

### "Cannot find vignettes"

```bash
# Reseed database
docker compose exec web php bin/console app:seed-vignettes
```

## 📝 Common Modifications

### Change Word Count Range

Edit `src/Controller/SurveyController.php`:

```php
if ($wordCount < 30 || $wordCount > 80) { // Changed from 50-100
```

### Add New Vignette

Edit `src/Command/SeedVignettesCommand.php`:

```php
[
    'title' => 'New Scenario',
    'content' => 'Your scenario text...',
    'socialProximity' => 'close', // or 'distant'
    'protagonist' => 'friend'
]
```

Then run: `docker compose exec web php bin/console app:seed-vignettes`

### Change Likert Scale

Edit `templates/survey/phase3_evaluate.html.twig`:

```twig
{% for i in 1..5 %}  {# Change from 1..7 to 1..5 #}
```

### Modify Generation Temperature

Edit `src/Service/GeminiService.php`:

```php
$result = $this->callGeminiAPI($prompt, 0.5, ...); // Changed from 0.3
```

## 🎯 Performance Tips

### Production Optimization

```bash
# Install production dependencies
docker compose exec web composer install --no-dev --optimize-autoloader

# Clear and warm cache
docker compose exec web php bin/console cache:clear --env=prod
docker compose exec web php bin/console cache:warmup --env=prod

# Set APP_ENV=prod in .env
```

### Database Indexing

```sql
-- Add indexes for better performance
CREATE INDEX idx_participant_phase ON participants(current_phase);
CREATE INDEX idx_response_participant ON participant_responses(participant_id);
CREATE INDEX idx_generation_participant ON llm_generations(participant_id);
CREATE INDEX idx_evaluation_generation ON evaluations(generation_id);
```

## 📚 Documentation Index

1. **README.md** - Quick start & overview
2. **DOCUMENTATION.md** - Complete technical documentation
3. **IMPLEMENTATION_SUMMARY.md** - Implementation checklist & status
4. **QUICK_REFERENCE.md** - This file (commands & tips)
5. **Paper.txt** - Original study protocol

## 🆘 Support Resources

- Symfony Docs: https://symfony.com/doc/current/
- Doctrine ORM: https://www.doctrine-project.org/projects/doctrine-orm/en/latest/
- Gemini API: https://ai.google.dev/docs
- Twig Templates: https://twig.symfony.com/doc/3.x/

## ✅ Pre-deployment Checklist

- [ ] Docker containers running
- [ ] Database created and seeded
- [ ] GEMINI_API_KEY configured
- [ ] Test survey completed end-to-end
- [ ] Data verified in database
- [ ] Logs checked for errors
- [ ] HTTPS configured (production)
- [ ] Backups configured
- [ ] Admin access documented
