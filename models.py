from sqlalchemy import (
    Float, create_engine, Column, Integer, String, Boolean, Date, ForeignKey, Text, DECIMAL, CheckConstraint, Index, BigInteger, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

# Base class for all models
Base = declarative_base()

class Address(Base):
    __tablename__ = 'address'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    number = Column(Integer, nullable=False)
    street = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    postcode = Column(String(20), nullable=False)  # Updated length
    country = Column(String(100), nullable=False)  # Updated length

    companies = relationship("Company", back_populates="address", cascade="all, delete-orphan")
    directors = relationship("Director", back_populates="address", cascade="all, delete-orphan")
    vats = relationship("VAT", back_populates="address", cascade="all, delete-orphan")

class Company(Base):
    __tablename__ = 'company'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    house_number = Column(String(10), nullable=False)  # Updated length
    name = Column(String(255), nullable=False)
    nature = Column(String(255), nullable=False)
    pay_reference_number = Column(String(50), nullable=False)  # Updated length
    account_office_number = Column(String(50), nullable=False)  # Updated length
    cis = Column(Boolean, nullable=False)
    vat = Column(Boolean, nullable=False)
    email = Column(String(255), nullable=False, unique=True)  # Added unique constraint
    address_id = Column(BigInteger, ForeignKey('address.id'), nullable=False)
    contact_number = Column(String(50), nullable=False)  # Updated length
    government_gateway_id = Column(String(50), nullable=False)  # Updated length
    date_added = Column(Date, nullable=False)
    files_count = Column(Integer, default=0)

    address = relationship("Address", back_populates="companies")
    accounts = relationship("Account", back_populates="company", uselist=False,cascade="all, delete-orphan")
    confirmation_statements = relationship("ConfirmationStatement", uselist=False, back_populates="company", cascade="all, delete-orphan")
    cis_details = relationship("CIS", back_populates="company", uselist=False, cascade="all, delete-orphan")
    vats = relationship("VAT", back_populates="company", uselist=False, cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="company")
    files = relationship("Files", back_populates="company", cascade="all, delete-orphan")
    employers = relationship("Employer", back_populates="company", cascade="all, delete-orphan")
    payrun = relationship("PayRun", back_populates="company", uselist=False, cascade="all, delete-orphan")
    directors = relationship("Director", back_populates="company", cascade="all, delete-orphan")

class Director(Base):
    __tablename__ = 'director'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('company.id'), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    insurance_number = Column(String(30), nullable=False)  # Updated length
    address_id = Column(BigInteger, ForeignKey('address.id'), nullable=False)
    phone = Column(String(20), nullable=False)  # Updated length
    email = Column(String(255), nullable=False)

    company = relationship("Company", back_populates="directors")
    address = relationship("Address", back_populates="directors")

    __table_args__ = (
        Index('idx_director_company_id', 'company_id'),  # Updated index name for clarity
        Index('idx_director_address_id', 'address_id'),  # Updated index name for clarity
    )

class Employer(Base):
    __tablename__ = 'employer'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    company_id = Column(BigInteger, ForeignKey('company.id'), nullable=False, unique=True)
    utr = Column(String(15))  # Changed to String to match UTR format
    nino = Column(String(15))
    start_date = Column(Date, nullable=False)

    company = relationship("Company", back_populates="employers")

    __table_args__ = (
        Index('idx_employer_company_id', 'company_id'),  # Updated index name for clarity
    )

class PayRun(Base):
    __tablename__ = 'payrun'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    company_id = Column(BigInteger, ForeignKey('company.id'), nullable=False, unique=True)
    date = Column(Date, nullable=False)
    status = Column(Enum('Early', 'Soon', 'Urgent', 'Overdue'), nullable=False)  # Changed to Enum
    month_check = Column(Boolean, nullable=False)
    pay_run = Column(Boolean, nullable=False)
    p60 = Column(Boolean, nullable=False)
    files_count = Column(Integer, default=0)

    company = relationship("Company", back_populates="payrun")

class Account(Base):
    __tablename__ = 'account'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('company.id'), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum('Early', 'Soon', 'Urgent', 'Overdue'), nullable=False)  # Changed to Enum
    email_check = Column(Boolean, nullable=False, default=False)
    invoice_check = Column(Boolean, nullable=False, default=False)
    done_check = Column(Boolean, nullable=False, default=False)
    files_count = Column(Integer, default=0)

    company = relationship("Company", back_populates="accounts")

class ConfirmationStatement(Base):
    __tablename__ = 'confirmation_statement'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('company.id'), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum('Early', 'Soon', 'Urgent', 'Overdue'), nullable=False)  # Changed to Enum
    invoice_check = Column(Boolean, nullable=False)
    done_check = Column(Boolean, nullable=False)

    company = relationship("Company", back_populates="confirmation_statements")

class CIS(Base):
    __tablename__ = 'cis'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('company.id'), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    employees_reference = Column(String(255), nullable=False)
    last_month = Column(Date, nullable=False)
    next_month = Column(Date, nullable=False)
    status = Column(Enum('Early', 'Soon', 'Urgent', 'Overdue'), nullable=False)  # Changed to Enum
    email_check = Column(Boolean, nullable=False, default=False)
    month_check = Column(Boolean, nullable=False, default=False)

    company = relationship("Company", back_populates="cis_details")

class VAT(Base):
    __tablename__ = 'vat'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    number = Column(String(9), nullable=False)
    registration_date = Column(Date)
    address_id = Column(BigInteger, ForeignKey('address.id'), nullable=False)
    company_number = Column(String(8))
    company_name = Column(String(255), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    due_date = Column(Date)
    calculations = Column(Text)
    files_count = Column(Integer, default=0)
    done = Column(Boolean, default=False)
    company_id = Column(BigInteger, ForeignKey('company.id'))
    status = Column(Enum('Early', 'Soon', 'Urgent', 'Overdue'), nullable=False, unique=True)  # Changed to Enum

    address = relationship("Address", back_populates="vats")
    company = relationship("Company", back_populates="vats")

    __table_args__ = (
        Index('idx_vat_address_id', 'address_id'),  # Updated index name for clarity
    )

class Invoice(Base):
    __tablename__ = 'invoice'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255))
    type = Column(Enum('company', 'individual'), nullable=False)  # Changed to Enum
    service_description = Column(Text)
    date = Column(Date)
    amount = Column(DECIMAL(10, 2))
    sent = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    company_id = Column(BigInteger, ForeignKey('company.id'))

    company = relationship("Company", back_populates="invoices")

class Task(Base):
    __tablename__ = 'task'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_name = Column(String(50), nullable=False)
    done_by = Column(Enum('aleks', 'krista', 'ledia', 'denalda', 'kujtim', 'other', name="done_by_enum"), nullable=False)
    status = Column(Enum('not_started', 'in_process', 'details_missing', 'done', 'paid', name="task_status_enum"), nullable=False)
    task_type = Column(String(100), nullable=True)  
    date_added = Column(Date, nullable=True)
    date_finished = Column(Date, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    invoice_sent = Column(Boolean, default=False)
    invoice_paid = Column(Boolean, default=False)
    office = Column(Enum('london', 'leeds', name="task_office_enum"), nullable=False)
    files_count = Column(Integer, default=0)

class Files(Base):
    __tablename__ = 'files'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('company.id'), nullable=True)
    second_id = Column(Enum('Vat', 'Account', 'Company', 'Payrun','Task'), nullable=False)  # Changed to Enum
    path = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)  # Add this line

    company = relationship("Company", back_populates="files")



class DataInsights(Base):
    __tablename__ = 'data_insights'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(Enum('CIS', 'VAT', 'Account', 'PayRun', 'ConfirmationStatement','Invoice', 'Task', name="category_enum"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    # Count of tasks for each status
    early_count = Column(Integer, nullable=True)
    soon_count = Column(Integer, nullable=True)
    urgent_count = Column(Integer, nullable=True)
    overdue_count = Column(Integer, nullable=True)
    paid_count = Column(Integer, nullable=True)  # If applicable

    total_count = Column(Integer, nullable=False)  # Total tasks considered for this category, month, year
