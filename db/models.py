from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    x_handle = Column(String(15), unique=True, nullable=False, index=True)
    x_user_id = Column(String(20), unique=True)
    oauth_token = Column(Text)
    oauth_token_secret = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_analysis = Column(DateTime)
    subscription_tier = Column(String(10), default='free')
    
    # Relationships
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    peer_matches = relationship("PeerMatch", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.x_handle}>"


class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    followers_count = Column(Integer)
    following_count = Column(Integer)
    tweet_count = Column(Integer)
    niche = Column(String(50))
    content_style = Column(JSON)
    avg_engagement_rate = Column(Float)
    growth_30d = Column(Integer)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="profiles")
    
    def __repr__(self):
        return f"<UserProfile {self.user_id}>"


class PeerMatch(Base):
    __tablename__ = 'peer_matches'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    peer_handle = Column(String(15), nullable=False)
    peer_followers = Column(Integer)
    match_score = Column(Float)
    match_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="peer_matches")
    
    def __repr__(self):
        return f"<PeerMatch {self.peer_handle}>"


class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    growth_score = Column(Integer)
    insights = Column(JSON)
    comparison_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis {self.id}>"

class PeerPool(Base):
    """Shared pool of verified peer accounts"""
    __tablename__ = 'peer_pools'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    handle = Column(String(15), nullable=False, index=True)
    pool_key = Column(String(100), nullable=False, index=True)  # e.g., "tech_50000-100000"
    niche = Column(String(50), nullable=False)
    follower_count = Column(Integer)
    growth_rate = Column(Float)
    is_valid = Column(Boolean, default=True)
    last_validated = Column(DateTime, default=datetime.utcnow, index=True)
    times_used = Column(Integer, default=0)  # Track popularity
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PeerPool @{self.handle} in {self.pool_key}>"

class OAuthState(Base):
    __tablename__ = 'oauth_states'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state = Column(String(100), unique=True, nullable=False, index=True)
    code_verifier = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<OAuthState {self.state}>"


class TweetsCache(Base):
    __tablename__ = 'tweets_cache'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    x_handle = Column(String(15), nullable=False, index=True)
    tweet_data = Column(JSON)
    fetched_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<TweetsCache {self.x_handle}>"

