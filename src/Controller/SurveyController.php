<?php

namespace App\Controller;

use App\Entity\Participant;
use App\Entity\ParticipantResponse;
use App\Entity\Evaluation;
use App\Service\SurveyService;
use App\Service\LLMService;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\Session\SessionInterface;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\DependencyInjection\Attribute\Autowire;

#[Route('/survey')]
class SurveyController extends AbstractController
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        private SurveyService $surveyService,
        #[Autowire(service: 'App\Service\ValidationLLMService')]
        private LLMService $validationLLMService
    ) {}

    #[Route('/start', name: 'survey_start')]
    public function start(Request $request, SessionInterface $session): Response
    {
        // Try to restore session from localStorage
        $storedAnonymousId = $request->query->get('resume_id');

        if ($storedAnonymousId) {
            // Try to find existing participant
            $participant = $this->entityManager->getRepository(Participant::class)
                ->findOneBy(['anonymousId' => $storedAnonymousId]);

            if ($participant && $participant->isConsentGiven()) {
                // Restore session only if consent was given
                $session->set('participant_id', $participant->getAnonymousId());
                $session->set('participant_db_id', $participant->getId());

                // Redirect to appropriate phase
                return $this->redirectToPhaseForParticipant($participant);
            }
        }

        // Create new participant session
        $anonymousId = bin2hex(random_bytes(16));
        $session->set('participant_id', $anonymousId);

        return $this->render('survey/consent.html.twig');
    }

    #[Route('/consent', name: 'survey_consent', methods: ['POST'])]
    public function consent(Request $request, SessionInterface $session): Response
    {
        $consent = $request->request->get('consent');

        if ($consent !== 'agree') {
            return $this->redirectToRoute('home');
        }

        // Verify session has participant_id
        if (!$session->get('participant_id')) {
            return $this->redirectToRoute('survey_start');
        }

        // Set temporary flag that consent form was submitted (not circumventable)
        $session->set('consent_form_submitted', true);

        return $this->redirectToRoute('survey_demographics');
    }

    #[Route('/demographics', name: 'survey_demographics')]
    public function demographics(SessionInterface $session): Response
    {
        // Check if participant already exists in database (consent already given)
        $participant = $this->getParticipantFromSession($session);
        if ($participant && $participant->isConsentGiven()) {
            // Already consented, redirect to their current phase
            return $this->redirectToPhaseForParticipant($participant);
        }

        // For new participants, verify consent form was submitted
        if (!$session->get('consent_form_submitted')) {
            return $this->redirectToRoute('survey_start');
        }

        return $this->render('survey/demographics.html.twig');
    }

    #[Route('/demographics/submit', name: 'survey_demographics_submit', methods: ['POST'])]
    public function submitDemographics(Request $request, SessionInterface $session): Response
    {
        // Check if participant already exists with consent
        $participant = $this->getParticipantFromSession($session);
        if ($participant && $participant->isConsentGiven()) {
            // Already submitted, redirect to their current phase
            return $this->redirectToPhaseForParticipant($participant);
        }

        // Verify consent form was submitted (prevent bypass)
        if (!$session->get('consent_form_submitted')) {
            $this->addFlash('error', 'You must agree to the consent form first.');
            return $this->redirectToRoute('survey_start');
        }

        // Create new participant with consent and demographics
        $participant = new Participant();
        $participant->setAnonymousId($session->get('participant_id'));
        $participant->setNationality($request->request->get('nationality'));
        $participant->setAge((int)$request->request->get('age'));
        $participant->setGender($request->request->get('gender'));
        $participant->setConsentGiven(true);
        $participant->setConsentDate(new \DateTime());
        $participant->setCurrentPhase('phase1');

        $this->entityManager->persist($participant);
        $this->entityManager->flush();

        // Store participant DB ID and clear consent flag
        $session->set('participant_db_id', $participant->getId());
        $session->remove('consent_form_submitted');

        return $this->redirectToRoute('survey_phase1');
    }

    #[Route('/phase1', name: 'survey_phase1')]
    public function phase1(SessionInterface $session): Response
    {
        $participant = $this->getParticipantFromSession($session);
        if (!$participant || !$participant->isConsentGiven()) {
            return $this->redirectToRoute('survey_start');
        }
        $responseCount = $participant->getResponses()->count();

        if ($responseCount >= 10) {
            return $this->redirectToRoute('survey_phase1_complete');
        }

        $vignettes = $this->surveyService->selectVignettesForPhase1($participant);
        $currentVignette = $vignettes[$responseCount] ?? null;

        if (!$currentVignette) {
            return $this->redirectToRoute('survey_phase1_complete');
        }

        // Get previous rejected response if exists
        $previousResponse = $session->get('rejected_response_' . $currentVignette->getId(), '');
        $session->remove('rejected_response_' . $currentVignette->getId());

        return $this->render('survey/phase1_response.html.twig', [
            'vignette' => $currentVignette,
            'progress' => $responseCount + 1,
            'total' => 10,
            'previousResponse' => $previousResponse,
        ]);
    }

    #[Route('/phase1/submit', name: 'survey_phase1_submit', methods: ['POST'])]
    public function submitPhase1Response(Request $request, SessionInterface $session): Response
    {
        $participant = $this->getParticipantFromSession($session);
        if (!$participant || !$participant->isConsentGiven()) {
            $this->addFlash('error', 'Session expired or consent not given. Please start over.');
            return $this->redirectToRoute('survey_start');
        }

        $vignetteId = $request->request->get('vignette_id');
        $responseText = $request->request->get('response');

        $vignette = $this->entityManager->getRepository(\App\Entity\Vignette::class)->find($vignetteId);
        $wordCount = $this->surveyService->calculateWordCount($responseText);

        if ($wordCount < 50 || $wordCount > 100) {
            $this->addFlash('error', "Response must be between 50-100 words. Current: {$wordCount} words.");
            $session->set('rejected_response_' . $vignetteId, $responseText);
            // Use 303 redirect to prevent form resubmission
            return $this->redirectToRoute('survey_phase1', [], Response::HTTP_SEE_OTHER);
        }

        try {
            $validation = $this->validationLLMService->validateResponse($vignette->getContent(), $responseText);
        } catch (\Exception $e) {
            // Handle API errors gracefully
            $this->addFlash('error', 'Unable to validate your response at this time. Please try again in a moment. Error: ' . $e->getMessage());
            $session->set('rejected_response_' . $vignetteId, $responseText);
            return $this->redirectToRoute('survey_phase1', [], Response::HTTP_SEE_OTHER);
        }

        if (!$validation['is_valid']) {
            $this->addFlash('warning', $validation['feedback']);
            $session->set('rejected_response_' . $vignetteId, $responseText);
            return $this->redirectToRoute('survey_phase1', [], Response::HTTP_SEE_OTHER);
        }

        $response = new ParticipantResponse();
        $response->setParticipant($participant);
        $response->setVignette($vignette);
        $response->setResponse($responseText);
        $response->setWordCount($wordCount);
        $response->setValidated(true);
        $response->setValidationFeedback($validation['feedback']);
        $response->setResponseOrder($participant->getResponses()->count() + 1);

        $this->entityManager->persist($response);
        $this->entityManager->flush();

        return $this->redirectToRoute('survey_phase1', [], Response::HTTP_SEE_OTHER);
    }

    #[Route('/phase1/complete', name: 'survey_phase1_complete')]
    public function phase1Complete(SessionInterface $session): Response
    {
        $participant = $this->getParticipantFromSession($session);
        if (!$participant || !$participant->isConsentGiven()) {
            return $this->redirectToRoute('survey_start');
        }

        $participant->setCurrentPhase('phase2_generating');
        $this->entityManager->flush();

        try {
            $this->surveyService->generateLLMResponses($participant);
        } catch (\Exception $e) {
            // If generation fails, keep participant in phase1 and show error
            $participant->setCurrentPhase('phase1');
            $this->entityManager->flush();

            $this->addFlash('error', 'Unable to generate responses at this time. Please try again later. Error: ' . $e->getMessage());
            return $this->redirectToRoute('survey_phase1');
        }

        $participant->setCurrentPhase('phase3');
        $this->entityManager->flush();

        return $this->render('survey/phase1_complete.html.twig');
    }

    #[Route('/phase3', name: 'survey_phase3')]
    public function phase3(SessionInterface $session): Response
    {
        $participant = $this->getParticipantFromSession($session);
        if (!$participant || !$participant->isConsentGiven()) {
            return $this->redirectToRoute('survey_start');
        }

        $evaluatedCount = $participant->getEvaluations()->count();
        $totalGenerations = $participant->getGenerations()->count();

        // Check if we're still waiting for generations to be created
        // Expected: 12 generations (6 few-shot, 6 zero-shot)
        $expectedGenerations = 12;
        if ($totalGenerations < $expectedGenerations) {
            // Still generating, show waiting page
            return $this->render('survey/phase3_generating.html.twig', [
                'generated' => $totalGenerations,
                'expected' => $expectedGenerations,
            ]);
        }

        if ($evaluatedCount >= $totalGenerations) {
            return $this->redirectToRoute('survey_complete');
        }

        $generations = $this->surveyService->getRandomizedGenerationsForEvaluation($participant);

        $evaluatedGenerationIds = [];
        foreach ($participant->getEvaluations() as $evaluation) {
            $evaluatedGenerationIds[] = $evaluation->getGeneration()->getId();
        }

        $currentGeneration = null;
        foreach ($generations as $gen) {
            if (!in_array($gen->getId(), $evaluatedGenerationIds)) {
                $currentGeneration = $gen;
                break;
            }
        }

        if (!$currentGeneration) {
            return $this->redirectToRoute('survey_complete');
        }

        return $this->render('survey/phase3_evaluate.html.twig', [
            'generation' => $currentGeneration,
            'vignette' => $currentGeneration->getVignette(),
            'progress' => $evaluatedCount + 1,
            'total' => $totalGenerations,
        ]);
    }

    #[Route('/phase3/submit', name: 'survey_phase3_submit', methods: ['POST'])]
    public function submitPhase3Evaluation(Request $request, SessionInterface $session): Response
    {
        $participant = $this->getParticipantFromSession($session);
        if (!$participant || !$participant->isConsentGiven()) {
            return $this->redirectToRoute('survey_start');
        }

        $generationId = $request->request->get('generation_id');
        $agreementScore = (int)$request->request->get('agreement_score');
        $authenticityScore = (int)$request->request->get('authenticity_score');

        $generation = $this->entityManager->getRepository(\App\Entity\LLMGeneration::class)->find($generationId);

        $evaluation = new Evaluation();
        $evaluation->setParticipant($participant);
        $evaluation->setGeneration($generation);
        $evaluation->setAgreementScore($agreementScore);
        $evaluation->setAuthenticityScore($authenticityScore);
        $evaluation->setPresentationOrder($participant->getEvaluations()->count() + 1);

        $this->entityManager->persist($evaluation);
        $this->entityManager->flush();

        return $this->redirectToRoute('survey_phase3');
    }

    #[Route('/complete', name: 'survey_complete')]
    public function complete(SessionInterface $session): Response
    {
        $participant = $this->getParticipantFromSession($session);
        if (!$participant || !$participant->isConsentGiven()) {
            return $this->redirectToRoute('survey_start');
        }

        $participant->setCurrentPhase('completed');

        // Set completion timestamp if not already set
        if (!$participant->getCompletedAt()) {
            $participant->setCompletedAt(new \DateTime());
        }

        $this->entityManager->flush();

        $session->clear();

        return $this->render('survey/complete.html.twig', [
            'anonymousId' => $participant->getAnonymousId(),
        ]);
    }

    /**
     * Get participant from session and verify they exist in database
     */
    private function getParticipantFromSession(SessionInterface $session): ?Participant
    {
        $participantId = $session->get('participant_db_id');
        if (!$participantId) {
            return null;
        }

        return $this->entityManager->getRepository(Participant::class)->find($participantId);
    }

    private function redirectToPhaseForParticipant(Participant $participant): Response
    {
        $phase = $participant->getCurrentPhase();

        switch ($phase) {
            case 'demographic':
            case 'consent':
                return $this->redirectToRoute('survey_demographics');
            case 'phase1':
                return $this->redirectToRoute('survey_phase1');
            case 'phase2_generating':
            case 'phase3':
                return $this->redirectToRoute('survey_phase3');
            case 'completed':
                return $this->redirectToRoute('survey_complete');
            default:
                return $this->redirectToRoute('survey_demographics');
        }
    }
}
