@echo off
echo Instalowanie zależności...
pip install -r requirements.txt

echo Uruchamianie aplikacji FastAPI...
start /b python -m app.main

echo Czekam na uruchomienie aplikacji (10 sekund)...
timeout /t 10 /nobreak > NUL

echo Otwieranie przeglądarki pod adresem http://localhost:8000
start http://localhost:8000

echo Aplikacja działa. Aby zamknac, nacisnij CTRL+C w oknie serwera.

rem Skrypt czeka w tle, dopoki aplikacja FastApi nie zostanie zamknieta lub okno konsoli.
rem Jesli chcesz, aby skrypt zakonczyl sie po otwarciu przegladarki, usun 'start /b'
rem i zamiast tego uzyj 'python -m app.main', ale wtedy okno skryptu bedzie zajete.

exit