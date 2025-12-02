"""Job matching service"""
import re
import math
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer


def normalize(text: str) -> List[str]:
    """Normalize text for keyword extraction"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-+/#]", " ", text)
    toks = [t for t in text.split() if len(t) > 2]
    return toks


def keyword_set(text: str) -> set:
    """Extract keyword set from text"""
    return set(normalize(text))


def coverage_score(jd_text: str, resume_text: str) -> Tuple[float, List[str]]:
    """Calculate keyword coverage score between job description and resume"""
    jd_kw = keyword_set(jd_text)
    res_kw = keyword_set(resume_text)
    if not jd_kw:
        return 0.0, []
    overlap = jd_kw & res_kw
    score = len(overlap) / len(jd_kw)
    missing = list(jd_kw - res_kw)
    return score, missing


def cosine_match(jd_text: str, resume_text: str) -> float:
    """Calculate cosine similarity between job description and resume"""
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.9)
    X = vec.fit_transform([jd_text, resume_text])
    a = X[0].toarray()[0]
    b = X[1].toarray()[0]
    dot = (a * b).sum()
    denom = math.sqrt((a * a).sum()) * math.sqrt((b * b).sum())
    return 0.0 if denom == 0 else dot / denom


def compute_match(job_description: str, resume_text: str, cover_text: str = None, threshold: float = 0.70) -> dict:
    """
    Compute match score between job and candidate.
    
    Args:
        job_description: Job description text
        resume_text: Resume text
        cover_text: Optional cover letter text
        threshold: Minimum score threshold for suggestions
        
    Returns:
        Dictionary with score, coverage, cosine similarity, and tweaks
    """
    cov, missing = coverage_score(job_description, resume_text)
    cos = cosine_match(job_description, resume_text)
    # blend: put more weight on coverage for explainability
    final = 0.7 * cov + 0.3 * cos
    tweaks = []
    if final < threshold:
        top_missing = missing[:12]  # keep it digestible
        tweaks.append({
            "type": "resume",
            "message": "Consider incorporating these keywords/phrases to improve ATS match:",
            "keywords": top_missing
        })
    if cover_text:
        cov_c, missing_c = coverage_score(job_description, cover_text)
        cos_c = cosine_match(job_description, cover_text)
        final_c = 0.7 * cov_c + 0.3 * cos_c
        if final_c < threshold:
            tweaks.append({
                "type": "cover_letter",
                "message": "Suggested edits for your cover letter:",
                "keywords": missing_c[:12]
            })
    return {
        "score": round(final, 3),
        "coverage": round(cov, 3),
        "cosine": round(cos, 3),
        "tweaks": tweaks
    }
