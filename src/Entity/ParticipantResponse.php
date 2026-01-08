<?php

namespace App\Entity;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'participant_responses')]
class ParticipantResponse
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column(type: 'integer')]
    private ?int $id = null;

    #[ORM\ManyToOne(targetEntity: Participant::class, inversedBy: 'responses')]
    #[ORM\JoinColumn(nullable: false)]
    private Participant $participant;

    #[ORM\ManyToOne(targetEntity: Vignette::class)]
    #[ORM\JoinColumn(nullable: false)]
    private Vignette $vignette;

    #[ORM\Column(type: 'text')]
    private string $response;

    #[ORM\Column(type: 'integer')]
    private int $wordCount;

    #[ORM\Column(type: 'boolean')]
    private bool $validated = false;

    #[ORM\Column(type: 'text', nullable: true)]
    private ?string $validationFeedback = null;

    #[ORM\Column(type: 'datetime')]
    private \DateTimeInterface $submittedAt;

    #[ORM\Column(type: 'integer')]
    private int $responseOrder;

    public function __construct()
    {
        $this->submittedAt = new \DateTime();
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getParticipant(): Participant
    {
        return $this->participant;
    }

    public function setParticipant(Participant $participant): self
    {
        $this->participant = $participant;
        return $this;
    }

    public function getVignette(): Vignette
    {
        return $this->vignette;
    }

    public function setVignette(Vignette $vignette): self
    {
        $this->vignette = $vignette;
        return $this;
    }

    public function getResponse(): string
    {
        return $this->response;
    }

    public function setResponse(string $response): self
    {
        $this->response = $response;
        return $this;
    }

    public function getWordCount(): int
    {
        return $this->wordCount;
    }

    public function setWordCount(int $wordCount): self
    {
        $this->wordCount = $wordCount;
        return $this;
    }

    public function isValidated(): bool
    {
        return $this->validated;
    }

    public function setValidated(bool $validated): self
    {
        $this->validated = $validated;
        return $this;
    }

    public function getValidationFeedback(): ?string
    {
        return $this->validationFeedback;
    }

    public function setValidationFeedback(?string $validationFeedback): self
    {
        $this->validationFeedback = $validationFeedback;
        return $this;
    }

    public function getSubmittedAt(): \DateTimeInterface
    {
        return $this->submittedAt;
    }

    public function getResponseOrder(): int
    {
        return $this->responseOrder;
    }

    public function setResponseOrder(int $responseOrder): self
    {
        $this->responseOrder = $responseOrder;
        return $this;
    }
}
