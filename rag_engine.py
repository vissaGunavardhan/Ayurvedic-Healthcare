import json
import math
import logging
from pathlib import Path
from config import BASE_DIR
from gemini_service import GeminiService
from database import get_all_doctor_contributions

logger = logging.getLogger(__name__)

CACHE_FILE = BASE_DIR / 'data' / 'embeddings_cache.json'
STATIC_DATA_FILE = BASE_DIR / 'data' / 'ayurveda_knowledge.json'

def cosine_similarity(v1, v2):
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a, b in zip(v1, v2))) # norm1
    norm2 = math.sqrt(sum(b * b for b in v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class RAGEngine:
    def __init__(self):
        self.static_knowledge = []
        self.embeddings_cache = {}
        self.load_static_knowledge()
        self.load_cache()

    def load_static_knowledge(self):
        if STATIC_DATA_FILE.exists():
            try:
                with open(STATIC_DATA_FILE, 'r', encoding='utf-8') as f:
                    self.static_knowledge = json.load(f)
            except Exception as e:
                logger.error(f"Error loading static knowledge: {e}")
                self.static_knowledge = []

    def load_cache(self):
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.embeddings_cache = json.load(f)
            except Exception:
                self.embeddings_cache = {}

    def save_cache(self):
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.embeddings_cache, f)
        except Exception as e:
            logger.error(f"Error saving embeddings cache: {e}")

    def document_to_text(self, doc):
        """Construct dense semantic text representation of an Ayurvedic remedy"""
        parts = [
            f"Condition: {doc.get('condition_name', '')}",
            f"Ayurvedic: {doc.get('ayurvedic_name', '')}",
            f"Dosha: {doc.get('dosha_involved', doc.get('dosha_type', ''))}",
            f"Symptoms: {' '.join(doc.get('common_symptoms', [])) if isinstance(doc.get('common_symptoms'), list) else str(doc.get('symptoms', ''))}",
            f"Remedies: {' '.join(doc.get('step_by_step_remedy', [])) if isinstance(doc.get('step_by_step_remedy'), list) else str(doc.get('step_by_step_cure', ''))}",
            f"Herbs: {' '.join(doc.get('herbs_and_ingredients', [])) if isinstance(doc.get('herbs_and_ingredients'), list) else str(doc.get('herbs_used', ''))}",
        ]
        return " | ".join(parts)

    def warm_up_embeddings(self):
        """Precompute embeddings for static Ayurvedic remedies using Gemini API"""
        updated = False
        for doc in self.static_knowledge:
            doc_id = doc.get("id")
            if doc_id and doc_id not in self.embeddings_cache:
                doc_text = self.document_to_text(doc)
                emb = GeminiService.get_embedding(doc_text)
                if emb:
                    self.embeddings_cache[doc_id] = emb
                    updated = True
        if updated:
            self.save_cache()

    def keyword_score(self, query, text):
        query_words = set(query.lower().split())
        text_lower = text.lower()
        score = 0
        for word in query_words:
            if len(word) > 2 and word in text_lower:
                score += 1
        return score

    def retrieve(self, query, top_k=3):
        """
        Hybrid retrieval combining Gemini semantic vector similarity and keyword relevance.
        Also retrieves registered doctor clinical advice from the database.
        """
        # Ensure static knowledge is loaded
        if not self.static_knowledge:
            self.load_static_knowledge()

        # Query embedding
        query_emb = GeminiService.get_embedding(query)
        
        ranked_docs = []
        for doc in self.static_knowledge:
            doc_id = doc.get("id")
            doc_text = self.document_to_text(doc)
            
            # Vector score
            sim = 0.0
            if query_emb and doc_id in self.embeddings_cache:
                sim = cosine_similarity(query_emb, self.embeddings_cache[doc_id])
            elif query_emb:
                # compute on-the-fly and cache
                doc_emb = GeminiService.get_embedding(doc_text)
                if doc_emb:
                    self.embeddings_cache[doc_id] = doc_emb
                    self.save_cache()
                    sim = cosine_similarity(query_emb, doc_emb)

            # Keyword bonus
            k_score = self.keyword_score(query, doc_text) / 10.0
            total_score = (sim * 0.7) + (min(k_score, 0.5) * 0.3)
            
            ranked_docs.append((total_score, doc))

        # Sort descending by score
        ranked_docs.sort(key=lambda x: x[0], reverse=True)
        retrieved_static = [doc for score, doc in ranked_docs[:top_k]]

        # Also search Doctor Contributions from database
        doctor_contributions = get_all_doctor_contributions()
        relevant_doctor_insights = []
        for doc_item in doctor_contributions:
            doc_content = f"{doc_item.get('condition_name', '')} {doc_item.get('symptoms', '')} {doc_item.get('step_by_step_cure', '')}"
            if self.keyword_score(query, doc_content) > 0:
                relevant_doctor_insights.append(doc_item)

        return retrieved_static, relevant_doctor_insights[:3]

# Global singleton
rag_engine = RAGEngine()
