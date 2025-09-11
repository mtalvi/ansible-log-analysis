import os
import subprocess
import logging


def load_from_local_file(model_path: str) -> str:
    import joblib

    return joblib.load(model_path)


def load_from_model_registry(model_name: str) -> str:
    from model_registry import ModelRegistry  # , utils

    author_value, user_token_value, host_value = _fetch_model_registry_credentials()

    model_registry = ModelRegistry(
        host=host_value,
        author=author_value,
        token=user_token_value,
    )

    model = model_registry.get_registered_model(model_name)
    return model


def _fetch_model_registry_credentials() -> tuple[str, str, str]:
    logger = logging.getLogger(__name__)

    author_value = subprocess.run(
        "oc whoami", shell=True, capture_output=True, text=True, check=True
    ).stdout.strip()
    user_token_value = subprocess.run(
        "oc whoami -t", shell=True, capture_output=True, text=True, check=True
    ).stdout.strip()
    logger.debug(f"author_value = {author_value}")
    mr_namespace = os.getenv("MODEL_REGISTRY_NAMESPACE")
    mr_container = os.getenv("MODEL_REGISTRY_CONTAINER")

    cmd = (
        f"oc get svc {mr_container} -n {mr_namespace} -o json | "
        f"jq '.metadata.annotations.\"routing.opendatahub.io/external-address-rest\"'"
    )
    host_output = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, check=True
    ).stdout.strip()

    if not host_output:
        error_message = (
            f"Model registry service '{mr_container}' is not available in namespace '{mr_namespace}'. "
            f"Please ensure the service is properly deployed and accessible."
        )
        logger.info(error_message)
        raise RuntimeError(error_message)

    host_value = f"https://{host_output[1:-5]}"  # Remove quotes and :443
    return author_value, user_token_value, host_value
