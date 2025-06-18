# app/main.py

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import logging
import uvicorn # Importujemy uvicorn tutaj, aby był dostępny w __main__

# Ustawienie logowania (na górze pliku, raz)
logging.basicConfig(level=logging.INFO)

# Importujemy KLIENTÓW dla obu usług Custom Vision
# get_breeds_prediction - model do klasyfikacji RAS (używa azure_client.py)
from .azure_client import get_breed_prediction as get_breeds_prediction
# get_dog_cat_prediction - model do klasyfikacji Pies/Kot (używa custom_vision_client.py)
from .custom_vision_client import get_dog_cat_prediction

# Wczytanie zmiennych środowiskowych z pliku .env
# To jest potrzebne tylko lokalnie, na Azure App Service zmienne środowiskowe konfigurujesz w portalu.
load_dotenv()

app = FastAPI(title="Pet Classifier AI 🐕🐈")

# --- KLUCZOWE ZMIANY DLA PRAWIDŁOWYCH ŚCIEŻEK NA AZURE I LOKALNIE, Bartek! ---
# Pobieramy absolutną ścieżkę do katalogu, w którym znajduje się main.py (czyli 'app')
current_dir = os.path.dirname(os.path.abspath(__file__))

# Montowanie statycznych plików (CSS, JS, obrazki, tłumaczenia)
# Ścieżka do katalogu 'static' jest teraz budowana względem 'app'
# Upewnij się, że katalog 'app/static' istnieje i zawiera Twoje pliki
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")
logging.info(f"Serwowanie statycznych plików z katalogu: {os.path.join(current_dir, 'static')}")

# Konfiguracja szablonów Jinja2
# Ścieżka do katalogu 'templates' jest teraz budowana względem 'app'
# Upewnij się, że katalog 'app/templates' istnieje
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))
logging.info(f"Ładowanie szablonów z katalogu: {os.path.join(current_dir, 'templates')}")
# --- KONIEC KLUCZOWYCH ZMIAN ---


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, error_message: str = None):
    """Serwuje główną stronę HTML."""
    context = {"request": request}
    if error_message:
        context["error_message"] = error_message
    return templates.TemplateResponse("index.html", context=context)

@app.post("/predict_breeds/", response_class=JSONResponse)
async def predict_breeds_endpoint(file: UploadFile = File(...)):
    """
    Endpoint do przyjmowania obrazu i zwracania predykcji RAS (za pomocą Custom Vision).
    """
    if not file.content_type.startswith("image/"):
        logging.warning(f"Otrzymano plik, który nie jest obrazem: {file.content_type}")
        return JSONResponse(
            status_code=400,
            content={"error": "Przesłany plik nie jest obrazem."}
        )

    try:
        image_bytes = await file.read()
        
        # Wywołujemy klienta Custom Vision dla ras
        prediction_results = await get_breeds_prediction(image_bytes=image_bytes)

        if prediction_results and prediction_results.get("error"):
            logging.error(f"Błąd z Custom Vision (Rasy): {prediction_results.get('error')}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Błąd predykcji ras: {prediction_results.get('error')}"}
            )

        return prediction_results # Zwracamy całe wyniki predykcji ras

    except Exception as e:
        logging.error(f"Błąd podczas przetwarzania pliku dla ras: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Wystąpił wewnętrzny błąd serwera dla ras: {str(e)}"}
        )

@app.post("/predict_animal_type/", response_class=JSONResponse)
async def predict_animal_type_endpoint(file: UploadFile = File(...)):
    """
    Endpoint do przyjmowania obrazu i zwracania predykcji typu zwierzęcia (Pies/Kot)
    (za pomocą Custom Vision).
    """
    if not file.content_type.startswith("image/"):
        logging.warning(f"Otrzymano plik, który nie jest obrazem: {file.content_type}")
        return JSONResponse(
            status_code=400,
            content={"error": "Przesłany plik nie jest obrazem."}
        )

    try:
        image_bytes = await file.read()
        
        # Wywołujemy klienta Custom Vision dla typu zwierzęcia (Pies/Kot)
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

# To uruchamiasz tylko lokalnie
if __name__ == "__main__":
    import uvicorn
    # Upewnij się, że uruchamiasz to z katalogu głównego projektu (`pet-classifier-webapp`)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
