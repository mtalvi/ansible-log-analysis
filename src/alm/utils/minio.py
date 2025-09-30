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
        secure=False,  # Use HTTP instead of HTTPS for internal OpenShift services
    )

    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    # save to ram
    import io
    import joblib

    with io.BytesIO() as buffer:
        joblib.dump(model, buffer)
        buffer.seek(0)

        minio_client.put_object(
            bucket_name, file_name, buffer, length=buffer.getbuffer().nbytes
        )
