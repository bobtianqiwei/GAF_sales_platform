from sqlalchemy import Column, Integer, String, Float, Text, create_engine, UniqueConstraint, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Contractor(Base):
    __tablename__ = 'contractors'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    rating = Column(Float)
    reviews = Column(Integer)
    phone = Column(String)
    city = Column(String)
    state = Column(String)
    postal_code = Column(String)
    certifications = Column(Text)  # 存JSON字符串
    type = Column(String)
    contractor_id = Column(String, unique=True)
    url = Column(String)
    insight = Column(Text)  # AI-generated sales insight
    relevance_score = Column(Integer)  # AI self-evaluation: relevance
    actionability_score = Column(Integer)  # AI self-evaluation: actionability
    accuracy_score = Column(Integer)  # AI self-evaluation: accuracy
    clarity_score = Column(Integer)  # AI self-evaluation: clarity
    evaluation_comment = Column(Text)  # AI self-evaluation: comment
    manual_evaluation_comment = Column(Text)  # Human evaluation: comment
    business_summary = Column(Text)  # AI-generated: business scale and activity
    sales_tip = Column(Text)  # AI-generated: personalized sales talking point
    risk_alert = Column(Text)  # AI-generated: risk or negative trend alert
    priority_suggestion = Column(Text)  # AI-generated: sales priority suggestion
    next_action = Column(Text)  # AI-generated: recommended next action
    latitude = Column(Float)  # Geocoded latitude
    longitude = Column(Float)  # Geocoded longitude

# 初始化数据库
engine = create_engine('sqlite:///contractors.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine) 