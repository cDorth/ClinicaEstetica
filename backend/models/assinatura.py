from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Assinatura(Base):
    __tablename__ = "assinaturas"

    id = Column(Integer, primary_key=True, index=True)
    anamnese_id = Column(Integer, ForeignKey("anamneses.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String, nullable=False)  # inicial, final
    imagem_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    anamnese = relationship("Anamnese", back_populates="assinaturas")
