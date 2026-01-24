<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

/**
 * Auto-generated Migration: Please modify to your needs!
 */
final class Version20260124045324 extends AbstractMigration
{
    public function getDescription(): string
    {
        return '';
    }

    public function up(Schema $schema): void
    {
        // this up() migration is auto-generated, please modify it to your needs
        $this->addSql('CREATE TABLE evaluations (id INT AUTO_INCREMENT NOT NULL, agreement_score INT NOT NULL, authenticity_score INT NOT NULL, presentation_order INT NOT NULL, evaluated_at DATETIME NOT NULL, participant_id INT NOT NULL, generation_id INT NOT NULL, INDEX IDX_3B72691D9D1C3019 (participant_id), INDEX IDX_3B72691D553A6EC4 (generation_id), PRIMARY KEY (id)) DEFAULT CHARACTER SET utf8mb4');
        $this->addSql('CREATE TABLE llm_generations (id INT AUTO_INCREMENT NOT NULL, simulated_response LONGTEXT NOT NULL, reasoning LONGTEXT NOT NULL, is_zero_shot TINYINT NOT NULL, temperature DOUBLE PRECISION NOT NULL, example_order JSON NOT NULL, generated_at DATETIME NOT NULL, model_version VARCHAR(100) NOT NULL, participant_id INT NOT NULL, vignette_id INT NOT NULL, INDEX IDX_B0513F169D1C3019 (participant_id), INDEX IDX_B0513F167D16298B (vignette_id), PRIMARY KEY (id)) DEFAULT CHARACTER SET utf8mb4');
        $this->addSql('CREATE TABLE participant_responses (id INT AUTO_INCREMENT NOT NULL, response LONGTEXT NOT NULL, word_count INT NOT NULL, validated TINYINT NOT NULL, validation_feedback LONGTEXT DEFAULT NULL, submitted_at DATETIME NOT NULL, response_order INT NOT NULL, participant_id INT NOT NULL, vignette_id INT NOT NULL, INDEX IDX_F25D50B09D1C3019 (participant_id), INDEX IDX_F25D50B07D16298B (vignette_id), PRIMARY KEY (id)) DEFAULT CHARACTER SET utf8mb4');
        $this->addSql('CREATE TABLE participants (id INT AUTO_INCREMENT NOT NULL, anonymous_id VARCHAR(100) NOT NULL, nationality VARCHAR(100) NOT NULL, age INT NOT NULL, gender VARCHAR(50) NOT NULL, consent_given TINYINT NOT NULL, consent_date DATETIME NOT NULL, created_at DATETIME NOT NULL, completed_at DATETIME DEFAULT NULL, current_phase VARCHAR(50) NOT NULL, phase1_vignette_ids JSON DEFAULT NULL, UNIQUE INDEX UNIQ_71697092FA93803 (anonymous_id), PRIMARY KEY (id)) DEFAULT CHARACTER SET utf8mb4');
        $this->addSql('CREATE TABLE vignettes (id INT AUTO_INCREMENT NOT NULL, content LONGTEXT NOT NULL, altruistic_response LONGTEXT NOT NULL, egoistic_response LONGTEXT NOT NULL, item_difficulty DOUBLE PRECISION NOT NULL, reality_similarity DOUBLE PRECISION NOT NULL, `set` VARCHAR(1) NOT NULL, social_proximity VARCHAR(50) NOT NULL, PRIMARY KEY (id)) DEFAULT CHARACTER SET utf8mb4');
        $this->addSql('CREATE TABLE messenger_messages (id BIGINT AUTO_INCREMENT NOT NULL, body LONGTEXT NOT NULL, headers LONGTEXT NOT NULL, queue_name VARCHAR(190) NOT NULL, created_at DATETIME NOT NULL, available_at DATETIME NOT NULL, delivered_at DATETIME DEFAULT NULL, INDEX IDX_75EA56E0FB7336F0 (queue_name), INDEX IDX_75EA56E0E3BD61CE (available_at), INDEX IDX_75EA56E016BA31DB (delivered_at), PRIMARY KEY (id)) DEFAULT CHARACTER SET utf8mb4');
        $this->addSql('ALTER TABLE evaluations ADD CONSTRAINT FK_3B72691D9D1C3019 FOREIGN KEY (participant_id) REFERENCES participants (id)');
        $this->addSql('ALTER TABLE evaluations ADD CONSTRAINT FK_3B72691D553A6EC4 FOREIGN KEY (generation_id) REFERENCES llm_generations (id)');
        $this->addSql('ALTER TABLE llm_generations ADD CONSTRAINT FK_B0513F169D1C3019 FOREIGN KEY (participant_id) REFERENCES participants (id)');
        $this->addSql('ALTER TABLE llm_generations ADD CONSTRAINT FK_B0513F167D16298B FOREIGN KEY (vignette_id) REFERENCES vignettes (id)');
        $this->addSql('ALTER TABLE participant_responses ADD CONSTRAINT FK_F25D50B09D1C3019 FOREIGN KEY (participant_id) REFERENCES participants (id)');
        $this->addSql('ALTER TABLE participant_responses ADD CONSTRAINT FK_F25D50B07D16298B FOREIGN KEY (vignette_id) REFERENCES vignettes (id)');
    }

    public function down(Schema $schema): void
    {
        // this down() migration is auto-generated, please modify it to your needs
        $this->addSql('ALTER TABLE evaluations DROP FOREIGN KEY FK_3B72691D9D1C3019');
        $this->addSql('ALTER TABLE evaluations DROP FOREIGN KEY FK_3B72691D553A6EC4');
        $this->addSql('ALTER TABLE llm_generations DROP FOREIGN KEY FK_B0513F169D1C3019');
        $this->addSql('ALTER TABLE llm_generations DROP FOREIGN KEY FK_B0513F167D16298B');
        $this->addSql('ALTER TABLE participant_responses DROP FOREIGN KEY FK_F25D50B09D1C3019');
        $this->addSql('ALTER TABLE participant_responses DROP FOREIGN KEY FK_F25D50B07D16298B');
        $this->addSql('DROP TABLE evaluations');
        $this->addSql('DROP TABLE llm_generations');
        $this->addSql('DROP TABLE participant_responses');
        $this->addSql('DROP TABLE participants');
        $this->addSql('DROP TABLE vignettes');
        $this->addSql('DROP TABLE messenger_messages');
    }
}
