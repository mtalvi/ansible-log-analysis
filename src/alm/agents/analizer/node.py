from typing import Literal, List

from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN, MeanShift, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Load the user message (prompt) from the markdown file
with open("src/alm/agents/analizer/prompts/summarize_error_log.md", "r") as f:
    log_summary_user_message = f.read()

with open("src/alm/agents/analizer/prompts/classifiy_log.md", "r") as f:
    log_category_user_message = f.read()

with open("src/alm/agents/analizer/prompts/create_step_by_step_sol.md", "r") as f:
    log_suggest_step_by_step_solution_user_message = f.read()


# create stractued output for summary log and categorize log
class SummarySchema(BaseModel):
    summary: str = Field(description="Summary of the log")


class ClassifySchema(BaseModel):
    category: Literal[
        "Cloud Infrastructure / AWS Engineers",
        "Kubernetes / OpenShift Cluster Admins",
        "DevOps / CI/CD Engineers (Ansible + Automation Platform)",
        "Networking / Security Engineers",
        "System Administrators / OS Engineers",
        "Application Developers / GitOps / Platform Engineers",
        "Identity & Access Management (IAM) Engineers",
        "Other / Miscellaneous",
    ] = Field(description="Category of the log")


class SuggestStepByStepSolutionSchema(BaseModel):
    step_by_step_solution: str = Field(
        description="Step by step solution to the problem"
    )


async def summarize_log(log, llm: ChatOpenAI):
    llm_summary = llm.with_structured_output(SummarySchema)
    log_summary = await llm_summary.ainvoke(
        [
            {"role": "system", "content": "You Ansible expert and helpful assistant"},
            {
                "role": "user",
                "content": log_summary_user_message.replace("{error_log}", log),
            },
        ]
    )
    return log_summary.summary


async def classify_log(log_summary, llm: ChatOpenAI):
    llm_categorize = llm.with_structured_output(ClassifySchema)
    log_category = await llm_categorize.ainvoke(
        [
            {"role": "system", "content": "You Ansible expert and helpful assistant"},
            {
                "role": "user",
                "content": log_category_user_message.replace(
                    "{log_summary}", log_summary
                ),
            },
        ]
    )
    return log_category.category


def get_category_cluster(classification: str) -> str:
    """Map expertClassification to categoryCluster for higher-level grouping."""
    classification_to_cluster = {
        "Cloud Infrastructure / AWS Engineers": "Cloud Infrastructure",
        "Kubernetes / OpenShift Cluster Admins": "Kubernetes / OpenShift Cluster Admins",
        "DevOps / CI/CD Engineers (Ansible + Automation Platform)": "DevOps / CI/CD Engineers (Ansible + Automation Platform)",
        "Networking / Security Engineers": "Networking / Security Engineers",
        "System Administrators / OS Engineers": "System Administrators / OS Engineers",
        "Application Developers / GitOps / Platform Engineers": "Application Developers / GitOps / Platform Engineers",
        "Identity & Access Management (IAM) Engineers": "Identity & Access Management (IAM) Engineers",
        "Other / Miscellaneous": "Other / Miscellaneous",
    }
    return classification_to_cluster.get(classification, "Unclassified")


async def suggest_step_by_step_solution(log_summary: str, log: str, llm: ChatOpenAI):
    llm_suggest_step_by_step_solution = llm.with_structured_output(
        SuggestStepByStepSolutionSchema
    )
    log_suggest_step_by_step_solution = await llm_suggest_step_by_step_solution.ainvoke(
        [
            {
                "role": "system",
                "content": "You are an Ansible expert and helpful assistant",
            },
            {
                "role": "user",
                "content": log_suggest_step_by_step_solution_user_message.replace(
                    "{log_summary}",
                    log_summary,  # currently disabled
                ).replace("{ansible_error_log}", log),
            },
        ]
    )
    return log_suggest_step_by_step_solution.step_by_step_solution


def cluster_logs(
    logs: List[str],
    model_name: str = "Qwen/Qwen3-Embedding-0.6B",
    algorithm: str = "meanshift",
):
    """
    Cluster log summaries using sentence embeddings and various clustering algorithms.

    Args:
        log_summaries: List of log summary strings
        model_name: HuggingFace sentence transformer model name
        algorithm: Clustering algorithm to use ('dbscan', 'meanshift', 'agglomerative')

    Returns:
        List of cluster labels for each log summary (same order as input)
    """
    if not logs:
        return []

    # Initialize sentence transformer encoder
    encoder = SentenceTransformer(model_name)

    # Encode all log summaries
    embeddings = encoder.encode(
        [summary[-50:] for summary in logs],
        convert_to_numpy=True,
        show_progress_bar=True,
        # batch_size=10,
    )

    print("finished embeddings")

    if algorithm.lower() == "dbscan":
        # DBSCAN - Good for finding clusters of varying shapes and handling noise
        # Uses cosine distance for text similarity
        distance_matrix = cosine_distances(embeddings)
        clusterer = DBSCAN(eps=0.3, min_samples=2, metric="precomputed")
        cluster_labels = clusterer.fit_predict(distance_matrix)

    elif algorithm.lower() == "meanshift":
        # Mean Shift - Automatically determines number of clusters
        clusterer = MeanShift(bandwidth=None)  # Auto-estimate bandwidth
        cluster_labels = clusterer.fit_predict(embeddings)

    elif algorithm.lower() == "agglomerative":
        # Agglomerative Clustering with distance threshold
        # Automatically determines number of clusters based on distance threshold
        clusterer = AgglomerativeClustering(
            n_clusters=None, distance_threshold=0.5, linkage="average", metric="cosine"
        )
        cluster_labels = clusterer.fit_predict(embeddings)

    else:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. Choose from 'dbscan', 'meanshift', 'agglomerative'"
        )

    return cluster_labels.tolist()
