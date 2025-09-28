import os
from minio import Minio
import sklearn


def upload_model_to_minio(
    model: sklearn.base.BaseEstimator, bucket_name: str, file_name: str
):
    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT") + ":" + os.getenv("MINIO_PORT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
    )

    # save to ram
    import io
    import joblib

    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    buffer.seek(0)

    minio_client.fput_object(bucket_name, file_name, buffer)
