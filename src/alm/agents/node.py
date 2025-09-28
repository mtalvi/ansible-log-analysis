from typing import List
import os
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN, MeanShift, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
import joblib
from langchain_openai import ChatOpenAI
from src.alm.agents.output_scheme import (
    SummarySchema,
    ClassifySchema,
    SuggestStepByStepSolutionSchema,
    RouterStepByStepSolutionSchema,
)
import numpy as np
from src.alm.utils.minio import upload_model_to_minio

# Load the user message (prompt) from the markdown file
with open("src/alm/agents/prompts/summarize_error_log.md", "r") as f:
    log_summary_user_message = f.read()

with open("src/alm/agents/prompts/classifiy_log.md", "r") as f:
    log_category_user_message = f.read()

with open("src/alm/agents/prompts/create_step_by_step_sol.md", "r") as f:
    log_suggest_step_by_step_solution_user_message = f.read()

with open("src/alm/agents/prompts/router_step_by_step_solution.md", "r") as f:
    router_step_by_step_solution_user_message = f.read()


# Can be improve by using eval-optimizer.
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


async def router_step_by_step_solution(log_summary: str, log: str, llm: ChatOpenAI):
    llm_router_step_by_step_solution = llm.with_structured_output(
        RouterStepByStepSolutionSchema
    )
    router_step_by_step_solution = await llm_router_step_by_step_solution.ainvoke(
        [
            {
                "role": "system",
                "content": "You are an Ansible expert and helpful assistant",
            },
            {
                "role": "user",
                "content": router_step_by_step_solution_user_message.replace(
                    "{log_summary}", log_summary
                ).replace("{ansible_error_log}", log),
            },
        ]
    )
    return router_step_by_step_solution.suggestion


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


def _embed_logs(logs: List[str]):
    model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL_NAME")
    encoder = SentenceTransformer(model_name)

    embeddings = encoder.encode(
        [summary[-50:] for summary in logs],
        convert_to_numpy=True,
        show_progress_bar=True,
        # batch_size=10,
    )
    print("finished embeddings")

    return embeddings


def _cluster_logs(embeddings: np.ndarray):
    algorithm = os.getenv("CLUSTERING_ALGORITHM")
    if algorithm.lower() == "dbscan":
        # DBSCAN - Good for finding clusters of varying shapes and handling noise
        # Uses cosine distance for text similarity
        distance_matrix = cosine_distances(embeddings)
        cluster_model = DBSCAN(eps=0.3, min_samples=2, metric="precomputed")
        cluster_labels = cluster_model.fit_predict(distance_matrix)

    elif algorithm.lower() == "meanshift":
        # Mean Shift - Automatically determines number of clusters
        cluster_model = MeanShift(bandwidth=None)  # Auto-estimate bandwidth
        cluster_labels = cluster_model.fit_predict(embeddings)

    elif algorithm.lower() == "agglomerative":
        # Agglomerative Clustering with distance threshold
        # Automatically determines number of clusters based on distance threshold
        cluster_model = AgglomerativeClustering(
            n_clusters=None, distance_threshold=0.5, linkage="average", metric="cosine"
        )
        cluster_labels = cluster_model.fit_predict(embeddings)

    else:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. Choose from 'dbscan', 'meanshift', 'agglomerative'"
        )
    return cluster_model, cluster_labels


def infer_cluster_log(log: str):
    embeddings = _embed_logs([log])
    cluster_model = joblib.load(os.getenv("TMP_CLUSTER_MODEL_PATH"))
    cluster_label = cluster_model.predict(embeddings)
    return str(cluster_label.tolist()[0])


def _handle_outlaier_cluster(cluster_labels: np.ndarray):
    clusters = np.unique(cluster_labels)
    max_cluster = clusters.max()
    # each cluster that is -1 replace it to be in cluster by himself

    # Find indices where cluster_labels is -1 (outliers/noise points)
    outlier_indices = np.where(cluster_labels == -1)[0]

    # Assign each outlier its own unique cluster ID
    next_cluster_id = max_cluster + 1
    for idx in outlier_indices:
        cluster_labels[idx] = next_cluster_id
        next_cluster_id += 1

    return cluster_labels


# TODO export it to be service that is deployed once, and been called from diffrent api requests.
# Deploy it as service.
def train_embed_and_cluster_logs(
    logs: List[str],
    save_cluster_model: bool = True,
):
    """
    Cluster log summaries using sentence embeddings and various clustering algorithms.

    Args:
        log_summaries: List of log summary strings

    Returns:
        List of cluster labels for each log summary (same order as input)
    """
    if not logs:
        return []

    # Embed logs
    embeddings = _embed_logs(logs)

    # Train clustering model
    cluster_model, cluster_labels = _cluster_logs(embeddings)

    # handle outlaier cluster
    cluster_labels = _handle_outlaier_cluster(cluster_labels)

    if save_cluster_model:
        if os.getenv("MINIO_BUCKET_NAME"):
            upload_model_to_minio(
                cluster_model, os.getenv("MINIO_BUCKET_NAME"), "clustering_model.joblib"
            )
        else:
            joblib.dump(cluster_model, os.getenv("TMP_CLUSTER_MODEL_PATH"))

    return cluster_labels.tolist()
