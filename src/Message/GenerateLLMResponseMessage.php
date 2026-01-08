<?php

namespace App\Message;

class GenerateLLMResponseMessage
{
    public function __construct(
        private int $participantId,
        private int $vignetteId,
        private array $fewShotExamples,
        private bool $isZeroShot
    ) {}

    public function getParticipantId(): int
    {
        return $this->participantId;
    }

    public function getVignetteId(): int
    {
        return $this->vignetteId;
    }

    public function getFewShotExamples(): array
    {
        return $this->fewShotExamples;
    }

    public function isZeroShot(): bool
    {
        return $this->isZeroShot;
    }
}
