from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Anexo(Base):
    __tablename__ = "anexos"

    id = Column(Integer, primary_key=True, index=True)
    anamnese_id = Column(Integer, ForeignKey("anamneses.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String, nullable=False)  # bancada, antes_depois
    arquivo_path = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    anamnese = relationship("Anamnese", back_populates="anexos")
