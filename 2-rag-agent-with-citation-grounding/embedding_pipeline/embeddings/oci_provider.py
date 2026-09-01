"""OCI Cohere implementation of the embedding-provider contract."""

import logging
import time

import oci

from embedding_pipeline.embeddings.data_models import EmbeddingRequest, EmbeddingResponse
from embedding_pipeline.embeddings.oci_config import OciEmbeddingConfig


logger = logging.getLogger(__name__)


class OciEmbeddingProvider:
    """Create embeddings with an OCI-hosted Cohere Embed model."""

    def __init__(self, config: OciEmbeddingConfig) -> None:
        """Load OCI profile authentication and create an inference client."""
        self.config = config
        oci_profile_config = oci.config.from_file(
            file_location=self.config.config_file_path,
            profile_name=self.config.profile_name,
        )
        oci.config.validate_config(oci_profile_config)
        self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=oci_profile_config,
            service_endpoint=self.config.endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )

    def _build_embed_details(self, request: EmbeddingRequest):
        """Convert a neutral embedding request into OCI SDK request details."""
        return oci.generative_ai_inference.models.EmbedTextDetails(
            compartment_id=self.config.compartment_id,
            inputs=[request.text],
            input_type=request.input_type,
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=self.config.model_id
            ),
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Embed one document chunk or one user query through OCI."""
        started_at = time.perf_counter()
        logger.info("OCI embedding call started", extra={"input_type": request.input_type})

        try:
            response = self.client.embed_text(self._build_embed_details(request))
        except Exception as error:
            duration_ms = round((time.perf_counter() - started_at) * 1000)
            logger.warning(
                "OCI embedding call failed",
                extra={"duration_ms": duration_ms, "error_type": type(error).__name__},
            )
            raise

        vectors = response.data.embeddings
        if not vectors:
            raise ValueError("OCI returned no embedding vectors.")

        request_id = getattr(response, "request_id", None)
        logger.info(
            "OCI embedding call finished",
            extra={
                "request_id": request_id,
                "duration_ms": round((time.perf_counter() - started_at) * 1000),
                "dimensions": len(vectors[0]),
            },
        )
        return EmbeddingResponse(
            embedding=vectors[0],
            provider_name="oci",
            model_id=getattr(response.data, "model_id", None) or self.config.model_id,
            input_type=request.input_type,
            request_id=request_id,
        )
