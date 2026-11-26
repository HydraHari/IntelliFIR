"""
core/demo_data.py — Seed fictional demo complaints, legal provisions, and cases.
ALL DATA IS STRICTLY FICTIONAL AND CREATED FOR PROTOTYPE DEMONSTRATION ONLY.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
import uuid

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.complaint import Complaint, ComplaintStatus
from app.models.legal import SimilarCase, LegalDocument
from app.services.extraction_service import process_complaint_pipeline
from app.services.draft_service import generate_fir_draft
from app.services.validation_service import validate_fir_draft
from app.services.similar_case_service import ingest_case
from app.services.legal_service import add_legal_document

logger = logging.getLogger(__name__)

FICTIONAL_COMPLAINTS = [
    {
        "title": "Robbery of Mobile Phone and Wallet at Connaught Place",
        "reference_id": "DEMO-CASE-001",
        "raw_text": (
            "I, Rajesh Kumar, son of Mohan Kumar, resident of 14B Green Park, New Delhi, "
            "hereby report that on 12/10/2026 at around 8:30 PM, I was walking near the Inner Circle, "
            "Connaught Place, opposite Regal Building. Two unidentified men riding a black motorcycle "
            "with no visible registration plate intercepted me. The pillion rider brandished a knife "
            "and snatched my Apple iPhone 14 and leather wallet containing Rs. 4,500 in cash and my Driving License. "
            "A nearby street tea-vendor named Suresh saw the incident occur. The perpetrators fled towards Barakhamba Road. "
            "CCTV cameras installed outside the nearby bank may have captured the escape route. "
            "I request the police to register my complaint and recover my stolen belongings."
        ),
        "incident_date": date(2026, 10, 12),
        "incident_location": "Inner Circle, Connaught Place, New Delhi",
    },
    {
        "title": "Online Banking Fraud and Unauthorized Account Debit",
        "reference_id": "DEMO-CASE-002",
        "raw_text": (
            "My name is Priya Sharma, residing at Sector 18, Noida. On 28/09/2026 at approximately 3:15 PM, "
            "I received a telephone call from a person claiming to be a customer care representative of ABC Bank. "
            "The caller stated that my KYC verification was overdue and sent a link via SMS from sender VK-ABCBANK. "
            "Upon clicking the link and entering details, Rs. 75,000 was debited in two transactions to an unknown account. "
            "I have preserved the call recording, SMS header, and bank transaction statement as electronic evidence. "
            "I suspect that the caller belongs to an organized cyber fraud syndicate operating from Jharkhand."
        ),
        "incident_date": date(2026, 9, 28),
        "incident_location": "Online / Sector 18, Noida",
    },
    {
        "title": "House Trespass and Theft of Gold Jewelry in Apartment",
        "reference_id": "DEMO-CASE-003",
        "raw_text": (
            "To the Station House Officer. I, Vikram Adani, resident of Flat 402, Shanti Heights, Indirapuram, "
            "wish to report a burglary at my flat. Sometime between 10:00 AM and 6:00 PM on 03/11/2026, when my family was away at work, "
            "unknown person or persons entered by breaking the main door wooden latch. They stole approximately 50 grams "
            "of gold ornaments worth Rs. 3,50,000 from the bedroom almirah. The building security guard Ramesh stated he noticed "
            "two men in delivery uniforms around 2:00 PM. I request an urgent investigation."
        ),
        "incident_date": date(2026, 11, 3),
        "incident_location": "Flat 402, Shanti Heights, Indirapuram",
    },
]

FICTIONAL_LEGAL_DOCUMENTS = [
    {
        "title": "Bharatiya Nyaya Sanhita (BNS) — Section 303 (Theft)",
        "source": "Bharatiya Nyaya Sanhita, 2023",
        "content": (
            "Section 303: Theft.—(1) Whoever, intending to take dishonestly any movable property out of the possession of any person "
            "without that person's consent, moves that property in order to such taking, is said to commit theft. "
            "Punishment: Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to three years, "
            "or with fine, or with both."
        ),
        "provision_type": "penal_code",
    },
    {
        "title": "Bharatiya Nyaya Sanhita (BNS) — Section 309 (Robbery)",
        "source": "Bharatiya Nyaya Sanhita, 2023",
        "content": (
            "Section 309: Robbery.—In all robbery there is either theft or extortion. Theft is robbery if, in order to the committing of the theft, "
            "or in committing the theft, or in carrying away or attempting to carry away property obtained by the theft, the offender, for that end, "
            "voluntarily causes or attempts to cause to any person death or hurt or wrongful restraint, or fear of instant death or of instant hurt, "
            "or of instant wrongful restraint."
        ),
        "provision_type": "penal_code",
    },
    {
        "title": "Information Technology Act, 2000 — Section 66D (Cheating by Personation using Computer)",
        "source": "Information Technology Act, 2000",
        "content": (
            "Section 66D: Punishment for cheating by personation by using computer resource.—Whoever, by means of any communication device "
            "or computer resource cheats by personating, shall be punished with imprisonment of either description for a term which may extend to three years "
            "and shall also be liable to fine which may extend to one lakh rupees."
        ),
        "provision_type": "cyber_law",
    },
]


def seed_demo_data() -> None:
    """Create default users and seed realistic fictional demo cases and legal texts."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Create default admin and reviewer accounts
        admin_email = "admin@intellifir.local"
        reviewer_email = "reviewer@intellifir.local"
        investigator_email = "investigator@intellifir.local"

        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("admin12345"),
                full_name="Admin Officer",
                role=UserRole.administrator,
                is_active=True,
            )
            db.add(admin)

        reviewer = db.query(User).filter(User.email == reviewer_email).first()
        if not reviewer:
            reviewer = User(
                email=reviewer_email,
                hashed_password=hash_password("reviewer12345"),
                full_name="Authorized Reviewer Sharma",
                role=UserRole.reviewer,
                is_active=True,
            )
            db.add(reviewer)

        investigator = db.query(User).filter(User.email == investigator_email).first()
        if not investigator:
            investigator = User(
                email=investigator_email,
                hashed_password=hash_password("investigator12345"),
                full_name="Investigator Verma",
                role=UserRole.investigator,
                is_active=True,
            )
            db.add(investigator)

        db.commit()
        db.refresh(admin)

        # 2. Ingest verified legal documents
        for doc in FICTIONAL_LEGAL_DOCUMENTS:
            existing_doc = db.query(LegalDocument).filter(LegalDocument.title == doc["title"]).first()
            if not existing_doc:
                try:
                    add_legal_document(
                        db=db,
                        title=doc["title"],
                        source=doc["source"],
                        content=doc["content"],
                        provision_type=doc["provision_type"],
                    )
                except Exception as exc:
                    logger.warning("Could not index legal doc into FAISS: %s", exc)

        # 3. Ingest demo complaints and execute pipeline
        for c_data in FICTIONAL_COMPLAINTS:
            existing_c = db.query(Complaint).filter(Complaint.reference_id == c_data["reference_id"]).first()
            if not existing_c:
                c = Complaint(
                    reference_id=c_data["reference_id"],
                    title=c_data["title"],
                    raw_text=c_data["raw_text"],
                    extracted_text=c_data["raw_text"],
                    language="en",
                    incident_date=c_data["incident_date"],
                    incident_location=c_data["incident_location"],
                    status=ComplaintStatus.uploaded,
                    submitted_by_id=admin.id,
                )
                db.add(c)
                db.commit()
                db.refresh(c)

                # Process extraction, draft, and validation
                try:
                    process_complaint_pipeline(db, c)
                    draft = generate_fir_draft(db, c, user_id=admin.id, method="template")
                    validate_fir_draft(db, draft)
                    # Also ingest into similar cases
                    ingest_case(
                        db=db,
                        reference_id=c.reference_id,
                        summary=f"{c.title}: {c.raw_text[:200]}",
                        category="Criminal Complaint",
                    )
                except Exception as exc:
                    logger.warning("Error running demo pipeline on %s: %s", c.reference_id, exc)

        logger.info("Demo data seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_demo_data()
