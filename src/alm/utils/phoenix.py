from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register


def register_phoenix():
    # Register Phoenix with auto-instrumentation
    tracer_provider = register(
        project_name="my-llm-app",
        auto_instrument=True,
    )

    # Explicitly instrument LangChain for Phoenix tracing
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

    return tracer_provider.get_tracer(__name__)
