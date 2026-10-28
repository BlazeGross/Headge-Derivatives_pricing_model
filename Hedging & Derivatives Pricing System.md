# Hedging & Derivatives Pricing System
## Wycena instrumentów FX i towarowych oraz ocena strategii zabezpieczających

**Projekt analityczno-badawczy do portfolio zawodowego**

| Metryka | Informacja |
|---|---|
| Wersja | 1.0 |
| Data opracowania | 25 października 2026 r. |
| Obszar | Treasury, market risk, quantitative finance |
| Instrumenty | Forward FX, europejskie opcje FX, forward towarowy, swap towarowy fixed-for-floating |
| Perspektywa | Przedsiębiorstwo niefinansowe: importer waluty i nabywca surowca |
| Charakter danych | Wyłącznie jawne założenia i dane syntetyczne; bez bieżących kwotowań |
| Rezultat | Prototyp Streamlit, modele analityczne, testy, konfiguracja Docker/GitLab CI i metodologia |

> **Status projektu:** działający prototyp analityczny opisany w [README](./README.md), z wyceną FX i towarów, testami oraz konfiguracją Docker/GitLab CI. Nie jest to zweryfikowany system produkcyjny, transakcyjny ani księgowy. Wyniki liczbowe są demonstracją modeli przy wskazanych założeniach, nie empirycznym dowodem skuteczności na rynku. Dokument nie stanowi rekomendacji inwestycyjnej, wyceny transakcyjnej ani opinii księgowej.

---

## Streszczenie zarządcze

Celem projektu jest zaprojektowanie spójnego procesu, który łączy wycenę instrumentów pochodnych z decyzją o zabezpieczeniu rzeczywistej ekspozycji przedsiębiorstwa. Analiza nie kończy się na cenie instrumentu: obejmuje końcowy koszt zakupu, ryzyko rezydualne, premię, finansowanie i ograniczenia płynnościowe.

Projekt odpowiada na cztery pytania:

1. Jaka jest teoretyczna cena nowego kontraktu i bieżąca wartość już zawartej transakcji?
2. Jaką część ekspozycji zabezpieczyć oraz w jakim kierunku zawrzeć instrument?
3. Jak zmieniają się ryzyko, koszt i udział w korzystnym ruchu rynku?
4. Jak weryfikować wynik poza próbą estymacyjną i nie mylić skuteczności ekonomicznej z rachunkowością zabezpieczeń?

**Najważniejsze wyniki demonstracji:**

| Analiza | Wynik | Znaczenie biznesowe |
|---|---:|---|
| Forward EUR/PLN, 6 miesięcy | 4,354087 PLN/EUR | Przy nominale 1 mln EUR ustala koszt na 4 354 087,34 PLN |
| Call EUR/PLN, strike 4,35 | Premia 145 280,51 PLN | Finansowana premia wynosi w terminie 149 331,16 PLN |
| Maksymalny koszt waluty z call | 4 499 331,16 PLN | Pułap dotyczy dokładnie dopasowanego nominału i terminu, bez dodatkowych opłat |
| Swap towarowy, cztery dostawy | Cena stała 82,487500 USD/bbl | Ustala cenę benchmarku, ale nie usuwa automatycznie ryzyka walutowego ani basis risk |
| Cross-hedge: estymacja OLS | Hedge ratio 0,80 | Instrument benchmarkowy obejmuje 80% wolumenu ekspozycji przy zgodnych jednostkach |
| Redukcja wariancji poza próbą | 75,29% | Wynik jest słabszy niż 96,77% w próbie estymacyjnej |

**Wniosek:** nie istnieje jedna najlepsza strategia niezależna od celu. Forward służy pewności budżetu, zakupiona opcja ograniczeniu niekorzystnego kosztu przy zachowaniu korzyści ze spadku ceny, a częściowy hedge lub cross-hedge pozostawia świadomie część ryzyka. Zerowa premia początkowa nie oznacza braku kosztów ekonomicznych.

## Spis treści

1. [Cel i zakres](#1-cel-i-zakres)
2. [Problem biznesowy i pytania badawcze](#2-problem-biznesowy-i-pytania-badawcze)
3. [Dane, jednostki i konwencje](#3-dane-jednostki-i-konwencje)
4. [Metodologia wyceny](#4-metodologia-wyceny)
5. [Studium A: zabezpieczenie FX](#5-studium-a-zabezpieczenie-fx)
6. [Studium B: zakup surowca i swap](#6-studium-b-zakup-surowca-i-swap)
7. [Dobór hedge ratio](#7-dobór-hedge-ratio)
8. [Ocena skuteczności](#8-ocena-skuteczności)
9. [Koszt strategii i kryteria wyboru](#9-koszt-strategii-i-kryteria-wyboru)
10. [Łączne ryzyko FX i towarowe](#10-łączne-ryzyko-fx-i-towarowe)
11. [Specyfikacja projektowanego systemu](#11-specyfikacja-projektowanego-systemu)
12. [Walidacja i kontrola jakości](#12-walidacja-i-kontrola-jakości)
13. [Ograniczenia i dalsze badania](#13-ograniczenia-i-dalsze-badania)
14. [Wnioski i prezentacja w portfolio](#14-wnioski-i-prezentacja-w-portfolio)
15. [Bibliografia i źródła](#15-bibliografia-i-źródła)
16. [Załącznik: odtworzenie wyników](#16-załącznik-odtworzenie-wyników)

---

## 1. Cel i zakres

### Cel główny

Opracowanie metodyki wyceny i porównywania zabezpieczeń przepływów pieniężnych przedsiębiorstwa na rynku walutowym i towarowym.

### Zakres podstawowy

- Wycena forwardów FX przy wykorzystaniu parytetu stóp procentowych.
- Wycena europejskich opcji call i put FX modelem Garmana–Kohlhagena.
- Wycena forwardu na składowalny towar modelem kosztu przenoszenia.
- Wycena swapu towarowego przez dyskontowanie oczekiwanych przepływów z krzywej forward.
- Wyznaczenie nominalnego i minimalnowariancyjnego hedge ratio.
- Ocena skuteczności in-sample i out-of-sample na jawnym zbiorze syntetycznym.
- Porównanie kosztów zabezpieczenia oraz scenariuszowa analiza ryzyka.
- Projekt funkcjonalny systemu analitycznego i zestaw kontroli walidacyjnych.

### Poza zakresem

Opcje amerykańskie, azjatyckie i barierowe, IRS/FRA, swapy walutowe i cross-currency swaps, modele stochastycznych stóp, pełne CVA/DVA/FVA/MVA, zarządzanie księgą transakcyjną i automatyczne zawieranie transakcji. Swap towarowy jest odrębnym instrumentem od swapu FX. Termin „system” oznacza tu zaprojektowany proces analityczny, nie dostarczone oprogramowanie.

## 2. Problem biznesowy i pytania badawcze

Przedsiębiorstwo ma przyszłą płatność w EUR oraz zakupy surowca rozliczanego w USD. Wzrost kursu waluty lub ceny towaru może obniżyć marżę. Sama prognoza kierunku rynku nie wystarcza do kontroli tego ryzyka.

**Pytania badawcze:**

- Czy pełne zabezpieczenie forwardem daje stały koszt przy idealnym dopasowaniu kontraktu?
- Ile kosztuje zachowanie udziału w korzystnym ruchu kursu przez zakup opcji?
- Czy hedge ratio oszacowane historycznie redukuje wariancję również poza próbą?
- Które ryzyka pozostają po zastosowaniu swapu towarowego?

**Hipotezy:**

- H1: przy identycznym nominale, terminie i instrumencie bazowym forward eliminuje zmienność końcowego kosztu waluty, pomijając ryzyka niewykonania i rozliczenia.
- H2: kupiona opcja call ustanawia pułap kosztu zakupu, ale wymaga premii i pozostawia zmienność kosztu poniżej strike.
- H3: minimalnowariancyjne hedge ratio nie musi wynosić 1, a skuteczność poza próbą może być niższa niż w próbie estymacyjnej.
- H4: zabezpieczenie ceny surowca w USD nie usuwa ryzyka kosztu w PLN.

H1–H2 są weryfikowane algebraicznie i scenariuszowo. H3–H4 ilustrują eksperymenty syntetyczne; nie jest to test statystyczny na danych historycznych.

## 3. Dane, jednostki i konwencje

### 3.1. Notacja

| Symbol | Interpretacja | Jednostka |
|---|---|---|
| \(S_t\) | Kurs spot: waluta krajowa za jednostkę waluty zagranicznej | np. PLN/EUR |
| \(P_t\) | Cena fizycznego towaru | USD/bbl |
| \(F_{t,T}\) | Cena forward ustalana w chwili \(t\) na termin \(T\) | jak odpowiadający jej spot |
| \(K\) | Uzgodniony kurs lub cena wykonania | jak instrument bazowy |
| \(Q\) | Nominał waluty lub ilość towaru | EUR albo bbl |
| \(D_d(t,T)\), \(D_f(t,T)\) | Krajowy i zagraniczny czynnik dyskontowy | bez jednostki |
| \(r_d,r_f,r\) | Roczne stopy procentowe | zapis dziesiętny |
| \(\sigma\) | Roczna zmienność logarytmiczna FX | zapis dziesiętny |
| \(u,y\) | Proporcjonalny koszt składowania i convenience yield | rocznie |
| \(h\) | Ilość zabezpieczenia na jednostkę ekspozycji | zależnie od definicji danych |
| \(N(x)\), \(\phi(x)\) | Dystrybuanta i gęstość standardowego rozkładu normalnego | bez jednostki |

W całym opracowaniu stopy są kapitalizowane w sposób ciągły, a czasy podane w latach. W przykładach przyjęto dokładnie \(T=0{,}5\) lub terminy kwartalne; nie wyznaczano ich z dat kalendarzowych. W zastosowaniu rynkowym należy jawnie ustalić day count, daty spot i płatności, kalendarze oraz reguły przesuwania dni.

„EUR/PLN” jest tu oznaczeniem pary, a wartość liczbowa ma jednostkę **PLN za EUR**. Wzrost kursu oznacza wzrost kosztu importera. Dodatnie MtM i payoff oznaczają wartość lub wpływ dla analizowanej firmy.

### 3.2. Jakość i pochodzenie danych

Wszystkie parametry w studiach przypadków są założeniami dydaktycznymi. Zbiór [dane_cross_hedge.csv](./dane_cross_hedge.csv) zawiera 16 syntetycznych obserwacji zmian cen, nie historyczne notowania. Oznaczenia `train` i `test` odpowiadają kolejności eksperymentu, nie datom handlowym.

Dla badania empirycznego wymagane byłyby:

1. Kwotowania FX spot, forward points i krzywe dyskontowe zgodne z walutą collateral.
2. Powierzchnia zmienności FX z konwencją delta, strike i premium adjustment.
3. Krzywa forward benchmarku towarowego oraz ceny fizycznego zakupu tej samej jakości i lokalizacji.
4. Harmonogramy przepływów, wolumeny, waluty i dokumentacja kontraktów.
5. Bid/ask, prowizje, wymogi depozytowe i koszty finansowania.

Nie wolno zastępować cen fizycznych automatycznie seriami futures bez kontroli rolowania, terminów dostaw i jednostek. Interpolację czynników dyskontowych oraz krzywej forward należy określić i przetestować; w przykładach z płaskimi stopami nie jest ona potrzebna.

## 4. Metodologia wyceny

### 4.1. Forward FX

Przy braku basis i zgodnych założeniach finansowania kurs wynikający z covered interest parity wynosi [1]:

\[
F_{t,T}=S_t\frac{D_f(t,T)}{D_d(t,T)}
=S_te^{(r_d-r_f)(T-t)}.
\]

Jest to **kurs nowego kontraktu**, a nie wartość istniejącego forwardu. Dla kupna \(Q\) jednostek waluty zagranicznej po kursie \(K\):

\[
V_t=Q\left[S_tD_f(t,T)-KD_d(t,T)\right]
=QD_d(t,T)(F_{t,T}-K).
\]

W terminie payoff wynosi \(Q(S_T-K)\). Dla importera długie zabezpieczenie zyskuje przy wzroście kursu. Eksporter otrzymujący walutę zastosowałby pozycję przeciwną.

Nowy forward ma wartość modelową zero, gdy \(K=F_{t,T}\). Nie oznacza to braku limitu kredytowego, spreadu lub potencjalnych wymogów collateral. W praktyce kwotowania uwzględniają basis, płynność i umowę zabezpieczeń; prosty parytet jest punktem odniesienia, nie gwarancją kwotowania rynkowego.

### 4.2. Europejskie opcje FX: Garman–Kohlhagen

Model rozszerza wycenę Blacka–Scholesa o zagraniczną stopę procentową [2]. Dla \(\tau=T-t>0\):

\[
d_1=\frac{\ln(S_t/K)+(r_d-r_f+\tfrac12\sigma^2)\tau}
{\sigma\sqrt{\tau}},\qquad d_2=d_1-\sigma\sqrt{\tau}.
\]

\[
c=S_te^{-r_f\tau}N(d_1)-Ke^{-r_d\tau}N(d_2),
\]

\[
p=Ke^{-r_d\tau}N(-d_2)-S_te^{-r_f\tau}N(-d_1).
\]

Wartości \(c,p\) są wyrażone w walucie krajowej za jednostkę waluty zagranicznej. Premia całkowita to \(Qc\) lub \(Qp\).

Kontrola put–call parity:

\[
c-p=S_te^{-r_f\tau}-Ke^{-r_d\tau}.
\]

Wybrane miary wrażliwości dla jednej jednostki nominału:

\[
\Delta_c=e^{-r_f\tau}N(d_1),\qquad
\Delta_p=e^{-r_f\tau}(N(d_1)-1),
\]

\[
\Gamma=\frac{e^{-r_f\tau}\phi(d_1)}{S_t\sigma\sqrt{\tau}},\qquad
\text{Vega}=S_te^{-r_f\tau}\phi(d_1)\sqrt{\tau}.
\]

Vega powyżej dotyczy zmiany zmienności o 1,00, czyli 100 punktów procentowych; dla 1 punktu procentowego należy pomnożyć ją przez 0,01. Zastosowano spot delta bez korekty o premię.

Model zakłada europejskie wykonanie, lognormalny kurs, stałe stopy i zmienność oraz pomija koszty transakcyjne. Nie odwzorowuje smile i ryzyka skoków. Zakup call jest zabezpieczeniem importera; zakup put odpowiada ekspozycji eksportera.

### 4.3. Forward towarowy: koszt przenoszenia

Dla składowalnego towaru i proporcjonalnych rocznych kosztów [4]:

\[
F_{t,T}=P_te^{(r+u-y)(T-t)}.
\]

Koszt składowania \(u\) zwiększa cenę forward, a convenience yield \(y\), czyli korzyść z fizycznego posiadania zapasu, działa w przeciwnym kierunku.

Convenience yield nie jest zwykle bezpośrednio obserwowalny. Dla towarów konsumpcyjnych ograniczenia krótkiej sprzedaży, dostępność zapasów i sezonowość osłabiają prostą replikację. Model jest ilustracją ekonomiki carry; do wyceny kontraktu należy preferować obserwowaną krzywą forward. Dla energii elektrycznej model składowania nie jest właściwym modelem bazowym.

Dla istniejącego forwardu na kupno \(Q\) jednostek po \(K\), przy deterministycznym dyskontowaniu:

\[
V_t=QD(t,T)(F_{t,T}-K).
\]

Kontrakt futures i forward nie są zawsze równoważne: dzienne rozliczanie futures oraz korelacja ze stopami mogą powodować różnicę wyceny. Projekt nie modeluje tej korekty.

### 4.4. Swap towarowy fixed-for-floating

Firma kupująca surowiec płaci cenę stałą \(K\) i otrzymuje cenę zmienną benchmarku. Dla ilości \(Q_i\), dat \(T_i\) i cen forward \(F_i\):

\[
V_t=\sum_i Q_iD(t,T_i)(F_i-K),
\qquad
K^*=\frac{\sum_iQ_iD(t,T_i)F_i}{\sum_iQ_iD(t,T_i)}.
\]

To średnia cen forward ważona **ilością i dyskontem**, a nie zwykła średnia arytmetyczna. W tych wzorach \(Q_i\) jest ilością przypadającą na płatność; nie dodaje się mnożnika accrual właściwego np. dla kuponu IRS.

Payoff w okresie to \(Q_i(I_i-K)\), gdzie \(I_i\) jest umownym fixingiem. W przykładzie fixing jest pojedynczą obserwacją i płatność przypada na tę samą datę. W swapie opartym na średniej miesięcznej należy wycenić harmonogram fixingów, uwzględnić już ustalone obserwacje i datę opóźnionej płatności. Nie należy bezpośrednio podstawiać pojedynczego spotu zamiast średniej.

Jeżeli zakup fizyczny ma cenę \(I_i+b_i\), po swapie pozostaje koszt \(Q_i(K+b_i)\). Zmienny basis \(b_i\) nie znika.

## 5. Studium A: zabezpieczenie FX

### 5.1. Ekspozycja i parametry

Importer musi zapłacić **1 000 000 EUR za pół roku**. Całą analizę kosztów końcowych prowadzimy w PLN na datę płatności.

| Parametr | Wartość |
|---|---:|
| Spot \(S_0\) | 4,300000 PLN/EUR |
| Stopa PLN \(r_d\) | 5,50% |
| Stopa EUR \(r_f\) | 3,00% |
| Termin \(T\) | 0,50 roku |
| Zmienność \(\sigma\) | 12,00% rocznie |
| Strike call \(K_c\) | 4,350000 PLN/EUR |
| Nominał \(Q\) | 1 000 000 EUR |

Warianty: brak zabezpieczenia, 100% forward, 70% forward i 30% ekspozycji otwartej, 100% nominalnego pokrycia kupioną opcją call.

### 5.2. Wycena na początku

\[
F_0=4{,}30e^{(0{,}055-0{,}03)\cdot0{,}5}
=4{,}3540873416.
\]

Dla opcji:

| Wielkość | Wynik |
|---|---:|
| \(d_1\) | 0,0534947210 |
| \(d_2\) | −0,0313580927 |
| Call na 1 EUR | 0,1452805089 PLN |
| Put na 1 EUR, ten sam strike | 0,1413040378 PLN |
| Premia za call na 1 mln EUR | 145 280,51 PLN |
| Delta call | 0,5135695223 |

Premia jest płatna w \(t=0\). Dla porównania kosztów na wspólną datę zakładamy jej finansowanie stopą PLN równą \(r_d\):

\[
\Pi_T=145\,280{,}5089e^{0{,}055\cdot0{,}5}
=149\,331{,}16\text{ PLN}.
\]

To jawne uproszczenie: stopa finansowania przedsiębiorstwa może różnić się od krzywej dyskontowej. Przy innej stopie należy osobno przeliczyć \(\Pi_T\).

### 5.3. Porównanie końcowego kosztu

\[
\begin{aligned}
C_{\text{bez}}&=QS_T,\\
C_{\text{forward}}&=QF_0,\\
C_{\text{70\%}}&=Q[0{,}7F_0+0{,}3S_T],\\
C_{\text{call}}&=QS_T-Q(S_T-K_c)^++\Pi_T\\
&=Q\min(S_T,K_c)+\Pi_T.
\end{aligned}
\]

| Kurs za pół roku | Bez hedge | 100% forward | 70% forward | 100% call z finansowaniem premii |
|---|---:|---:|---:|---:|
| 3,90 PLN/EUR | 3 900 000,00 | 4 354 087,34 | 4 217 861,14 | 4 049 331,16 |
| 4,30 PLN/EUR | 4 300 000,00 | 4 354 087,34 | 4 337 861,14 | 4 449 331,16 |
| 4,80 PLN/EUR | 4 800 000,00 | 4 354 087,34 | 4 487 861,14 | 4 499 331,16 |

Wszystkie koszty w PLN. Tabela pomija spready, prowizje, podatki i niewykonanie kontraktu; nie jest porównaniem ofert bankowych.

**Interpretacja:**

- Forward eliminuje zmienność kosztu przy dokładnym dopasowaniu, ale zamyka korzyść ze spadku EUR/PLN.
- Call zapewnia pułap 4 499 331,16 PLN i zachowuje korzyść ze spadku kursu, pomniejszoną o finansowaną premię.
- Częściowy forward ogranicza ekspozycję liniową do 30%, ale nie daje bezwarunkowego pułapu kosztu.
- Wzrost stóp PLN względem EUR powoduje dodatnie punkty forward; nie są one tym samym co prowizja.
- „100% call” oznacza zgodność nominału, nie zerową deltę portfela. Początkowa wrażliwość kosztu zakupu pomniejszonego o wartość call to około \(Q(1-\Delta_c)=486\,430\) EUR ekwiwalentu spot; nominalny hedge i delta hedge rozwiązują inne zadania.

### 5.4. Wartość istniejącego forwardu po trzech miesiącach

Załóżmy \(S_t=4{,}50\), pozostały termin \(\tau=0{,}25\), niezmienione stopy i pierwotny kurs kontraktu \(K=4{,}3540873416\):

\[
V_t=1\,000\,000e^{-0{,}055\cdot0{,}25}
\left[4{,}50e^{(0{,}055-0{,}03)\cdot0{,}25}-K\right]
=171\,747{,}89\text{ PLN}.
\]

Jest to dodatnie MtM długiego forwardu dla importera. Nie jest to automatycznie otrzymana gotówka; wcześniejsze zamknięcie wymaga kwotowania unwind i może wiązać się ze spreadem.

## 6. Studium B: zakup surowca i swap

### 6.1. Forward towarowy

Zakup 10 000 bbl składowalnego surowca za pół roku:

| Parametr | Wartość |
|---|---:|
| Cena spot | 80,00 USD/bbl |
| Stopa USD | 4,00% |
| Koszt składowania \(u\) | 2,50% rocznie |
| Convenience yield \(y\) | 1,50% rocznie |
| Termin | 0,50 roku |

\[
F_0=80e^{(0{,}04+0{,}025-0{,}015)\cdot0{,}5}
=82{,}0252096420\text{ USD/bbl}.
\]

Koszt objęty forwardem wynosi **820 252,10 USD**. Jest to przykład modelu carry, a nie część poniższej niezależnie zadanej krzywej swapowej.

### 6.2. Swap: cztery kwartalne zakupy

Firma kupuje po 10 000 bbl w każdym kwartale. Przyjmujemy płaską stopę USD 4% i następującą **niezależną, hipotetyczną krzywą forward**:

| Termin w latach | Ilość w bbl | Forward w USD/bbl | Czynnik \(e^{-0,04T_i}\) |
|---|---:|---:|---:|
| 0,25 | 10 000 | 81,00 | 0,99004983 |
| 0,50 | 10 000 | 82,00 | 0,98019867 |
| 0,75 | 10 000 | 83,00 | 0,97044553 |
| 1,00 | 10 000 | 84,00 | 0,96078944 |

\[
K^*=\frac{\sum_i10\,000e^{-0{,}04T_i}F_i}
{\sum_i10\,000e^{-0{,}04T_i}}
=82{,}4875003542\text{ USD/bbl}.
\]

Przy tej cenie wartość początkowa swapu jest równa zero z dokładnością numeryczną. Założono brak opłaty początkowej i spreadu.

### 6.3. Koszt zakupu fizycznego i rozliczenie swapu

| Scenariusz | Fixingi w kolejnych kwartałach | Zakup fizyczny USD | Suma payoff swapu USD | Koszt netto USD |
|---|---|---:|---:|---:|
| Spadek | 75; 76; 77; 78 | 3 060 000,00 | −239 500,01 | 3 299 500,01 |
| Ścieżka bazowa | 81; 82; 83; 84 | 3 300 000,00 | 499,99 | 3 299 500,01 |
| Wzrost | 95; 96; 97; 98 | 3 860 000,00 | 560 499,99 | 3 299 500,01 |

Koszt netto = zakup fizyczny − payoff. Ujemny payoff oznacza płatność przedsiębiorstwa z tytułu swapu. Są to **sumy nominalnych przepływów z czterech dat**, nie ich wartość bieżąca ani wynik finansowany na koniec roku. Przy idealnym dopasowaniu w każdym kwartale koszt to \(10\,000K^*\); jego PV również jest identyczne w scenariuszach.

Niezerowy nominalny payoff na ścieżce bazowej jest prawidłowy: cena stała jest średnią dyskontowaną, nie arytmetyczną.

### 6.4. Wrażliwość wartości swapu

Przy natychmiastowym równoległym wzroście wszystkich forwardów o 5 USD/bbl, bez upływu czasu i zmiany dyskonta:

\[
\Delta V=\sum_i10\,000D_i\cdot5
=195\,074{,}17\text{ USD}.
\]

Płatnik stałej ceny zyskuje, ponieważ odbierana noga zmienna staje się droższa. Wielkość ta jest zmianą MtM, a nie sumą przyszłych nominalnych wypłat.

## 7. Dobór hedge ratio

### 7.1. Zabezpieczenie nominalne

Dla dokładnie dopasowanego forwardu:

\[
h_{\text{nom}}=\frac{Q_{\text{hedge}}}{Q_{\text{ekspozycji}}}.
\]

Wartość 1 oznacza pełne pokrycie nominału. Dla niepewnej ekspozycji ilościowej pełne zabezpieczenie prognozy może prowadzić do overhedgingu, gdy rzeczywisty zakup będzie mniejszy. Dlatego decyzja musi uwzględniać pewność przepływu, nie tylko historyczną korelację.

### 7.2. Minimalnowariancyjny cross-hedge

Niech \(Y=\Delta P\) oznacza zmianę ceny kupowanego towaru, a \(X=\Delta B\) zmianę ceny benchmarku zabezpieczającego. Obie zmiany mierzymy w USD/bbl i na tym samym horyzoncie.

Dla nabywcy surowca **długa pozycja benchmarkowa** przynosi dodatni wynik przy wzroście ceny. Rezydualny wzrost kosztu na jednostkę to:

\[
R(h)=Y-hX.
\]

Minimalizacja \(\operatorname{Var}(Y-hX)\) daje [3, 4]:

\[
h^*=\frac{\operatorname{Cov}(Y,X)}{\operatorname{Var}(X)}
=\rho_{Y,X}\frac{\sigma_Y}{\sigma_X}.
\]

To nachylenie regresji OLS:

\[
Y_t=\alpha+h^*X_t+\varepsilon_t.
\]

Wszystkie wariancje i kowariancje próby liczymy z mianownikiem \(n-1\). Stała \(\alpha\) opisuje średnią różnicę zmian; nie jest przepływem z zabezpieczenia. Do oceny kosztu używamy \(Y-hX\), a nie automatycznie reszt regresji po usunięciu stałej.

Jeżeli wykorzystuje się stopy zwrotu zamiast zmian cen, współczynnik ma inną interpretację: liczbę jednostek benchmarku należy przeliczyć przez ceny \(Q_B=h_{\text{return}}Q_PP_0/B_0\). Nie wolno przenosić współczynnika regresji zwrotów bezpośrednio na wolumeny.

### 7.3. Eksperyment na danych syntetycznych

W załączonym zbiorze pierwsze osiem obserwacji służy wyłącznie do estymacji, a ostatnie osiem do testu. Dane cenowe wygenerowano jawnie:

- `train`: \(X=(-4,-3,-2,-1,1,2,3,4)\), \(Y=0{,}8X+0{,}4(1,-1,-1,1,1,-1,-1,1)\).
- `test`: \(X=(-6,-3,-1,2,4,-2,1,5)\), \(Y=0{,}7X+0{,}6(2,-1,1,-2,1,-1,2,-2)\).

To celowo zaprojektowana zmiana zależności między próbkami, ilustrująca niestabilność hedge ratio. Obserwacje nie są ścieżką poziomów cen ani prognozą rozkładu.

Estymacja wyłącznie na `train`:

| Parametr | Wynik |
|---|---:|
| Wyraz wolny | 0,000000 |
| Hedge ratio OLS | 0,800000 |
| Korelacja | 0,983739 |

Dla ekspozycji 10 000 bbl oznacza to długie zabezpieczenie 8 000 bbl benchmarku, przed uwzględnieniem wielkości kontraktów i limitów. Gdy kontrakt obejmuje \(q_c\) bbl, liczba kontraktów wynosi \(h^*Q/q_c\); zaokrąglenie należy ocenić ponownie pod kątem ryzyka. Nie przyjmujemy specyfikacji rzeczywistego kontraktu giełdowego.

Współczynnik OLS jest rozwiązaniem bez ograniczeń. Jeżeli polityka dopuszcza tylko \(0\le h\le1\), należy rozwiązać problem ograniczony i zaraportować aktywny limit. Wartość ujemna lub ponad 1 nie może być bezrefleksyjnie uznana za zgodną z polityką hedgingową.

## 8. Ocena skuteczności

### 8.1. Redukcja wariancji

\[
HE=1-\frac{\operatorname{Var}(C_{\text{hedged}})}
{\operatorname{Var}(C_{\text{unhedged}})}.
\]

Dla eksperymentu cross-hedge podstawiamy \(C_{\text{unhedged}}=QY\) i \(C_{\text{hedged}}=Q(Y-hX)\). Ten sam stały wolumen \(Q\) skraca się w ilorazie.

| Próba | \(h\) stosowane w ocenie | Wariancja \(Y\) | Wariancja \(Y-hX\) | HE |
|---|---:|---:|---:|---:|
| Estymacyjna: 8 obserwacji | 0,80 | 5,668571 | 0,182857 | 96,77% |
| Testowa: 8 obserwacji | 0,80, bez ponownej estymacji | 5,828571 | 1,440000 | 75,29% |

Wariancje są w \((\text{USD/bbl})^2\). Spadek skuteczności między próbami wskazuje, że dobre dopasowanie historyczne nie gwarantuje takiej samej ochrony później.

Interpretacja: \(HE=1\) oznacza zerową wariancję rezydualną, \(HE=0\) brak jej redukcji, a \(HE<0\) zwiększenie ryzyka. Dla zerowej wariancji ekspozycji miara jest niezdefiniowana; system powinien wyświetlić ten stan, a nie zwracać 0% lub 100%.

Stała premia opcyjna może nie zmieniać wariancji kosztu na dany termin, lecz zmienia jego poziom i ogon rozkładu. Dlatego samo HE nie wystarcza do wyboru strategii.

### 8.2. Mierniki uzupełniające

- Odchylenie standardowe końcowego kosztu.
- Kwantyl kosztu \(q_{95\%}(C)\) oraz Expected Shortfall w najdroższych 5% scenariuszy.
- Cash Flow at Risk z jawną konwencją: \(CFaR_{95}=q_{95}(C)-C_{\text{budżet}}\). Ujemna wartość oznacza, że kwantyl mieści się poniżej budżetu.
- Prawdopodobieństwo przekroczenia budżetu \(P(C>C_{\text{budżet}})\).
- Największe zapotrzebowanie na gotówkę: premia, collateral, margin calls i finansowanie.
- Wrażliwości FX, towaru, zmienności i krzywych, raportowane w zgodnych jednostkach.

Powyższe miary poza HE są specyfikacją dalszego badania. Nie obliczono VaR, ES ani prawdopodobieństw na podstawie trzech scenariuszy FX lub ośmiu obserwacji testowych: taka próba nie uzasadnia wiarygodnej estymacji ogona.

### 8.3. Skuteczność ekonomiczna a IFRS 9

Redukcja wariancji nie jest samodzielnym potwierdzeniem kwalifikacji do rachunkowości zabezpieczeń. IFRS 9 wymaga m.in. formalnej dokumentacji relacji, ekonomicznego związku między pozycją i instrumentem, braku dominacji ryzyka kredytowego oraz hedge ratio odzwierciedlającego faktyczne ilości używane w zarządzaniu ryzykiem [5].

Nie stosujemy mechanicznie dawnego przedziału 80–125% jako kryterium IFRS 9. Wyznaczony współczynnik OLS nie jest automatycznie współczynnikiem do desygnacji księgowej. W tym projekcie nie przeprowadzono kwalifikacji rachunkowej ani wyceny zapisów OCI/P&L.

## 9. Koszt strategii i kryteria wyboru

### 9.1. Rozdzielenie kategorii kosztu

| Kategoria | Przykład | Sposób ujęcia |
|---|---|---|
| Premia | Zakup call | Osobny przepływ początkowy; kapitalizacja tylko do porównania na wspólną datę |
| Finansowanie | Odsetki od premii lub collateral | Faktyczna stopa firmy i okres finansowania |
| Wykonanie | Bid/ask, brokerage, prowizje | Kwotowanie po właściwej stronie rynku, bez ponownego doliczania tego samego spreadu |
| Carry | Różnica stóp, storage, convenience yield | Element wyceny forward, nie druga prowizja |
| Rozliczenia | Płatności swapu, margin calls | Rozdzielenie P&L od potrzeb płynnościowych |
| Utracona korzyść | Brak udziału w spadku kursu po forwardzie | Koszt alternatywny w danym scenariuszu, nie opłata gotówkowa z góry |
| Ryzyko niedopasowania | Basis, wolumen, termin | Ryzyko rezydualne i ewentualny koszt zamknięcia |

W konwencji kosztów końcowych:

\[
C_H(\omega)=C_{\text{zakupu}}(\omega)
-\Pi_{\text{instrumentu}}(\omega)
+\text{premia finansowana}
+\text{inne koszty na tę samą datę}.
\]

Tożsamość wymaga konsekwencji: jeśli instrument fizycznie dostarcza walutę, nie dodajemy jednocześnie pełnej płatności forward i zakupu całej tej waluty na spot. Zapis „spot minus payoff” jest równoważnym sposobem prezentacji ekonomicznej, nie dodatkową transakcją.

### 9.2. Wybór strategii zależy od mandatu

| Cel firmy | Strategia uzasadniona w modelu | Kompromis |
|---|---|---|
| Dokładny budżet walutowy przy pewnym nominale | 100% forward | Brak korzyści ze spadku kursu; możliwe collateral i koszty zamknięcia |
| Pułap kosztu i zachowanie korzystnego spadku | Kupiona call | Premia oraz koszt jej finansowania |
| Częściowa ochrona przy niepewnym przepływie | Częściowy forward, po analizie wolumenu | Rezydualne ryzyko kursowe |
| Ograniczenie ryzyka innego gatunku surowca | Cross-hedge benchmarkiem | Basis risk i niestabilność korelacji |
| Stała cena serii dostaw benchmarkowych | Swap fixed-for-floating | Zgodność fixingów i ilości; ryzyko FX pozostaje |

Nie wskazujemy „najtańszej strategii” na podstawie premii równej zero ani zwycięzcy ze średniej trzech arbitralnych scenariuszy.

### 9.3. Projekt problemu optymalizacji

Dla kosztów wyrażonych w jednej walucie i na wspólny termin można rozważyć:

\[
\min_{h,w}\ \mathbb{E}[C_H]+\lambda\operatorname{Var}(C_H),
\]

przy ograniczeniach:

\[
0\le h\le1,\quad w_j\ge0,\quad
\text{premia}_0\le B_{\text{premii}},\quad
P(C_H>B_{\text{budżetu}})\le\varepsilon.
\]

Wagi \(w\) określają pokrycie poszczególnymi instrumentami; dla tego samego przepływu suma nominalnego pokrycia musi respektować limit i nie może przypadkowo tworzyć nadzabezpieczenia. Parametr \(\lambda\) ma jednostkę odwrotną do waluty kosztu, aby składniki celu były wymiarowo zgodne.

Do rzeczywistej optymalizacji potrzebny jest rozkład scenariuszy pod miarą fizyczną i mandat ryzyka. Wycena instrumentów odbywa się pod miarą martyngałową; forward nie jest automatycznie prognozą oczekiwanego spotu. Ten projekt przedstawia problem, ale nie deklaruje znalezienia optimum mieszanego portfela.

## 10. Łączne ryzyko FX i towarowe

Koszt zakupu surowca w PLN:

\[
C_T=QP_TS_T,
\]

gdzie \(P_T\) jest ceną w USD/bbl, a \(S_T\) kursem w PLN/USD. Jest to inna para walutowa niż EUR/PLN ze studium A.

Dla niezmiennego wolumenu:

\[
\Delta C=Q(P_0\Delta S+S_0\Delta P+\Delta P\Delta S).
\]

Przykład stresowy: \(Q=10\,000\), \(P_0=80\), \(S_0=4{,}00\). Początkowy koszt wynosi 3 200 000 PLN. Przy \(P_T=100\) i \(S_T=4{,}40\) koszt rośnie do 4 400 000 PLN.

| Składnik wzrostu | Wartość PLN |
|---|---:|
| Sam ruch FX: \(QP_0\Delta S\) | 320 000 |
| Sam ruch towaru: \(QS_0\Delta P\) | 800 000 |
| Interakcja: \(Q\Delta P\Delta S\) | 80 000 |
| Łącznie | 1 200 000 |

Pominięcie składnika mieszanego zaniżyłoby wzrost kosztu o 80 000 PLN w tym stresie.

Jeżeli idealnie dopasowany swap ustala cenę USD na \(K\), koszt po jego rozliczeniu to \(QKS_T\). Pozostaje więc ryzyko walutowe. Przy jednoczesnym zabezpieczeniu FX kwota forwardu powinna odpowiadać **netto ustalonemu przepływowi USD**, a nie zostać automatycznie skopiowana z niepewnej wartości zakupu brutto.

W wielookresowym portfelu trzeba dopasować daty płatności za towar, rozliczeń swapu i zabezpieczeń walutowych. Nieznany basis, zmienny wolumen albo opóźnienie rozliczenia pozostawiają otwarte przepływy.

## 11. Prototyp systemu i odpowiedzialności modułów

W repozytorium znajduje się działający prototyp interfejsu Streamlit. Zawiera strony FX Pricing, Commodity Pricing i Cross Hedge oraz oddzielony od interfejsu moduł modeli Python. Instrukcje lokalnego uruchomienia, Docker Compose i pipeline GitLab opisano w [README](./README.md). Konfiguracja przygotowuje obraz do publikacji w GitLab Container Registry, ale nie konfiguruje sama runnera, reverse proxy, uwierzytelniania ani serwera użytkownika.

### 11.1. Proces analityczny

```text
Ekspozycje + harmonogramy + dane rynkowe + polityka ryzyka
                            |
                            v
       Walidacja jednostek, dat, kierunków i jakości danych
                            |
                            v
           Wycena instrumentów i przepływów netto
                            |
                            v
       Dobór hedge ratio i portfela zgodnego z limitami
                            |
                            v
       Scenariusze, backtest, ryzyko i koszt finansowania
                            |
                            v
         Raport decyzyjny + wersjonowany ślad audytowy
```

### 11.2. Moduły i odpowiedzialności

| Moduł | Wejście | Wyjście |
|---|---|---|
| Ekspozycje | Ilości, waluty, terminy, pewność przepływu | Harmonogram ryzyka brutto |
| Dane rynkowe | Spot, krzywe, zmienność, identyfikatory źródeł | Zweryfikowany snapshot |
| Pricing | Snapshot i definicje kontraktów | Cena nowego kontraktu, MtM, Greeks, przepływy |
| Hedge design | Ekspozycja, instrumenty, limity | Kierunek, nominał, hedge ratio, niedopasowania |
| Risk & backtest | Scenariusze, próby train/test | HE, koszt, naruszenia limitów, stress P&L |
| Raportowanie | Wyniki i metadane | Raport porównawczy i historia założeń |

### 11.3. Minimalny model danych

- **Exposure:** identyfikator, rodzaj zakupu/sprzedaży, waluta kosztu, ilość i jednostka, data lub profil płatności, benchmark i basis, stopień pewności.
- **Instrument:** typ, long/short, nominał, jednostka, waluty, strike/cena stała, daty fixingów i płatności, rodzaj rozliczenia.
- **MarketSnapshot:** czas obserwacji, źródło, spot, identyfikatory krzywych i konwencje, powierzchnia zmienności, bid/ask.
- **HedgePolicy:** cel, dopuszczalne instrumenty, limit pokrycia, budżet premii, limit płynności, reguły rebalancingu.
- **AnalysisResult:** identyfikator analizy, wersja modelu i danych, MtM, przepływy, miary ryzyka, ostrzeżenia i przyjęte ograniczenia.

### 11.4. Wymagania funkcjonalne i kryteria odbioru

| ID | Wymaganie | Kryterium odbioru przyszłej implementacji |
|---|---|---|
| F01 | Wycena forwardu FX | Poprawny kurs i MtM dla obu kierunków; zero MtM przy zawarciu po fair strike |
| F02 | Wycena call/put FX | Zgodność z parytetem i testami granicznymi; jawna jednostka premii |
| F03 | Swap towarowy | Cena ważona dyskontem i ilością; poprawne znaki dla obu stron |
| F04 | Hedge ratio | Estymacja tylko na train; raport nominalnego i statystycznego pokrycia |
| F05 | Ryzyko | HE i scenariusze netto obejmujące ekspozycję wraz z instrumentem |
| F06 | Koszt | Oddzielenie premii, finansowania, wykonania i kosztu alternatywnego |
| F07 | Walidacja | Odrzucenie niespójnych jednostek, brakujących fixingów i błędnych terminów z komunikatem |
| F08 | Audyt | Każdy wynik odtwarzalny ze snapshotu, wersji modelu i założeń |

Kontrole niefunkcjonalne: brak cichego zastępowania brakujących danych zerem, deterministyczne wyniki dla tych samych parametrów, spójne zaokrąglenia dopiero na etapie prezentacji, jawne błędy i rozdzielenie daty wyceny od daty pobrania danych. Prototyp nie łączy się z dostawcą danych rynkowych i nie przechowuje danych biznesowych.

## 12. Walidacja i kontrola jakości

### 12.1. Kontrole wykonane dla przykładów

Obliczenia sprawdzono niezależnym skryptem obliczeniowym w Pythonie 3, z funkcją normalnej dystrybuanty opartą na `erf` i bez dodatkowych pakietów. To kontrola numeryczna tego opracowania, nie testy wdrożonej aplikacji. Kwoty wyliczano na niezaokrąglonych parametrach.

| Kontrola | Oczekiwany rezultat | Wynik |
|---|---|---|
| Forward FX: MtM przy \(K=F_0\) | \(|V_0|<0,01\) PLN | Spełniony |
| Put–call parity | Błąd < \(10^{-5}\) PLN/EUR | Spełniony |
| Swap: MtM przy \(K=K^*\) | \(|V_0|<10^{-7}\) USD | Spełniony |
| Wzrost krzywej swapu o 5 USD | \(\Delta V=5\sum Q_iD_i\) | Spełniony |
| Forward FX: końcowy koszt | 4 354 087,34 PLN w każdym z trzech scenariuszy | Spełniony |
| Swap: końcowe koszty netto | 3 299 500,01 USD jako nominalna suma w każdym scenariuszu | Spełniony |
| OLS na train | \(|h-0,8|<10^{-12}\) | Spełniony |
| HE na train i test | Zgodność z definicją \(1-\text{Var}_H/\text{Var}_U\) | Spełniony |
| Rozkład ryzyka FX × towar | Suma składników = 1 200 000 PLN | Spełniony |

### 12.2. Kontrole wymagane przed implementacją produkcyjną

- Dla \(T=0\): payoff opcji równy wartości wewnętrznej i brak dzielenia przez zero.
- Dla \(\sigma=0\): wycena deterministyczna, bez stosowania wzoru z zerowym mianownikiem.
- Dla FX: dodatnie spot i strike, nieujemna zmienność, brak daty płatności przed wyceną.
- Ujemne stopy nie są automatycznie błędem; lognormalny model ceny towaru nie nadaje się natomiast do benchmarku dopuszczającego ceny ujemne bez zmiany modelu.
- Czynnik dyskontowy musi być dodatni; nie musi być mniejszy od 1 przy ujemnych stopach.
- Zmiana long na short odwraca MtM i payoff, ale nie zmienia fair strike.
- Przy braku wariancji benchmarku współczynnik OLS jest niezdefiniowany; wymagany komunikat, nie domyślne \(h=0\).
- Przy brakujących lub niesynchronizowanych danych backtest jest blokowany albo jawnie ograniczany, nigdy „uzupełniany” bez informacji.
- Kontrola cash-settled kontra physically-settled oraz fixing date kontra payment date.
- Porównanie z niezależną biblioteką lub kalkulatorem finansowym na większym zbiorze przypadków.

Kontrole wzorów, jednostek, warunków brzegowych oraz estymacji cross-hedge są objęte testami jednostkowymi w repozytorium. Testy nie zastępują niezależnej walidacji modelu, integracyjnego testu deploymentu ani testów na danych rynkowych.

## 13. Ograniczenia i dalsze badania

### Ograniczenia

1. Dane syntetyczne nie pozwalają deklarować historycznej skuteczności ani oczekiwanej rentowności.
2. Płaskie stopy, stała zmienność i brak basis upraszczają rzeczywistą wycenę.
3. Nie modelowano płynności, niewypłacalności kontrahenta, spreadów i podatków w liczbowych przykładach.
4. Redukcja wariancji nie musi oznaczać poprawy wyniku w każdym scenariuszu.
5. Mała próba cross-hedge nie uzasadnia wniosków o istotności statystycznej ani stabilności parametrów.
6. Niepewne wolumeny, terminy i ceny fizyczne mogą istotnie zmienić skuteczność.
7. Samo dodatnie MtM zabezpieczenia nie dowodzi sukcesu: trzeba oceniać łączny wynik ekspozycji i instrumentu.

### Plan badania empirycznego

1. Pozyskać licencjonowane, zsynchronizowane szeregi cen fizycznych i instrumentów zabezpieczających.
2. Ustalić ekonomicznie uzasadniony horyzont zmian oraz zasady budowy serii futures.
3. Zastosować chronologiczny podział danych i kroczącą estymację bez look-ahead bias.
4. Porównać \(h=0\), \(h=1\), stały OLS i kroczący OLS po kosztach.
5. Dodać stress testy korelacji, basis, wolumenu, zmienności i finansowania.
6. Oszacować przedziały niepewności HE, uwzględniając zależność czasową obserwacji.
7. Wprowadzić politykę rebalancingu i mierzyć obrót oraz koszty wykonania.
8. Dopiero po walidacji danych i modeli wdrożyć prototyp analityczny oraz niezależną kontrolę wyceny.

## 14. Wnioski i prezentacja w portfolio

**Wniosek finansowy:** właściwy hedge powinien wynikać z przepływu i celu ryzyka, a nie z poglądu na kierunek rynku. Należy oddzielać cenę instrumentu, wartość istniejącej pozycji, przepływy gotówkowe i koszt całej strategii.

**Wniosek ilościowy:** w demonstracji OLS daje \(h=0,80\), lecz redukcja wariancji spada z 96,77% do 75,29% poza próbą. Nawet dobre dopasowanie wymaga monitorowania.

**Wniosek operacyjny:** hedge towaru w USD i hedge FX trzeba projektować wspólnie, aby nie przeoczyć przepływów netto, interakcji i zapotrzebowania na płynność.

### Proponowany opis projektu do CV

> Opracowanie projektu analitycznego Hedging & Derivatives Pricing System dla ekspozycji walutowych i towarowych. Zastosowanie parytetu stóp procentowych, modelu Garmana–Kohlhagena i DCF swapu towarowego; porównanie kosztów zabezpieczeń, estymacja hedge ratio OLS oraz demonstracja walidacji out-of-sample na danych syntetycznych.

Opis celowo nie sugeruje wdrożenia aplikacji ani pracy na rzeczywistych portfelach.

### Proponowany przebieg prezentacji rekrutacyjnej: 7–10 minut

1. Ekspozycja importera i cel ochrony marży.
2. Różnica między fair forward rate i MtM.
3. Forward kontra call: pewność kosztu kontra premia i asymetria.
4. Swap towarowy i znaczenie dyskontowania.
5. Hedge ratio 0,80 oraz spadek HE poza próbą.
6. Ryzyka pozostające po hedge i plan przejścia do badania empirycznego.

## 15. Bibliografia i źródła

Źródła służą uzasadnieniu metod, nie dostarczeniu parametrów liczbowych do przykładów. Dostęp do materiałów internetowych: 25.10.2026. Nie cytowano obszernych fragmentów publikacji.

1. Borio, C., McCauley, R., McGuire, P., Sushko, V. (2016), *Covered interest parity lost: understanding the cross-currency basis*, BIS Quarterly Review, September. [BIS](https://www.bis.org/publ/qtrpdf/r_qt1609e.htm). Parzystość stóp, mechanika FX swaps i ograniczenia arbitrażu.
2. Garman, M. B., Kohlhagen, S. W. (1983), *Foreign currency option values*, Journal of International Money and Finance, 2(3), 231–237. [DOI: 10.1016/S0261-5606(83)80001-1](https://doi.org/10.1016/S0261-5606(83)80001-1). Model europejskich opcji walutowych.
3. Ederington, L. H. (1979), *The Hedging Performance of the New Futures Markets*, The Journal of Finance, 34(1), 157–170. [DOI: 10.2307/2327150](https://doi.org/10.2307/2327150). Klasyczna literatura pomiaru skuteczności zabezpieczenia.
4. Hull, J. C., *Options, Futures, and Other Derivatives*, Pearson, wydania podręcznika. Rozdziały dotyczące strategii zabezpieczających z futures, ustalania cen forward/futures, swapów i opcji walutowych. Numeracja rozdziałów zależy od wydania; wzory w opracowaniu przedstawiono samodzielnie.
5. IFRS Foundation, *IFRS 9 Financial Instruments*, sekcja 6, w szczególności 6.4.1 i wskazówki B6.4. [Strona standardu](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/). Wymogi rachunkowości zabezpieczeń należy analizować w pełnym tekście standardu; dostęp może wymagać konta.

## 16. Załącznik: odtworzenie wyników

### Dane i kolejność obliczeń

1. Odczytać parametry studium A; wszystkie stopy podzielić przez 100.
2. Wyznaczyć \(F_0\), \(d_1,d_2\), call i put. Dystrybuantę można obliczyć jako \(N(x)=\tfrac12[1+\operatorname{erf}(x/\sqrt2)]\).
3. Premię całkowitą pomnożyć przez \(e^{r_dT}\) i zastosować formuły kosztów do trzech kursów końcowych.
4. Wycenić istniejący forward przy pozostałym terminie 0,25 roku; nie wyznaczać ponownie pierwotnego strike.
5. Dla forwardu towarowego zsumować carry: \(0,04+0,025-0,015=0,05\).
6. Dla swapu zastosować osobną zadaną krzywą, wyznaczyć dyskonta i średnią ważoną \(K^*\).
7. W [dane_cross_hedge.csv](./dane_cross_hedge.csv) użyć tylko `train` do OLS z wyrazem wolnym; następnie zamrozić \(h=0,80\).
8. Osobno w obu próbach obliczyć wariancję \(\Delta P\) i \(\Delta P-0,8\Delta B\), zawsze z mianownikiem \(n-1\).
9. Obliczyć HE, nie mieszając prób i nie ponawiając estymacji na `test`.

### Specyfikacja pliku danych

| Kolumna | Znaczenie |
|---|---|
| `observation_id` | Kolejność obserwacji eksperymentu, bez interpretacji kalendarzowej |
| `sample` | `train` albo `test` |
| `benchmark_change_usd_per_bbl` | \(X\): zmiana ceny benchmarku |
| `physical_change_usd_per_bbl` | \(Y\): zmiana ceny kupowanego towaru |

Separator CSV: przecinek; separator dziesiętny: kropka. Wiersze nie zawierają poziomów cen ani wyników rzeczywistych transakcji.

### Zasady prezentacji

- Obliczenia na pełnej precyzji; kwoty pieniężne prezentowane do dwóch miejsc.
- Kursy i ceny jednostkowe można prezentować z większą precyzją, aby umożliwić odtworzenie.
- Brakujące źródło, błędna jednostka lub niedostępny parametr wymagają jawnej informacji.
- Obliczenia teoretyczne, scenariusze i wyniki empiryczne muszą pozostawać wyraźnie rozdzielone.
