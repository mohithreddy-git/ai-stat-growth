from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.language import normalize_language
from app.models import User
from app.services.documents import retrieve_chunks

GENERAL_ANSWERS = {
    "stratified sampling": {
        "en": "Stratified sampling divides a population into meaningful groups, called strata, and samples within each group. It helps ensure important subgroups are represented and can improve precision when the groups are internally similar.",
        "hi": "स्तरीकृत नमूनाकरण में जनसंख्या को महत्वपूर्ण समूहों, जिन्हें स्तर कहा जाता है, में बाँटा जाता है और प्रत्येक समूह से नमूने लिए जाते हैं। इससे महत्वपूर्ण उपसमूहों का प्रतिनिधित्व सुनिश्चित करने और सटीकता बढ़ाने में मदद मिल सकती है।",
    },
    "data quality": {
        "en": "Data quality is multi-dimensional. Common dimensions include accuracy, timeliness, coherence, relevance, accessibility, and completeness. A good quality process documents checks, findings, and corrective action.",
        "hi": "डेटा गुणवत्ता बहुआयामी होती है। इसके सामान्य आयामों में शुद्धता, समयबद्धता, सुसंगति, प्रासंगिकता, पहुँच और पूर्णता शामिल हैं। अच्छी गुणवत्ता प्रक्रिया में जाँच, निष्कर्ष और सुधारात्मक कार्रवाई दर्ज की जाती है।",
    },
    "skill gap": {
        "en": "A skill gap is the measurable difference between the competency level required for a role or activity and the current evidence-derived competency score. AI STAT-GROWTH ranks the gap with role, activity, department, and future-demand signals.",
        "hi": "कौशल अंतर किसी भूमिका या गतिविधि के लिए आवश्यक दक्षता स्तर और वर्तमान साक्ष्य-आधारित दक्षता स्कोर के बीच मापने योग्य अंतर है। AI STAT-GROWTH भूमिका, गतिविधि, विभाग और भविष्य की मांग के संकेतों से इसका क्रम तय करता है।",
    },
}


def answer(db: Session, user: User, message: str, mode: str, document_id: int | None, top_k: int, language: str = "en") -> dict:
    requested = normalize_language(language)
    lowered = message.casefold()
    if mode == "document":
        if document_id is None:
            raise HTTPException(status_code=422, detail="document_id is required in document mode")
        chunks = retrieve_chunks(db, document_id, message, top_k)
        if not chunks:
            raise HTTPException(status_code=404, detail="Insufficient evidence in the uploaded material.")
        selected = chunks[0]
        answer_text = f"Document-grounded answer: the closest source passage states: \"{selected.text}\""
        sources = [{"document_id": selected.document_id, "chunk_id": selected.chunk_id, "page_number": selected.page_number, "slide_number": selected.slide_number, "section": selected.section} for selected in chunks]
        return {"answer": answer_text, "mode": "document", "sources": sources, "provider": "mock-retrieval", "requested_language": requested, "localized": False}
    keywords = {"stratified sampling": "stratified sampling", "data quality": "data quality", "skill gap": "skill gap", "स्तरीकृत": "stratified sampling", "नमूनाकरण": "stratified sampling", "डेटा गुणवत्ता": "data quality", "कौशल अंतर": "skill gap"}
    for keyword, answer_key in keywords.items():
        if keyword in lowered:
            return {"answer": GENERAL_ANSWERS[answer_key][requested], "mode": "general", "sources": [], "provider": "mock-deterministic", "requested_language": requested, "localized": requested == "hi"}
    fallback = "मैं सांख्यिकीय अवधारणाओं, सिफारिश तर्क या संसाधन से जुड़े प्रश्नों को समझाने में सहायता कर सकता हूँ।" if requested == "hi" else "I can explain statistical concepts, recommendation logic, or answer from a processed learning document. Try asking about stratified sampling, data quality, or a specific source passage."
    return {"answer": fallback, "mode": "general", "sources": [], "provider": "mock-deterministic", "requested_language": requested, "localized": requested == "hi"}
