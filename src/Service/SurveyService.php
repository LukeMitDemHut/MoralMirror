<?php

namespace App\Service;

use App\Entity\Participant;
use App\Entity\Vignette;
use App\Entity\LLMGeneration;
use App\Message\GenerateLLMResponseMessage;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Component\Messenger\MessageBusInterface;

class SurveyService
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        private LLMService $generationLLMService,
        private MessageBusInterface $messageBus
    ) {}

    public function selectVignettesForPhase1(?Participant $participant = null): array
    {
        // If participant has stored vignette IDs, use those
        if ($participant && $participant->getPhase1VignetteIds()) {
            $vignetteIds = $participant->getPhase1VignetteIds();
            $vignettes = $this->entityManager
                ->getRepository(Vignette::class)
                ->createQueryBuilder('v')
                ->where('v.id IN (:ids)')
                ->setParameter('ids', $vignetteIds)
                ->getQuery()
                ->getResult();

            // Sort vignettes by the stored order
            $sortedVignettes = [];
            foreach ($vignetteIds as $id) {
                foreach ($vignettes as $vignette) {
                    if ($vignette->getId() === $id) {
                        $sortedVignettes[] = $vignette;
                        break;
                    }
                }
            }
            return $sortedVignettes;
        }

        // Select and shuffle new vignettes
        $closeVignettes = $this->entityManager
            ->getRepository(Vignette::class)
            ->createQueryBuilder('v')
            ->where('v.socialProximity = :proximity')
            ->setParameter('proximity', 'close')
            ->setMaxResults(5)
            ->getQuery()
            ->getResult();

        $distantVignettes = $this->entityManager
            ->getRepository(Vignette::class)
            ->createQueryBuilder('v')
            ->where('v.socialProximity = :proximity')
            ->setParameter('proximity', 'distant')
            ->setMaxResults(5)
            ->getQuery()
            ->getResult();

        $allVignettes = array_merge($closeVignettes, $distantVignettes);
        shuffle($allVignettes);

        // Store the vignette IDs with the participant for consistency
        if ($participant) {
            $vignetteIds = array_map(fn($v) => $v->getId(), $allVignettes);
            $participant->setPhase1VignetteIds($vignetteIds);
            $this->entityManager->flush();
        }

        return $allVignettes;
    }

    public function selectVignettesForPhase2(Participant $participant): array
    {
        $usedVignetteIds = [];
        foreach ($participant->getResponses() as $response) {
            $usedVignetteIds[] = $response->getVignette()->getId();
        }

        $closeVignettes = $this->entityManager
            ->getRepository(Vignette::class)
            ->createQueryBuilder('v')
            ->where('v.socialProximity = :proximity')
            ->andWhere('v.id NOT IN (:usedIds)')
            ->setParameter('proximity', 'close')
            ->setParameter('usedIds', $usedVignetteIds)
            ->setMaxResults(6)
            ->getQuery()
            ->getResult();

        $distantVignettes = $this->entityManager
            ->getRepository(Vignette::class)
            ->createQueryBuilder('v')
            ->where('v.socialProximity = :proximity')
            ->andWhere('v.id NOT IN (:usedIds)')
            ->setParameter('proximity', 'distant')
            ->setParameter('usedIds', $usedVignetteIds)
            ->setMaxResults(6)
            ->getQuery()
            ->getResult();

        return [
            'close_few_shot' => array_slice($closeVignettes, 0, 3),
            'distant_few_shot' => array_slice($distantVignettes, 0, 3),
            'close_zero_shot' => array_slice($closeVignettes, 3, 3),
            'distant_zero_shot' => array_slice($distantVignettes, 3, 3),
        ];
    }

    public function generateLLMResponses(Participant $participant): void
    {
        $vignettes = $this->selectVignettesForPhase2($participant);

        $fewShotExamples = [];
        foreach ($participant->getResponses() as $response) {
            if ($response->isValidated()) {
                $fewShotExamples[] = [
                    'vignette' => $response->getVignette()->getContent(),
                    'response' => $response->getResponse()
                ];
            }
        }

        // Dispatch async messages for all generations
        foreach ($vignettes['close_few_shot'] as $vignette) {
            $this->messageBus->dispatch(new GenerateLLMResponseMessage(
                $participant->getId(),
                $vignette->getId(),
                $fewShotExamples,
                false
            ));
        }

        foreach ($vignettes['distant_few_shot'] as $vignette) {
            $this->messageBus->dispatch(new GenerateLLMResponseMessage(
                $participant->getId(),
                $vignette->getId(),
                $fewShotExamples,
                false
            ));
        }

        foreach ($vignettes['close_zero_shot'] as $vignette) {
            $this->messageBus->dispatch(new GenerateLLMResponseMessage(
                $participant->getId(),
                $vignette->getId(),
                [],
                true
            ));
        }

        foreach ($vignettes['distant_zero_shot'] as $vignette) {
            $this->messageBus->dispatch(new GenerateLLMResponseMessage(
                $participant->getId(),
                $vignette->getId(),
                [],
                true
            ));
        }

        // Flush is not needed since messages are dispatched to queue
    }

    public function getRandomizedGenerationsForEvaluation(Participant $participant): array
    {
        $generations = $participant->getGenerations()->toArray();
        shuffle($generations);
        return $generations;
    }

    public function calculateWordCount(string $text): int
    {
        // Match client-side logic: trim, split on whitespace, filter empty strings, count
        $trimmed = trim($text);
        if ($trimmed === '') {
            return 0;
        }
        $words = preg_split('/\s+/', $trimmed);
        $words = array_filter($words, fn($w) => strlen($w) > 0);
        return count($words);
    }
}
