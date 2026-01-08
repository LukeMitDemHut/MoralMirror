<?php

namespace App\Entity;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'llm_generations')]
class LLMGeneration
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column(type: 'integer')]
    private ?int $id = null;

    #[ORM\ManyToOne(targetEntity: Participant::class, inversedBy: 'generations')]
    #[ORM\JoinColumn(nullable: false)]
    private Participant $participant;

    #[ORM\ManyToOne(targetEntity: Vignette::class)]
    #[ORM\JoinColumn(nullable: false)]
    private Vignette $vignette;

    #[ORM\Column(type: 'text')]
    private string $simulatedResponse;

    #[ORM\Column(type: 'text')]
    private string $reasoning;

    #[ORM\Column(type: 'boolean')]
    private bool $isZeroShot = false;

    #[ORM\Column(type: 'float')]
    private float $temperature;

    #[ORM\Column(type: 'json')]
    private array $exampleOrder = [];

    #[ORM\Column(type: 'datetime')]
    private \DateTimeInterface $generatedAt;

    #[ORM\Column(type: 'string', length: 100)]
    private string $modelVersion;

    public function __construct()
    {
        $this->generatedAt = new \DateTime();
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

    public function getSimulatedResponse(): string
    {
        return $this->simulatedResponse;
    }

    public function setSimulatedResponse(string $simulatedResponse): self
    {
        $this->simulatedResponse = $simulatedResponse;
        return $this;
    }

    public function getReasoning(): string
    {
        return $this->reasoning;
    }

    public function setReasoning(string $reasoning): self
    {
        $this->reasoning = $reasoning;
        return $this;
    }

    public function isZeroShot(): bool
    {
        return $this->isZeroShot;
    }

    public function setIsZeroShot(bool $isZeroShot): self
    {
        $this->isZeroShot = $isZeroShot;
        return $this;
    }

    public function getTemperature(): float
    {
        return $this->temperature;
    }

    public function setTemperature(float $temperature): self
    {
        $this->temperature = $temperature;
        return $this;
    }

    public function getExampleOrder(): array
    {
        return $this->exampleOrder;
    }

    public function setExampleOrder(array $exampleOrder): self
    {
        $this->exampleOrder = $exampleOrder;
        return $this;
    }

    public function getGeneratedAt(): \DateTimeInterface
    {
        return $this->generatedAt;
    }

    public function getModelVersion(): string
    {
        return $this->modelVersion;
    }

    public function setModelVersion(string $modelVersion): self
    {
        $this->modelVersion = $modelVersion;
        return $this;
    }
}
