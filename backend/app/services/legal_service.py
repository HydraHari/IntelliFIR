"""
services/legal_service.py — Verified legal documents repository, statutory cross-mappings, and semantic retrieval.

Incorporates the Bharatiya Nyaya Sanhita, 2023 (BNS), Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS),
and Bharatiya Sakshya Adhiniyam, 2023 (BSA) with historical Indian Penal Code (IPC 1860) correspondences.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.legal import LegalDocument
from app.ml.embeddings.embedding_service import embedding_service
from app.services.similar_case_service import case_vector_store
from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard statutory seed dataset for criminal law under BNS 2023 and IPC 1860
STATUTORY_PROVISIONS_SEED = [
    {
        "title": "BNS Section 303(2) / IPC Section 379 — Theft",
        "source": "Bharatiya Nyaya Sanhita, 2023 (w.e.f. 1 July 2024)",
        "provision_type": "statute",
        "version": "2023",
        "content": (
            "Whoever, intending to take dishonestly any movable property out of the possession of any person "
            "without that person's consent, moves that property in order to such taking, commits theft. "
            "Punishment: Imprisonment of either description for a term which may extend to three years, or with fine, or with both. "
            "Cognizable, Non-Bailable. Corresponding historical provision: Section 378/379 of Indian Penal Code, 1860."
        ),
        "metadata": {"ipc_counterpart": "Section 379 IPC", "bns_section": "303(2)", "cognizable": True, "bailable": False},
    },
    {
        "title": "BNS Section 304 / IPC Section 392 — Snatching and Robbery",
        "source": "Bharatiya Nyaya Sanhita, 2023",
        "provision_type": "statute",
        "version": "2023",
        "content": (
            "Theft is 'snatching' if, in order to commit theft, the offender suddenly or quickly or forcibly seizes, "
            "secures, grabs or takes away from any person or from his possession any movable property. "
            "Punishment: Imprisonment for a term which may extend to three years, and with fine. "
            "Robbery under Section 309 BNS applies where death, hurt or wrongful restraint is caused. Cognizable, Non-Bailable."
        ),
        "metadata": {"ipc_counterpart": "Section 392 IPC", "bns_section": "304", "cognizable": True, "bailable": False},
    },
    {
        "title": "BNS Section 318(4) / IPC Section 420 — Cheating and Dishonestly Inducing Delivery of Property",
        "source": "Bharatiya Nyaya Sanhita, 2023",
        "provision_type": "statute",
        "version": "2023",
        "content": (
            "Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, "
            "or to make, alter or destroy the whole or any part of a valuable security. "
            "Punishment: Imprisonment for a term which may extend to seven years, and shall also be liable to fine. "
            "Cognizable, Non-Bailable. Corresponding historical provision: Section 420 of Indian Penal Code, 1860."
        ),
        "metadata": {"ipc_counterpart": "Section 420 IPC", "bns_section": "318(4)", "cognizable": True, "bailable": False},
    },
    {
        "title": "BNS Section 115(2) / IPC Section 323 — Voluntarily Causing Hurt",
        "source": "Bharatiya Nyaya Sanhita, 2023",
        "provision_type": "statute",
        "version": "2023",
        "content": (
            "Whoever voluntarily causes hurt to any person shall be punished with imprisonment of either description "
            "for a term which may extend to one year, or with fine which may extend to ten thousand rupees, or with both. "
            "Non-cognizable, Bailable. (If caused by dangerous weapon, Section 118 BNS applies: Cognizable, Non-Bailable). "
            "Corresponding historical provision: Section 323 IPC."
        ),
        "metadata": {"ipc_counterpart": "Section 323 IPC", "bns_section": "115(2)", "cognizable": False, "bailable": True},
    },
    {
        "title": "BNS Section 329(3) / IPC Section 448 — House-Trespass",
        "source": "Bharatiya Nyaya Sanhita, 2023",
        "provision_type": "statute",
        "version": "2023",
        "content": (
            "Whoever commits criminal trespass by entering into or remaining in any building, tent or vessel used as a human dwelling "
            "or used as a place for worship, or as a place for the custody of property, is said to commit house-trespass. "
            "Punishment: Imprisonment which may extend to one year, or fine, or both. Cognizable, Bailable. "
            "Corresponding historical provision: Section 448 IPC."
        ),
        "metadata": {"ipc_counterpart": "Section 448 IPC", "bns_section": "329(3)", "cognizable": True, "bailable": True},
    },
    {
        "title": "BNSS Section 173 / CrPC Section 154 — Information in Cognizable Cases (FIR Registration)",
        "source": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "provision_type": "procedure",
        "version": "2023",
        "content": (
            "Every information relating to the commission of a cognizable offence, if given orally to an officer in charge "
            "of a police station, shall be reduced to writing by him or under his direction, and be read over to the informant; "
            "and every such information, whether given in writing or reduced to writing as aforesaid, shall be signed by the person giving it, "
            "and the substance thereof shall be entered in a book to be kept by such officer. "
            "A copy of the information as recorded shall be given forthwith, free of cost, to the informant. "
            "Section 173(3) provides for preliminary inquiry within 14 days in offences punishable between 3 and 7 years."
        ),
        "metadata": {"crpc_counterpart": "Section 154 CrPC", "bnss_section": "173", "type": "procedure"},
    },
]


def add_legal_document(
    db: Session,
    title: str,
    source: str,
    content: str,
    provision_type: str = "statute",
    version: Optional[str] = None,
    publication_date: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> LegalDocument:
    """
    Ingest a verified legal statute, section, or judicial precedent.
    Embeds content and adds to FAISS vector index with document metadata.
    """
    case_vector_store._ensure_loaded()
    vec = embedding_service.embed(f"{title}\n{content}")

    faiss_meta = {
        "title": title,
        "source": source,
        "content": content,
        "provision_type": provision_type,
        "type": "legal_doc",
    }
    pos = case_vector_store.add(vec, faiss_meta)

    doc_obj = LegalDocument(
        title=title,
        source=source,
        version=version,
        publication_date=publication_date,
        content=content,
        provision_type=provision_type,
        embedding_id=pos,
        metadata_=metadata or {},
    )
    db.add(doc_obj)
    db.commit()
    db.refresh(doc_obj)
    return doc_obj


def seed_statutory_knowledge_base(db: Session) -> int:
    """Ensure core BNS 2023 / BNSS 2023 legal statutes are seeded into the database and FAISS."""
    seeded_count = 0
    for prov in STATUTORY_PROVISIONS_SEED:
        existing = db.query(LegalDocument).filter(LegalDocument.title == prov["title"]).first()
        if not existing:
            add_legal_document(
                db=db,
                title=prov["title"],
                source=prov["source"],
                content=prov["content"],
                provision_type=prov["provision_type"],
                version=prov["version"],
                metadata=prov.get("metadata"),
            )
            seeded_count += 1
    return seeded_count


def search_legal_documents(
    db: Session,
    query: str,
    top_k: int = 5,
    threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Semantic search over verified legal documents with auto-seed fallback.
    """
    case_vector_store._ensure_loaded()
    if case_vector_store.total_vectors == 0:
        seed_statutory_knowledge_base(db)

    q_vec = embedding_service.embed(query)
    thresh = threshold if threshold is not None else 0.25
    matches = case_vector_store.search(q_vec, k=top_k, threshold=thresh)

    results = []
    for m in matches:
        if m.get("type") == "legal_doc" or "title" in m:
            results.append({
                "title": m.get("title"),
                "source": m.get("source"),
                "content": m.get("content"),
                "provision_type": m.get("provision_type", "statute"),
                "score": round(float(m.get("score", 0.0)), 4),
            })

    return results
