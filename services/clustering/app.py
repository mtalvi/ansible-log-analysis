from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI()
# TODO change it for cluster deployment to be model registry.
model = joblib.load("clustering_model.joblib")


class InputData(BaseModel):
    features: list[float]  # Adjust based on your model's input shape


@app.post("/predict")
def predict(data: InputData):
    input_array = np.array(data.features)
    prediction = model.predict(input_array)
    return {"prediction": prediction.tolist()}
