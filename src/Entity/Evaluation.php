<?php

namespace App\Entity;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'evaluations')]
class Evaluation
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column(type: 'integer')]
    private ?int $id = null;

    #[ORM\ManyToOne(targetEntity: Participant::class, inversedBy: 'evaluations')]
    #[ORM\JoinColumn(nullable: false)]
    private Participant $participant;

    #[ORM\ManyToOne(targetEntity: LLMGeneration::class)]
    #[ORM\JoinColumn(nullable: false)]
    private LLMGeneration $generation;

    #[ORM\Column(type: 'integer')]
    private int $agreementScore;

    #[ORM\Column(type: 'integer')]
    private int $authenticityScore;

    #[ORM\Column(type: 'integer')]
    private int $presentationOrder;

    #[ORM\Column(type: 'datetime')]
    private \DateTimeInterface $evaluatedAt;

    public function __construct()
    {
        $this->evaluatedAt = new \DateTime();
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

    public function getGeneration(): LLMGeneration
    {
        return $this->generation;
    }

    public function setGeneration(LLMGeneration $generation): self
    {
        $this->generation = $generation;
        return $this;
    }

    public function getAgreementScore(): int
    {
        return $this->agreementScore;
    }

    public function setAgreementScore(int $agreementScore): self
    {
        $this->agreementScore = $agreementScore;
        return $this;
    }

    public function getAuthenticityScore(): int
    {
        return $this->authenticityScore;
    }

    public function setAuthenticityScore(int $authenticityScore): self
    {
        $this->authenticityScore = $authenticityScore;
        return $this;
    }

    public function getPresentationOrder(): int
    {
        return $this->presentationOrder;
    }

    public function setPresentationOrder(int $presentationOrder): self
    {
        $this->presentationOrder = $presentationOrder;
        return $this;
    }

    public function getEvaluatedAt(): \DateTimeInterface
    {
        return $this->evaluatedAt;
    }
}
