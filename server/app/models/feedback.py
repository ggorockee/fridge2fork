"""
피드백 관련 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Feedback(Base):
    """사용자 피드백 모델"""
    __tablename__ = "feedback"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 비회원도 가능
    type = Column(String(20), nullable=False)  # bug, feature, improvement, other
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5
    contact_email = Column(String(255), nullable=True)  # 비회원용 연락처
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 정의
    user = relationship("User", back_populates="feedback")
