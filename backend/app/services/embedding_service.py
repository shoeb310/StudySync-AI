import hashlib
import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard embedding model in modern google-genai SDK
PRIMARY_EMBEDDING_MODEL = "gemini-embedding-001"
FALLBACK_EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSION = 768


class EmbeddingServiceError(Exception):
    """Exception raised for errors during vector embedding generation."""
    pass


class EmbeddingService:
    """
    Wrapper for Google AI's embedding models using the modern `google-genai` SDK.
    Configured for 768-dimensional dense vector embeddings.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or settings.GEMINI_API_KEY or "").strip()
        self._client = None
        self._is_configured = False
        self._model_name = PRIMARY_EMBEDDING_MODEL

        if self.api_key and len(self.api_key) > 5 and not self.api_key.startswith("your_gemini"):
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                self._is_configured = True
                logger.info(f"Initialized Google GenAI Client with embedding model '{self._model_name}'.")
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")
        else:
            logger.warning(
                "GEMINI_API_KEY is not set or using placeholder. "
                "EmbeddingService will generate deterministic mock embeddings for offline testing."
            )

    @property
    def is_configured(self) -> bool:
        """Returns True if a live Google Gemini API key is configured."""
        return self._is_configured

    def _generate_deterministic_mock_vector(self, text: str) -> List[float]:
        """
        Fallback mock generator producing a deterministic 768-dimension vector
        based on the text SHA-256 hash when running in offline/testing mode.
        """
        hasher = hashlib.sha256(text.encode("utf-8"))
        seed = int(hasher.hexdigest()[:8], 16)

        import random
        rnd = random.Random(seed)
        vec = [rnd.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIMENSION)]

        # Normalize to unit length
        norm = sum(x * x for x in vec) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec

    def _call_embed_api(self, contents, config):
        """Helper to invoke embed_content with model fallback if needed."""
        from google.genai import types

        for model in [self._model_name, FALLBACK_EMBEDDING_MODEL]:
            try:
                response = self._client.models.embed_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                self._model_name = model
                return response
            except Exception as exc:
                err_str = str(exc)
                if "404" in err_str or "not found" in err_str.lower():
                    logger.warning(f"Model '{model}' not available for embedContent, trying fallback...")
                    continue
                raise exc

        raise EmbeddingServiceError(f"None of the embedding models ({self._model_name}, {FALLBACK_EMBEDDING_MODEL}) were accessible.")

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate a 768-dimensional embedding vector for a single text string.

        Args:
            text: Input text content.

        Returns:
            768-dimensional list of floats.
        """
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIMENSION

        if not self._is_configured or self._client is None:
            return self._generate_deterministic_mock_vector(text)

        try:
            from google.genai import types
            config = types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION)
            response = self._call_embed_api(contents=text, config=config)

            if response.embeddings and len(response.embeddings) > 0:
                return list(response.embeddings[0].values)
            raise EmbeddingServiceError("Empty embedding list received from Google Gemini API.")
        except Exception as exc:
            logger.error(f"Google Gemini embedding failed: {exc}")
            raise EmbeddingServiceError(f"Embedding API error: {str(exc)}") from exc

    def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts in manageable batches.

        Args:
            texts: List of text strings.
            batch_size: Maximum batch size per request.

        Returns:
            List of 768-dimensional float vectors.
        """
        if not texts:
            return []

        if not self._is_configured or self._client is None:
            return [self._generate_deterministic_mock_vector(t) for t in texts]

        all_embeddings: List[List[float]] = []
        from google.genai import types
        config = types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION)

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self._call_embed_api(contents=batch, config=config)
                if response.embeddings:
                    for emb in response.embeddings:
                        all_embeddings.append(list(emb.values))
                else:
                    raise EmbeddingServiceError("Empty embeddings batch returned.")
            except Exception as exc:
                logger.error(f"Batch embedding failed for batch starting at index {i}: {exc}")
                raise EmbeddingServiceError(f"Batch embedding API error: {str(exc)}") from exc

        return all_embeddings


# Default singleton instance
embedding_service = EmbeddingService()
