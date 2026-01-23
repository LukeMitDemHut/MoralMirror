"""
SQLAlchemy ORM Models for Moral LLM Assessment Database

These models mirror the PHP Doctrine entities and allow object-oriented 
access to the database from Python for data analysis.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, JSON
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


class Vignette(Base):
    """Moral vignettes presented to participants"""
    __tablename__ = 'vignettes'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    altruistic_response = Column('altruistic_response', Text, nullable=False)
    egoistic_response = Column('egoistic_response', Text, nullable=False)
    item_difficulty = Column('item_difficulty', Float, nullable=False)
    reality_similarity = Column('reality_similarity', Float, nullable=False)
    set = Column('set', String(1), nullable=False)
    social_proximity = Column('social_proximity', String(50), nullable=False)
    
    # Relationships
    responses = relationship('ParticipantResponse', back_populates='vignette')
    generations = relationship('LLMGeneration', back_populates='vignette')
    
    def __repr__(self):
        return f"<Vignette(id={self.id}, set='{self.set}', difficulty={self.item_difficulty})>"


class Participant(Base):
    """Study participants and their demographics"""
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True)
    anonymous_id = Column('anonymous_id', String(100), unique=True, nullable=False)
    nationality = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    consent_given = Column('consent_given', Boolean, default=False, nullable=False)
    consent_date = Column('consent_date', DateTime, nullable=False)
    created_at = Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column('completed_at', DateTime, nullable=True)
    current_phase = Column('current_phase', String(50), default='demographic', nullable=False)
    phase1_vignette_ids = Column('phase1_vignette_ids', JSON, nullable=True)
    
    # Relationships
    responses = relationship('ParticipantResponse', back_populates='participant', cascade='all, delete-orphan')
    generations = relationship('LLMGeneration', back_populates='participant', cascade='all, delete-orphan')
    evaluations = relationship('Evaluation', back_populates='participant', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Participant(id={self.id}, anonymous_id='{self.anonymous_id}', phase='{self.current_phase}')>"


class ParticipantResponse(Base):
    """Participant responses to vignettes in Phase 1"""
    __tablename__ = 'participant_responses'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column('participant_id', Integer, ForeignKey('participants.id'), nullable=False)
    vignette_id = Column('vignette_id', Integer, ForeignKey('vignettes.id'), nullable=False)
    response = Column(Text, nullable=False)
    word_count = Column('word_count', Integer, nullable=False)
    validated = Column(Boolean, default=False, nullable=False)
    validation_feedback = Column('validation_feedback', Text, nullable=True)
    submitted_at = Column('submitted_at', DateTime, default=datetime.utcnow, nullable=False)
    response_order = Column('response_order', Integer, nullable=False)
    
    # Relationships
    participant = relationship('Participant', back_populates='responses')
    vignette = relationship('Vignette', back_populates='responses')
    
    def __repr__(self):
        return f"<ParticipantResponse(id={self.id}, participant_id={self.participant_id}, vignette_id={self.vignette_id}, order={self.response_order})>"


class LLMGeneration(Base):
    """LLM-generated responses in Phase 2"""
    __tablename__ = 'llm_generations'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column('participant_id', Integer, ForeignKey('participants.id'), nullable=False)
    vignette_id = Column('vignette_id', Integer, ForeignKey('vignettes.id'), nullable=False)
    simulated_response = Column('simulated_response', Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    is_zero_shot = Column('is_zero_shot', Boolean, default=False, nullable=False)
    temperature = Column(Float, nullable=False)
    example_order = Column('example_order', JSON, default=list, nullable=False)
    generated_at = Column('generated_at', DateTime, default=datetime.utcnow, nullable=False)
    model_version = Column('model_version', String(100), nullable=False)
    
    # Relationships
    participant = relationship('Participant', back_populates='generations')
    vignette = relationship('Vignette', back_populates='generations')
    evaluations = relationship('Evaluation', back_populates='generation')
    
    def __repr__(self):
        shot_type = 'zero-shot' if self.is_zero_shot else 'few-shot'
        return f"<LLMGeneration(id={self.id}, participant_id={self.participant_id}, vignette_id={self.vignette_id}, type='{shot_type}')>"


class Evaluation(Base):
    """Participant evaluations of LLM generations in Phase 3"""
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column('participant_id', Integer, ForeignKey('participants.id'), nullable=False)
    generation_id = Column('generation_id', Integer, ForeignKey('llm_generations.id'), nullable=False)
    agreement_score = Column('agreement_score', Integer, nullable=False)
    authenticity_score = Column('authenticity_score', Integer, nullable=False)
    presentation_order = Column('presentation_order', Integer, nullable=False)
    evaluated_at = Column('evaluated_at', DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    participant = relationship('Participant', back_populates='evaluations')
    generation = relationship('LLMGeneration', back_populates='evaluations')
    
    def __repr__(self):
        return f"<Evaluation(id={self.id}, generation_id={self.generation_id}, agreement={self.agreement_score}, authenticity={self.authenticity_score})>"
