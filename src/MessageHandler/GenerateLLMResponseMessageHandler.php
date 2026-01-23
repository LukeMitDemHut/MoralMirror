<?php

namespace App\MessageHandler;

use App\Entity\LLMGeneration;
use App\Entity\Participant;
use App\Entity\Vignette;
use App\Message\GenerateLLMResponseMessage;
use App\Service\LLMService;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Component\DependencyInjection\Attribute\Autowire;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler]
class GenerateLLMResponseMessageHandler
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        #[Autowire(service: 'App\Service\GenerationLLMService')]
        private LLMService $generationLLMService
    ) {}

    public function __invoke(GenerateLLMResponseMessage $message): void
    {
        $participant = $this->entityManager->getRepository(Participant::class)->find($message->getParticipantId());
        if (!$participant) {
            throw new \RuntimeException('Participant not found: ' . $message->getParticipantId());
        }

        $vignette = $this->entityManager->getRepository(Vignette::class)->find($message->getVignetteId());
        if (!$vignette) {
            throw new \RuntimeException('Vignette not found: ' . $message->getVignetteId());
        }

        $fewShotExamples = $message->getFewShotExamples();
        $isZeroShot = $message->isZeroShot();

        // Shuffle examples for few-shot
        $shuffledExamples = $fewShotExamples;
        if (!$isZeroShot) {
            shuffle($shuffledExamples);
        }

        // Call LLM API
        $result = $this->generationLLMService->generatePersonalizedResponse(
            $vignette->getContent(),
            $shuffledExamples,
            $isZeroShot
        );

        // Create and persist generation
        $generation = new LLMGeneration();
        $generation->setParticipant($participant);
        $generation->setVignette($vignette);
        $generation->setSimulatedResponse($result['simulated_response']);
        $generation->setReasoning($result['reasoning']);
        $generation->setIsZeroShot($isZeroShot);
        $generation->setTemperature(0.3);
        $generation->setModelVersion($this->generationLLMService->getModelVersion());

        if (!$isZeroShot) {
            $exampleOrder = array_map(
                fn($ex) => substr(md5($ex['vignette']), 0, 8),
                $shuffledExamples
            );
            $generation->setExampleOrder($exampleOrder);
        }

        $this->entityManager->persist($generation);
        $this->entityManager->flush();
    }
}
