<?php

namespace App\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'participants')]
class Participant
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column(type: 'integer')]
    private ?int $id = null;

    #[ORM\Column(type: 'string', length: 100, unique: true)]
    private string $anonymousId;

    #[ORM\Column(type: 'string', length: 100)]
    private string $nationality;

    #[ORM\Column(type: 'integer')]
    private int $age;

    #[ORM\Column(type: 'string', length: 50)]
    private string $gender;

    #[ORM\Column(type: 'boolean')]
    private bool $consentGiven = false;

    #[ORM\Column(type: 'datetime')]
    private \DateTimeInterface $consentDate;

    #[ORM\Column(type: 'datetime')]
    private \DateTimeInterface $createdAt;

    #[ORM\Column(type: 'datetime', nullable: true)]
    private ?\DateTimeInterface $completedAt = null;

    #[ORM\Column(type: 'string', length: 50)]
    private string $currentPhase = 'demographic';

    #[ORM\Column(type: 'json', nullable: true)]
    private ?array $phase1VignetteIds = null;

    #[ORM\OneToMany(mappedBy: 'participant', targetEntity: ParticipantResponse::class, cascade: ['persist', 'remove'])]
    private Collection $responses;

    #[ORM\OneToMany(mappedBy: 'participant', targetEntity: LLMGeneration::class, cascade: ['persist', 'remove'])]
    private Collection $generations;

    #[ORM\OneToMany(mappedBy: 'participant', targetEntity: Evaluation::class, cascade: ['persist', 'remove'])]
    private Collection $evaluations;

    public function __construct()
    {
        $this->responses = new ArrayCollection();
        $this->generations = new ArrayCollection();
        $this->evaluations = new ArrayCollection();
        $this->createdAt = new \DateTime();
    }

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getAnonymousId(): string
    {
        return $this->anonymousId;
    }

    public function setAnonymousId(string $anonymousId): self
    {
        $this->anonymousId = $anonymousId;
        return $this;
    }

    public function getNationality(): string
    {
        return $this->nationality;
    }

    public function setNationality(string $nationality): self
    {
        $this->nationality = $nationality;
        return $this;
    }

    public function getAge(): int
    {
        return $this->age;
    }

    public function setAge(int $age): self
    {
        $this->age = $age;
        return $this;
    }

    public function getGender(): string
    {
        return $this->gender;
    }

    public function setGender(string $gender): self
    {
        $this->gender = $gender;
        return $this;
    }

    public function isConsentGiven(): bool
    {
        return $this->consentGiven;
    }

    public function setConsentGiven(bool $consentGiven): self
    {
        $this->consentGiven = $consentGiven;
        return $this;
    }

    public function getConsentDate(): \DateTimeInterface
    {
        return $this->consentDate;
    }

    public function setConsentDate(\DateTimeInterface $consentDate): self
    {
        $this->consentDate = $consentDate;
        return $this;
    }

    public function getCreatedAt(): \DateTimeInterface
    {
        return $this->createdAt;
    }

    public function getCompletedAt(): ?\DateTimeInterface
    {
        return $this->completedAt;
    }

    public function setCompletedAt(?\DateTimeInterface $completedAt): self
    {
        $this->completedAt = $completedAt;
        return $this;
    }

    public function getCurrentPhase(): string
    {
        return $this->currentPhase;
    }

    public function setCurrentPhase(string $currentPhase): self
    {
        $this->currentPhase = $currentPhase;
        return $this;
    }

    public function getResponses(): Collection
    {
        return $this->responses;
    }

    public function getGenerations(): Collection
    {
        return $this->generations;
    }

    public function getEvaluations(): Collection
    {
        return $this->evaluations;
    }

    public function getPhase1VignetteIds(): ?array
    {
        return $this->phase1VignetteIds;
    }

    public function setPhase1VignetteIds(?array $phase1VignetteIds): self
    {
        $this->phase1VignetteIds = $phase1VignetteIds;
        return $this;
    }
}
