<?php

namespace App\Entity;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'vignettes')]
class Vignette
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column(type: 'integer')]
    private ?int $id = null;

    #[ORM\Column(type: 'text')]
    private string $content;

    #[ORM\Column(type: 'text')]
    private string $altruisticResponse;

    #[ORM\Column(type: 'text')]
    private string $egoisticResponse;

    #[ORM\Column(type: 'float')]
    private float $itemDifficulty;

    #[ORM\Column(type: 'float')]
    private float $realitySimilarity;

    #[ORM\Column(name: '`set`', type: 'string', length: 1)]
    private string $set;

    #[ORM\Column(type: 'string', length: 50)]
    private string $socialProximity;

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getContent(): string
    {
        return $this->content;
    }

    public function setContent(string $content): self
    {
        $this->content = $content;
        return $this;
    }

    public function getAltruisticResponse(): string
    {
        return $this->altruisticResponse;
    }

    public function setAltruisticResponse(string $altruisticResponse): self
    {
        $this->altruisticResponse = $altruisticResponse;
        return $this;
    }

    public function getEgoisticResponse(): string
    {
        return $this->egoisticResponse;
    }

    public function setEgoisticResponse(string $egoisticResponse): self
    {
        $this->egoisticResponse = $egoisticResponse;
        return $this;
    }

    public function getItemDifficulty(): float
    {
        return $this->itemDifficulty;
    }

    public function setItemDifficulty(float $itemDifficulty): self
    {
        $this->itemDifficulty = $itemDifficulty;
        return $this;
    }

    public function getRealitySimilarity(): float
    {
        return $this->realitySimilarity;
    }

    public function setRealitySimilarity(float $realitySimilarity): self
    {
        $this->realitySimilarity = $realitySimilarity;
        return $this;
    }

    public function getSet(): string
    {
        return $this->set;
    }

    public function setSet(string $set): self
    {
        $this->set = $set;
        return $this;
    }

    public function getSocialProximity(): string
    {
        return $this->socialProximity;
    }

    public function setSocialProximity(string $socialProximity): self
    {
        $this->socialProximity = $socialProximity;
        return $this;
    }
}
