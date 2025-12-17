import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from app.core.config import settings
from app.core.chroma import get_documents_collection
from app.services.embedding_service import embedding_service
from app.schemas.chat import CitationSource

logger = logging.getLogger(__name__)


class RAGServiceError(Exception):
    """Exception raised for RAG pipeline errors."""
    pass


class RAGService:
    """
    Retrieval-Augmented Generation service.
    Orchestrates vector similarity lookup, strict prompt construction,
    and token-by-token streaming via Google Gemini.
    """

    def __init__(self):
        self.primary_model = settings.GEMINI_CHAT_MODEL
        self.fallback_model = settings.GEMINI_CHAT_FALLBACK_MODEL

    def retrieve_context(
        self,
        query: str,
        notebook_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query ChromaDB for top-k nearest semantic chunks filtered by notebook_id.
        """
        collection = get_documents_collection()

        # Generate 768-dim query embedding
        query_vector = embedding_service.get_embedding(query)

        try:
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where={"notebook_id": notebook_id},
                include=["documents", "metadatas", "distances"]
            )
        except Exception as query_err:
            logger.error(f"ChromaDB retrieval failed for notebook '{notebook_id}': {query_err}")
            return []

        chunks: List[Dict[str, Any]] = []
        documents_list = results.get("documents", [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        ids_list = results.get("ids", [[]])[0]

        for idx, (doc_text, meta, chunk_id) in enumerate(zip(documents_list, metadatas_list, ids_list)):
            meta = meta or {}
            chunks.append({
                "doc_id": idx + 1,
                "chunk_id": chunk_id,
                "filename": meta.get("filename", "unknown_source"),
                "page_number": int(meta.get("page_number", 1)),
                "text": doc_text
            })

        logger.info(f"Retrieved {len(chunks)} relevant chunks for query in notebook '{notebook_id}'.")
        return chunks

    def build_system_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Construct strict academic RAG prompt grounded solely in retrieved context.
        """
        context_blocks = []
        for c in chunks:
            block = (
                f"---\n"
                f"[Doc ID: {c['doc_id']} | Source: {c['filename']} | Page: {c['page_number']}]\n"
                f"{c['text']}"
            )
            context_blocks.append(block)

        formatted_context = "\n".join(context_blocks)

        prompt = (
            "You are StudySync AI, a precise academic assistant.\n\n"
            "INSTRUCTIONS:\n"
            "1. Answer the user's question STRICTLY using only the provided CONTEXT below.\n"
            "2. If the answer cannot be found in the CONTEXT, respond with:\n"
            '   "I could not find the answer to that in your selected notebook documents."\n'
            "3. Include inline citations matching the chunk index, e.g., [Doc 1, Page 4].\n"
            "4. Be concise, well-structured, and factual.\n\n"
            "CONTEXT:\n"
            f"{formatted_context}\n\n"
            f"USER QUESTION: {query}"
        )
        return prompt

    async def _stream_gemini(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Invoke Google Gemini streaming chat with model fallback.
        """
        from google import genai

        api_key = settings.GEMINI_API_KEY
        client = genai.Client(api_key=api_key)

        models_to_try = [self.primary_model, self.fallback_model]

        for model in models_to_try:
            try:
                chat = client.chats.create(model=model)
                response_stream = chat.send_message_stream(prompt)
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as model_err:
                logger.warning(f"Chat streaming with '{model}' failed ({model_err}). Trying next model...")

        raise RAGServiceError(f"All chat models ({models_to_try}) failed to generate stream.")

    async def stream_chat(
        self,
        query: str,
        notebook_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Main generator returning SSE-formatted strings:
        - data: {"type": "content", "token": "..."}\n\n
        - data: {"type": "citations", "citations": [...]}\n\n
        - data: [DONE]\n\n
        """
        try:
            # 1. Retrieve top-3 chunks
            chunks = self.retrieve_context(query=query, notebook_id=notebook_id, top_k=3)

            # Convert to structured citation objects
            citation_sources = [
                CitationSource(
                    doc_id=c["doc_id"],
                    chunk_id=c["chunk_id"],
                    filename=c["filename"],
                    page_number=c["page_number"],
                    snippet=c["text"][:200] + ("..." if len(c["text"]) > 200 else "")
                )
                for c in chunks
            ]

            # If no context found in vector store
            if not chunks:
                msg = "I couldn't find any relevant study materials in this notebook. Please upload documents first."
                payload = json.dumps({"type": "content", "token": msg})
                yield f"data: {payload}\n\n"

                citations_payload = json.dumps({"type": "citations", "citations": []})
                yield f"data: {citations_payload}\n\n"
                yield "data: [DONE]\n\n"
                return

            # 2. Build prompt
            prompt = self.build_system_prompt(query, chunks)

            # 3. Stream model response
            if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
                async for token in self._stream_gemini(prompt):
                    payload = json.dumps({"type": "content", "token": token})
                    yield f"data: {payload}\n\n"
            else:
                # Offline mock streaming fallback for local testing
                mock_tokens = [
                    "Based on your notes, ",
                    f"this concept is explained in [Doc 1, Page {chunks[0]['page_number']}]. ",
                    "It details how operations are coordinated efficiently."
                ]
                import asyncio
                for tok in mock_tokens:
                    payload = json.dumps({"type": "content", "token": tok})
                    yield f"data: {payload}\n\n"
                    await asyncio.sleep(0.05)

            # 4. Push citations payload
            citations_data = json.dumps({
                "type": "citations",
                "citations": [c.model_dump() for c in citation_sources]
            })
            yield f"data: {citations_data}\n\n"

            # 5. Complete stream
            yield "data: [DONE]\n\n"

        except Exception as exc:
            logger.error(f"Stream generation error: {exc}")
            err_payload = json.dumps({"type": "error", "error": str(exc)})
            yield f"data: {err_payload}\n\n"
            yield "data: [DONE]\n\n"


# Singleton instance
rag_service = RAGService()
