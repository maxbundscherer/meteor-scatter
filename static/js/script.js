let slideIndex = 0;
let slideshowIntervalId = null; // Für die automatische Slideshow
let isPaused = false; // Status für Start/Pause

// ------------------- Reload Intervall -------------------
// Setzt das dynamische Reload-Intervall (wird aus dem HTML übertragen)
const reloadInterval = typeof RELOAD_INTERVAL !== 'undefined' ? RELOAD_INTERVAL : 60000; // Fallback auf 5000 ms

// ------------------- Charts laden -------------------
function ladeChart(chartId, chartType) {

    let base_url_fetcher = `${SCRIPT_ROOT}`;

    const url = `${base_url_fetcher}/load_chart/${chartType}`; // Dynamische URL passend zum Typ

    // API-Aufruf
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP-Fehler! Status: ${response.status}`);
            }
            return response.json(); // JSON-Daten parsen
        })
        .then(data => {
            // Stellen Sie sicher, dass die Antwort eine URL enthält
            if (data.img_url) {
                const imgElement = document.getElementById(chartId);
                if (imgElement) {
                    imgElement.src = `${data.img_url}?t=${new Date().getTime()}`; // Direkt die Bild-URL setzen
                    console.log(`Chart erfolgreich aktualisiert für: ${chartId}`);
                } else {
                    console.error(`Fehler: Kein Element mit ID '${chartId}' gefunden.`);
                }
            } else {
                console.error(`Fehlende img_url für '${chartId}' in der Antwort.`);
            }
        })
        .catch(error => {
            console.error(`Fehler beim Laden von '${chartId}' mit Typ '${chartType}':`, error);
        });
}

// Funktion, um alle Charts regelmäßig zu laden
function ladeAlleCharts() {
    ladeChart('zeiger-chart', 'zeiger');          // Zeiger-Chart laden
    ladeChart('tagesverlauf-chart', 'tagesverlauf'); // Tagesverlauf-Chart laden
    ladeChart('week-chart', 'week');             // Wochen-Charts laden
    ladeChart('month-chart', 'month');           // Monats-Charts laden
}

// ------------------- Dynamischer Inhalt und Charts aktualisieren -------------------
async function aktualisiereDynamischenInhalt() {
    console.log("Dynamische Inhalte und Charts werden aktualisiert...");

    try {

        let base_url_fetcher = `${SCRIPT_ROOT}`;

        const url = `${base_url_fetcher}/api/dynamischer_inhalt`; // API-URL für das Intervall

        // API-Aufruf zur Abfrage der fehlenden Tage
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`API-Fehler dynamischer Inhalt: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Erhaltene dynamische Inhalte:", data.missing_days);

        // Aktualisiere die Anzeige der missing_days
        updateMissingDays(data.missing_days);

    } catch (error) {
        console.error("Fehler beim Abrufen dynamischer Inhalte:", error);
    }

    // Aktualisiere zusätzlich alle Charts
    ladeAlleCharts();
}

// Funktion zur Anzeige von "missing_days" auf der Website
function updateMissingDays(missingDays) {
    const missingDaysElement = document.getElementById('missing-days');
    if (!missingDaysElement) {
        console.error("Element mit ID 'missing-days' wurde nicht gefunden!");
        return;
    }

    // Dynamisch die fehlenden Tage anzeigen
    if (missingDays && missingDays.length > 0) {
        missingDaysElement.innerHTML = `Fehlende Tage: ${missingDays.join(', ')}`;
    } else {
        missingDaysElement.innerHTML = 'Keine fehlenden Tage!';
    }
}

// Periodisch dynamische Inhalte (Missing Days und Charts) laden
setInterval(aktualisiereDynamischenInhalt, reloadInterval);


// ------------------- Slideshow Funktionen -------------------
function showSlides(n) {
    const slides = document.getElementsByClassName("mySlides");
    const dots = document.getElementsByClassName("dot");

    if (n >= slides.length) slideIndex = 0; // Zurück zur ersten Folie
    if (n < 0) slideIndex = slides.length - 1; // Zurück zur letzten Folie

    // Alle Folien ausblenden
    for (let slide of slides) {
        slide.style.display = "none";
    }

    // Alle Punkte inaktiv setzen
    for (let dot of dots) {
        dot.className = dot.className.replace(" active", "");
    }

    // Aktuelle Folie anzeigen und den entsprechenden Punkt aktivieren
    slides[slideIndex].style.display = "block";
    if (dots[slideIndex]) {
        dots[slideIndex].className += " active";
    }
}

function nextSlide() {
    showSlides(slideIndex += 1); // Zur nächsten Folie
}

function prevSlide() {
    showSlides(slideIndex -= 1); // Zur vorherigen Folie
}

function startSlideshow(interval) {
    stopSlideshow(); // Verhindere doppelte Intervalle
    slideshowIntervalId = setInterval(nextSlide, interval);
    console.log(`Slideshow gestartet mit einem Intervall von ${interval} Millisekunden.`);
}

function stopSlideshow() {
    if (slideshowIntervalId) {
        clearInterval(slideshowIntervalId);
        slideshowIntervalId = null;
        console.log("Slideshow gestoppt.");
    }
}

function toggleSlideshow() {
    const toggleButton = document.getElementById("toggleSlide");

    if (isPaused) {
        loadConfigAndStartSlide(); // Hole das dynamische Intervall (API)
        toggleButton.innerText = "Pause"; // Button-Text zu "Pause" ändern
        isPaused = false;
    } else {
        stopSlideshow(); // Slideshow stoppen
        toggleButton.innerText = "Start"; // Button-Text zu "Start" ändern
        isPaused = true;
    }
}


// ------------------- Dynamisches Intervall (API-Aufruf) -------------------
function loadConfigAndStartSlide() {

    let base_url_fetcher = `${SCRIPT_ROOT}`;

    const url = `${base_url_fetcher}/config/slideshow_interval`; // API-URL für das Intervall

    // Hole die Konfiguration von der Flask-API
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP-Fehler! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Konvertiere das Intervall aus der API (String zu Zahl)
            const slideshow_interval = Number(data.slideshow_interval) || 7000;
            console.log(`Slideshow-Intervall von der API geladen: ${slideshow_interval} Millisekunden.`);
            startSlideshow(slideshow_interval); // Starte die Slideshow mit dem dynamischen Intervall
        })
        .catch(error => {
            console.error('Fehler beim Laden der Konfiguration:', error);
            startSlideshow(7000); // Fallback auf 7000ms, falls die API nicht erreichbar ist
        });
}

// ------------------- Button-Event-Listener hinzufügen -------------------
function setupButtonListeners() {
    const btnPrev = document.getElementById("prevSlide");
    const btnNext = document.getElementById("nextSlide");
    const btnToggle = document.getElementById("toggleSlide");

    if (btnPrev) btnPrev.addEventListener("click", prevSlide);
    if (btnNext) btnNext.addEventListener("click", nextSlide);
    if (btnToggle) btnToggle.addEventListener("click", toggleSlideshow);
}

// ------------------- Uhrzeit-Aktualisierung -------------------
function updateClock() {
    const now = new Date();
    const date = now.toLocaleDateString("de-DE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    });

    const time = now.toLocaleTimeString("de-DE", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });

    // Aktuelle Uhrzeit im definierten Bereich anzeigen
    document.getElementById("clock").innerText = `${date} - ${time}`;
}

// Aktualisiere die Uhrzeit jede Sekunde
setInterval(updateClock, 1000);

// ------------------- Initialisierung -------------------
window.onload = function () {
    console.log("Initialisierung gestartet...");

    loadConfigAndStartSlide();


    // Event-Listener für Buttons setzen
    setupButtonListeners();


    // Dynamische Inhalte und Charts initial laden
    aktualisiereDynamischenInhalt();

    // Slideshow starten
    showSlides(slideIndex);
    // autoSlide(slideshow_interval);

    // Uhrzeit starten
    updateClock();
};