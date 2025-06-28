from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from gradio_client import Client, handle_file
import tempfile
import os
import logging
import httpx
import uvicorn

from .azure_client import get_breed_prediction as get_breeds_prediction
from .custom_vision_client import get_dog_cat_prediction

# Ustawienie logowania
logging.basicConfig(level=logging.INFO)

# Wczytanie zmiennych środowiskowych
load_dotenv()

app = FastAPI(title="Pet Classifier AI 🐕🐈")

# Ścieżki
current_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Model Hugging Face
HF_SPACE_NAME = "MaxxxMi/predict_dog_age"
HF_API_NAME = "/predict"

async def get_dog_age_prediction(image_bytes: bytes) -> dict:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        client = Client(HF_SPACE_NAME)
        result = client.predict(
            image=handle_file(tmp_path),
            api_name=HF_API_NAME
        )

        label = str(result.get("prediction", result)).lower()

        label_to_range = {
            "young": "0–2 lata",
            "adult": "2–5 lat",
            "senior": "6+ lat"
        }

        mapped = label_to_range.get(label, label)

        if isinstance(result, dict):
            return {"prediction": mapped}
        else:
            return {"prediction": str(result)}
    except Exception as e:
        logging.error(f"Błąd podczas pobierania predykcji wieku psa: {e}")
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, error_message: str = None):
    context = {"request": request}
    if error_message:
        context["error_message"] = error_message
    return templates.TemplateResponse("index.html", context=context)

@app.post("/predict_breeds/", response_class=JSONResponse)
async def predict_breeds_endpoint(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        logging.warning(f"Otrzymano plik, który nie jest obrazem: {file.content_type}")
        return JSONResponse(
            status_code=400,
            content={"error": "Przesłany plik nie jest obrazem."}
        )

    try:
        image_bytes = await file.read()

        # najpierw predykcja wieku psa
        age_result = await get_dog_age_prediction(image_bytes)

        # potem próba predykcji ras (Azure)
        try:
            prediction_results = await get_breeds_prediction(image_bytes=image_bytes)
        except Exception as e:
            logging.error(f"Błąd z Custom Vision (Rasy): {e}")
            prediction_results = {"error": f"Błąd predykcji ras: {e}"}

        # dołącz wynik wieku psa
        prediction_results["dog_age_prediction"] = age_result

        return prediction_results

    except Exception as e:
        logging.error(f"Błąd podczas przetwarzania pliku dla ras: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Wystąpił wewnętrzny błąd serwera dla ras: {str(e)}"}
        )

@app.post("/predict_animal_type/", response_class=JSONResponse)
async def predict_animal_type_endpoint(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        logging.warning(f"Otrzymano plik, który nie jest obrazem: {file.content_type}")
        return JSONResponse(
            status_code=400,
            content={"error": "Przesłany plik nie jest obrazem."}
        )

    try:
        image_bytes = await file.read()
        prediction_result = await get_dog_cat_prediction(image_bytes)

        if prediction_result and prediction_result.get("error"):
            logging.error(f"Błąd z Custom Vision (Pies/Kot): {prediction_result.get('error')}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Błąd predykcji typu zwierzęcia: {prediction_result.get('error')}"}
            )

        return prediction_result

    except Exception as e:
        logging.error(f"Błąd podczas przetwarzania pliku dla typu zwierzęcia: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Wystąpił wewnętrzny błąd serwera dla typu zwierzęcia: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
