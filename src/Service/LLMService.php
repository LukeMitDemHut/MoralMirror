<?php

namespace App\Service;

use Symfony\Contracts\HttpClient\HttpClientInterface;

class LLMService
{
    public function __construct(
        private HttpClientInterface $httpClient,
        private string $apiKey,
        private string $apiEndpoint,
        private string $model
    ) {}

    public function validateResponse(string $vignette, string $response): array
    {
        $prompt = $this->buildValidationPrompt($vignette, $response);
        $schema = $this->getValidationSchema();

        $result = $this->callLLMAPI($prompt, 0.1, $schema);

        return $result;
    }

    public function generatePersonalizedResponse(
        string $targetVignette,
        array $fewShotExamples,
        bool $isZeroShot = false
    ): array {
        $prompt = $this->buildGenerationPrompt($targetVignette, $fewShotExamples, $isZeroShot);
        $schema = $this->getGenerationSchema();

        $result = $this->callLLMAPI($prompt, 0.3, $schema);

        return $result;
    }

    private function buildValidationPrompt(string $vignette, string $response): string
    {
        return <<<PROMPT
You are an LLM judge evaluating whether a participant's response to a moral vignette is a genuine attempt at answering.

**Vignette:**
{$vignette}

**Participant's Response:**
{$response}

**Task:**
Evaluate whether this response represents a GENUINE ATTEMPT at moral reasoning with a clear decision.

**Accept responses that:**
- Make a clear decision or commitment about what they would do
- Provide ANY specific reason or justification for their decision (even if self-interested, controversial, or morally questionable)
- Explain their thinking, values, or priorities that led to the decision
- Show they understood the scenario and committed to a course of action

**REJECT responses that:**
- Don't commit to a clear decision (e.g., just listing options without choosing, excessive hedging like multiple "I don't know" statements)
- Are vague non-answers like "I don't know", "I don't care", "because it is what it is", "maybe", "it depends" without further reasoning
- Are complete nonsense or random text
- Just restate the question without any reasoning or decision
- Are obvious attempts to bypass the task (e.g., "this is a test response")
- Are in another language other than English

IMPORTANT: Accept ALL types of moral reasoning including self-interested, pragmatic, emotional, or unconventional perspectives. However, the participant MUST make a clear decision and justify it. Indecisiveness without commitment (e.g., "I would do X but also maybe Y, I don't know") should be rejected.

If the response is a genuine attempt with a clear decision, set is_valid to true with brief encouraging feedback.
If it lacks a clear decision or reasoning, set is_valid to false with specific guidance asking them to commit to a decision and explain their reasoning.
PROMPT;
    }

    private function getValidationSchema(): array
    {
        return [
            'type' => 'json_schema',
            'json_schema' => [
                'name' => 'validation_response',
                'strict' => true,
                'schema' => [
                    'type' => 'object',
                    'properties' => [
                        'is_valid' => [
                            'type' => 'boolean',
                            'description' => 'Whether the response meets all validation criteria'
                        ],
                        'feedback' => [
                            'type' => 'string',
                            'description' => 'Encouraging feedback if valid, or specific improvement suggestions if not'
                        ]
                    ],
                    'required' => ['is_valid', 'feedback'],
                    'additionalProperties' => false
                ]
            ]
        ];
    }

    private function getGenerationSchema(): array
    {
        return [
            'type' => 'json_schema',
            'json_schema' => [
                'name' => 'generation_response',
                'strict' => true,
                'schema' => [
                    'type' => 'object',
                    'properties' => [
                        'simulated_response' => [
                            'type' => 'string',
                            'description' => 'The personalized moral reasoning response (50-100 words)'
                        ],
                        'reasoning' => [
                            'type' => 'string',
                            'description' => 'Brief explanation of the inferred pattern from examples'
                        ]
                    ],
                    'required' => ['simulated_response', 'reasoning'],
                    'additionalProperties' => false
                ]
            ]
        ];
    }

    private function buildGenerationPrompt(
        string $targetVignette,
        array $fewShotExamples,
        bool $isZeroShot
    ): string {
        // System message
        $systemMessage = <<<SYSTEM
You are an AI system tasked with simulating the moral reasoning of a specific individual.

Your goal is to produce outputs that reflect how this individual would respond in everyday moral situations, with high fidelity to both their decision-making patterns and reasoning style. Do not optimize for correctness, neutrality, or social desirability.

You must:
- Infer recurring value priorities, moral thresholds, and trade-offs from the examples
- Infer the individual's characteristic reasoning structure (e.g., intuitive vs. reflective) and emotional tone
- Infer typical balances between self-interest and concern for others with close as well as distant individuals
- Commit to a single decision consistent with the inferred personal moral pattern
- Justify that decision in the individual's voice, reflecting reasoning patterns, priorities, emotional framing, and typical language use
- Prioritize matching the individual's reasoning style and voice over producing a generally correct or defensible decision
- Allow natural variation in tone and emphasis while maintaining internal consistency

You must not:
- Reference ethical theories, moral frameworks, or philosophical concepts by name
- Optimize for consensus morality or social desirability
- Generalize to what most people would do or think
- Explain multiple possible options or weigh alternatives explicitly
- Introduce moral concepts or values not clearly implied by the examples
- Correct, improve, or moralize beyond the individual's apparent values
- Infer or label personality traits, psychological categories, or moral types
- Copy phrases, sentence structures, or distinctive wording from the examples
- Mention that you are an AI, a model, or that you are simulating
- Refer to the examples explicitly or describe how you inferred the pattern
- Reveal intermediate reasoning or analysis steps
SYSTEM;

        $examplesSection = '';

        if (!$isZeroShot && !empty($fewShotExamples)) {
            $examplesSection = "\n**Few-Shot Examples:**\nThe following are examples of how this individual has responded to moral situations involving close and distant individuals:\n\n";
            foreach ($fewShotExamples as $idx => $example) {
                $num = $idx + 1;
                $examplesSection .= "Example {$num}:\n";
                $examplesSection .= "Situation: {$example['vignette']}\n";
                $examplesSection .= "Response: {$example['response']}\n\n";
            }
        }

        return <<<PROMPT
{$systemMessage}
{$examplesSection}
**Target Situation:**
{$targetVignette}

**Task:**
Generate a response that mirrors the individual's moral reasoning. Write a single, open-ended justification in their voice. Do not provide explanations, meta-commentary, or commentary about the examples.

**Output Requirements:**
- Response length: approximately 50–100 words
- Tone and style should match the individual's prior responses
- First-person perspective unless the examples clearly use another style
- No headings, bullet points, or meta-commentary
- Fidelity to the individual's reasoning patterns is prioritized over correctness or balance

You must respond ONLY with valid JSON in this exact format:
{"simulated_response": "your 50-100 word response here", "reasoning": "brief explanation of the pattern you inferred"}
PROMPT;
    }

    private function callLLMAPI(string $prompt, float $temperature, ?array $responseFormat = null): array
    {
        $messages = [
            ['role' => 'user', 'content' => $prompt]
        ];

        $requestBody = [
            'model' => $this->model,
            'messages' => $messages,
            'temperature' => $temperature,
        ];

        if ($responseFormat !== null) {
            $requestBody['response_format'] = $responseFormat;
        }

        $maxRetries = 3;
        $retryDelay = 2; // Initial delay in seconds

        for ($attempt = 0; $attempt <= $maxRetries; $attempt++) {
            try {
                $response = $this->httpClient->request('POST', $this->apiEndpoint, [
                    'json' => $requestBody,
                    'headers' => [
                        'Content-Type' => 'application/json',
                        'Authorization' => 'Bearer ' . $this->apiKey,
                        'HTTP-Referer' => 'https://moral-reasoning-study.research',
                        'X-Title' => 'Moral Reasoning Research Study',
                    ]
                ]);

                $data = $response->toArray();
                break; // Success, exit retry loop
            } catch (\Symfony\Component\HttpClient\Exception\ClientException $e) {
                // Check if it's a 429 rate limit error
                if ($e->getResponse()->getStatusCode() === 429) {
                    if ($attempt < $maxRetries) {
                        // Wait with exponential backoff before retrying
                        $waitTime = $retryDelay * pow(2, $attempt);
                        sleep($waitTime);
                        continue;
                    }
                    // Out of retries
                    throw new \Exception('Rate limit exceeded. Please wait a moment and try again. If this persists, you may need to upgrade your OpenRouter API plan.');
                }
                // Other client errors, rethrow
                throw $e;
            }
        }

        if (!isset($data)) {
            throw new \Exception('Failed to get response from API after retries');
        }

        if (isset($data['choices'][0]['message']['content'])) {
            $textResponse = $data['choices'][0]['message']['content'];

            // Clean up markdown code blocks if present
            $textResponse = trim($textResponse);
            if (str_starts_with($textResponse, '```json')) {
                $textResponse = preg_replace('/^```json\s*/', '', $textResponse);
                $textResponse = preg_replace('/\s*```$/', '', $textResponse);
            } elseif (str_starts_with($textResponse, '```')) {
                $textResponse = preg_replace('/^```\s*/', '', $textResponse);
                $textResponse = preg_replace('/\s*```$/', '', $textResponse);
            }

            $decoded = json_decode($textResponse, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new \Exception('Failed to parse JSON response: ' . json_last_error_msg() . ' - Response: ' . substr($textResponse, 0, 200));
            }

            return $decoded;
        }

        throw new \Exception('Invalid response from LLM API: ' . json_encode($data));
    }

    public function getModelVersion(): string
    {
        return $this->model;
    }
}
