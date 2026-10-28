# Hedging & Derivatives Pricing System

Polskojęzyczny prototyp analityczny do wyceny FX i instrumentów towarowych oraz
oceny cross-hedge. Aplikacja jest napisana w Pythonie i Streamlit; modele
finansowe są oddzielone od interfejsu i objęte testami jednostkowymi.

> **Ograniczenie zastosowania:** prototyp demonstracyjny, nie system transakcyjny
> ani zweryfikowany system produkcyjny. Nie pobiera notowań rynkowych, nie
> przechowuje danych biznesowych i nie zastępuje walidacji modeli, wyceny
> transakcyjnej ani opinii prawno-księgowej. Dane w `dane_cross_hedge.csv` są
> syntetyczne.

Pełna metodologia, przykłady i bibliografia: [Hedging & Derivatives Pricing
System.md](./Hedging%20%26%20Derivatives%20Pricing%20System.md).

## Funkcje

- Forward FX na podstawie parytetu stóp i wycena MtM istniejącej pozycji.
- Europejskie opcje FX call/put modelem Garmana–Kohlhagena, w tym Greeks.
- Porównanie kosztu importera: brak hedge, pełny/częściowy forward i call z
  finansowaniem premii.
- Forward towarowy metodą kosztu przenoszenia.
- Cena stała, MtM i przepływy swapu towarowego fixed-for-floating.
- OLS hedge ratio oraz skuteczność in-sample/out-of-sample na danych syntetycznych.

## Uruchomienie lokalne

Wymagania: Python 3.11–3.13. Projekt wymaga Streamlit >=1.57.0.

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
streamlit run app.py
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
streamlit run app.py
```

Aplikacja otworzy się domyślnie pod `http://localhost:8501`. Do pracy z własnymi
szeregami należy przygotować dane oraz walidację zgodnie z metodologią; sam
prototyp nie przyjmuje danych rynkowych ani nie ma integracji z dostawcą danych.

## Testy i kontrola jakości

```bash
ruff check .
ruff format --check .
pytest --cov=hedging_system --cov-report=term-missing --cov-fail-under=90
```

Testy obejmują wzory, parytet opcji, warunki brzegowe, znaki pozycji i syntetyczny
przykład cross-hedge. Wynik testów nie jest walidacją modeli na danych rynkowych.

## Obraz i lokalny Docker Compose

Wymagania: Docker Engine z pluginem Compose v2.

```bash
docker compose -f compose.yaml up --build -d
docker compose -f compose.yaml ps
docker compose -f compose.yaml logs --follow hedging-dashboard
docker compose -f compose.yaml down
```

Usługa wiąże port aplikacji wyłącznie z `127.0.0.1:8501`, uruchamia się jako
nieuprzywilejowany użytkownik i używa read-only root filesystem oraz healthchecka.
Dla dostępu z sieci należy zastosować reverse proxy z HTTPS i kontrolą dostępu.
Przykładowy szablon Nginx: [`deploy/nginx.conf.example`](./deploy/nginx.conf.example).

### Konfiguracja serwera Linux

1. Przygotuj wspieraną dystrybucję Linux, aktualizacje bezpieczeństwa, Docker
   Engine/Compose, DNS i certyfikat TLS. Ogranicz dostęp SSH kluczami i firewall.
2. Umieść repozytorium na serwerze lub wdrażaj tylko przez obrazy z GitLab
   Container Registry. Dla konta deployment utwórz w GitLab **read-only deploy
   token** z zakresem `read_registry`; nie używaj osobistego tokenu ani nie
   zapisuj hasła w repozytorium.
3. Zaloguj się do registry interaktywnie albo przez bezpieczny pipe:

   ```bash
   echo "$GITLAB_DEPLOY_TOKEN" | docker login registry.gitlab.com \
     --username "$GITLAB_DEPLOY_USER" --password-stdin
   ```

   Token wczytaj z menedżera sekretów/zmiennej chronionej. Nie zapisuj go w
   historii powłoki ani pliku `.env`.
4. Zapisz `APP_IMAGE=registry.gitlab.com/grupa/projekt:<commit-sha>` w
   chronionym pliku `.env` na serwerze. Używaj niezmiennego tagu commit SHA albo
   wersjonowanego tagu release, nie `latest` jako referencji wdrożenia.
5. W katalogu z `compose.yaml` uruchom:

   ```bash
   docker compose pull
   docker compose up -d --no-build --pull always
   docker compose ps
   ```

6. Skonfiguruj reverse proxy Nginx/Ingress z HTTPS, WebSocket Upgrade i
   `proxy_read_timeout`; port 8501 jest celowo niedostępny z zewnętrznej sieci.
   **Przed publicznym udostępnieniem dodaj SSO/OAuth2 Proxy, VPN lub inną
   zatwierdzoną kontrolę dostępu. Sama aplikacja nie ma uwierzytelniania ani
   autoryzacji.** Nie wystawiaj jej bezpośrednio do Internetu.
7. Zweryfikuj status healthcheck, logi, backup/restore konfiguracji i procedurę
   rollbacku do poprzedniego obrazu. Ten projekt nie konfiguruje hosta, DNS,
   firewalla, certyfikatów ani polityki backupu.

Zalecane ustawienia serwera: uruchamianie Docker daemon jako usługi systemowej,
automatyczne aktualizacje OS, ograniczony firewall (SSH i 443 tylko według
polityki organizacji), monitoring zdrowia/zasobów oraz alertowanie.

## GitLab: repozytorium i CI/CD

### Pierwsza publikacja

Utwórz puste repozytorium GitLab, a lokalnie w katalogu projektu:

```bash
git init
git add .
git commit -m "Build hedging analytics prototype"
git branch -M main
git remote add origin git@gitlab.com:grupa/projekt.git
git push -u origin main
```

Przed `git add` sprawdź `git status` i upewnij się, że nie dodajesz `.env`,
tokenów, firmowych kwotowań ani innych danych poufnych. Zastąp przykładowy URL
własnym adresem projektu.

### Pipeline

Plik [`.gitlab-ci.yml`](./.gitlab-ci.yml) definiuje:

1. walidację Ruff (lint i formatowanie) oraz testy z raportem JUnit i progiem
   pokrycia modułów modelowych;
2. publikację obrazu do GitLab Container Registry po przejściu testów na
   domyślnej gałęzi lub tagu Git;
3. tag SHA commitu oraz dodatkowo `latest` wyłącznie dla domyślnej gałęzi.

Job publikujący obraz korzysta z Docker-in-Docker. Runner musi pozwalać na
uprzywilejowany tryb usługi `docker:dind`; w środowisku, w którym jest to
zabronione, należy skonfigurować zatwierdzony, nieuprzywilejowany builder
(np. BuildKit/Buildah) zamiast osłabiać politykę bezpieczeństwa runnera.

Zabezpiecz gałąź domyślną, wymagaj zielonego pipeline dla merge requestów,
ogranicz uprawnienia do release, włącz ochronę tagów i nie zapisuj sekretów w
repozytorium. Standardowe zmienne `CI_REGISTRY*` dostarcza GitLab CI. Przed
użyciem produkcyjnym przypnij obrazy bazowe do digestów i wprowadź zatwierdzony
skaner zależności/obrazu oraz politykę aktualizacji.

## Struktura

```text
.
├── app.py
├── pages/                 # Strony aplikacji Streamlit
├── src/hedging_system/    # Czyste funkcje wyceny i loader danych demo
├── tests/                 # Testy modeli oraz danych syntetycznych
├── dane_cross_hedge.csv   # Jawnie syntetyczny zbiór przykładowy
├── deploy/                # Przykładowa konfiguracja reverse proxy
├── compose.yaml
├── Dockerfile
└── .gitlab-ci.yml
```

## Ograniczenia przed użyciem produkcyjnym

- Brak market data feed, krzywych z collateral/basis, bid/ask i kalendarzy
  rynkowych.
- Brak autoryzacji, multi-tenancy, audytu użytkownika, trwałego przechowywania
  transakcji oraz kopii zapasowych.
- Brak CVA/DVA/FVA/MVA, płynności, margining, settlement risk, limitów
  kontrahenta i workflow akceptacji transakcji.
- Opcje: stała zmienność i europejski styl; brak smile i lokalnej/stochastycznej
  zmienności.
- Cross-hedge używa małego, syntetycznego zbioru; nie jest backtestem rynkowym.
- Wyniki nie są rekomendacją inwestycyjną, wyceną dealera ani oceną zgodności z
  rachunkowością zabezpieczeń IFRS 9.

Wdrożenie do rzeczywistego treasury wymaga przeglądu bezpieczeństwa, niezależnej
walidacji modeli, zatwierdzenia źródeł danych i konwencji, kontroli dostępu,
obserwowalności, odzyskiwania po awarii i formalnej akceptacji właściciela ryzyka.
