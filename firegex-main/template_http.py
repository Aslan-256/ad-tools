# =============================================================================
# FIREGEX — Template pyfilter per A/D CTF
# Modifica le sezioni marcate con [EDIT] in base al servizio da proteggere
# Testa con: fgex nfproxy filter_template.py 127.0.0.1 <porta> --proto http
# =============================================================================

from firegex.nfproxy import (
    pyfilter, ACCEPT, REJECT, DROP, UNSTABLE_MANGLE,
    FullStreamAction, ExceptionAction
)
from firegex.nfproxy.models import (
    RawPacket,
    TCPInputStream, TCPOutputStream,
    HttpRequest, HttpFullRequest,
    HttpResponse, HttpFullResponse,
)
import re

# =============================================================================
# CONFIGURAZIONE GLOBALE DEL FLUSSO
# Questi valori valgono per ogni flow (TCP stream) in modo indipendente
# =============================================================================

# [EDIT] Limite massimo per lo stream (default 1MB).
# Abbassalo se il servizio non ha bisogno di body grandi.
FGEX_STREAM_MAX_SIZE = 512 * 1024  # 512 KB

# Cosa fare se lo stream supera il limite:
# FLUSH = continua, DROP = droppare, REJECT = chiudi connessione, ACCEPT = lascia passare
FGEX_FULL_STREAM_ACTION = FullStreamAction.REJECT

# Cosa fare se il parser crasha (encoding invalido, ecc.)
FGEX_INVALID_ENCODING_ACTION = ExceptionAction.REJECT


# =============================================================================
# BLOCKLIST — parole/pattern vietati nel body delle request
# [EDIT] Aggiungi qui le stringhe tipiche dei payload di exploit
# =============================================================================

# Stringhe letterali bloccate (case-sensitive di default)
BANNED_STRINGS: list[bytes] = [
    # b"../",             # Path traversal
    # b"<script",        # XSS base
    # b"UNION SELECT",   # SQLi base
    # b"__import__",     # Python injection
    # b"/etc/passwd",    # LFI classica
]

# Regex bloccate (compilate una sola volta al caricamento del modulo)
BANNED_PATTERNS: list[re.Pattern] = [
    # re.compile(rb"(?i)union\s+select"),            # SQLi case-insensitive
    # re.compile(rb"\.\./+"),                        # Path traversal varianti
    # re.compile(rb"<script[\s>]", re.IGNORECASE),   # XSS
    # re.compile(rb"0x[0-9a-fA-F]{10,}"),            # Shell hex encoding
]

# =============================================================================
# ALLOWLIST — endpoint leciti (se la tua app ha pochi endpoint noti)
# [EDIT] Decommenta e popola se vuoi una allowlist di URL
# =============================================================================

# ALLOWED_PATHS: list[str] = [
#     "/",
#     "/login",
#     "/flag",
#     "/api/data",
# ]

# =============================================================================
# FILTRI TCP RAW — livello più basso, chiamato ad ogni pacchetto
# Utile per protocolli non-HTTP o per bloccare pattern a basso livello
# =============================================================================

@pyfilter
def raw_block_banned(packet: RawPacket) -> int:
    """Blocca payload TCP che contengono stringhe vietate."""
    for s in BANNED_STRINGS:
        if s in packet.data:
            return REJECT
    for pattern in BANNED_PATTERNS:
        if pattern.search(packet.data):
            return REJECT
    return ACCEPT


# =============================================================================
# FILTRI TCP STREAM — accumulano l'intero stream di input
# Utile quando il payload è spalmato su più pacchetti
# =============================================================================

@pyfilter
def stream_size_guard(stream: TCPInputStream) -> int:
    """Rigetta connessioni con stream in ingresso esageratamente grandi."""
    # [EDIT] Setta la soglia in byte ragionevole per il tuo servizio
    if stream.total_stream_size > 1 * 1024 * 1024:  # 1 MB
        return REJECT
    return ACCEPT


# =============================================================================
# FILTRI HTTP REQUEST — header già parsati, body può essere None
# Il filtro viene chiamato anche quando il body non è ancora arrivato:
# controlla sempre http_request.body is not None prima di usarlo
# =============================================================================

@pyfilter
def http_method_guard(req: HttpRequest) -> int:
    """Blocca metodi HTTP non attesi dal servizio."""
    # [EDIT] Lascia solo i metodi che il tuo servizio usa davvero
    ALLOWED_METHODS = {"GET", "POST"}
    if req.method not in ALLOWED_METHODS:
        return REJECT
    return ACCEPT


@pyfilter
def http_header_guard(req: HttpRequest) -> int:
    """Controlla header sospetti (Content-Type fuori posto, header injection)."""
    ct = req.get_header("content-type", "")

    # [EDIT] Blocca Content-Type non attesi se il servizio è solo JSON o solo form
    # if req.method == "POST" and "application/json" not in ct:
    #     return REJECT

    # Blocca header injection di base (valore contiene \r o \n)
    for val in req.headers.values():
        vals = val if isinstance(val, list) else [val]
        for v in vals:
            if "\r" in v or "\n" in v:
                return REJECT
    return ACCEPT


@pyfilter
def http_url_guard(req: HttpRequest) -> int:
    """Blocca URL con pattern pericolosi o non in allowlist."""
    url = req.url

    # Path traversal nell'URL
    if "../" in url or "%2e%2e" in url.lower():
        return REJECT

    # [EDIT] Decommenta per usare la allowlist di URL
    # path = url.split("?")[0]
    # if path not in ALLOWED_PATHS:
    #     return REJECT

    return ACCEPT


# =============================================================================
# FILTRI HTTP FULL REQUEST — body completamente arrivato
# Usa HttpFullRequest quando hai bisogno del body completo per decidere
# =============================================================================

@pyfilter
def http_body_guard(req: HttpFullRequest) -> int:
    """Analizza il body completo della request."""
    body = req.body_decoded  # usa la versione decodificata (gzip/br/ecc.)
    if body is None or body is False:
        return ACCEPT  # body vuoto o errore di decode: lascia passare

    # Stringhe vietate nel body
    for s in BANNED_STRINGS:
        if s in body:
            return REJECT

    # Pattern regex nel body
    for pattern in BANNED_PATTERNS:
        if pattern.search(body):
            return REJECT

    # [EDIT] Logica personalizzata — esempio: blocca body JSON con chiave "admin"
    # import json
    # try:
    #     data = json.loads(body)
    #     if data.get("role") == "admin":
    #         return REJECT
    # except Exception:
    #     pass

    return ACCEPT


# =============================================================================
# FILTRI HTTP RESPONSE — proteggi l'output del servizio
# Utile per censurare flag o dati sensibili nelle risposte (patchless patching)
# =============================================================================

@pyfilter
def http_response_flag_guard(resp: HttpFullResponse) -> int:
    """Blocca risposte che contengono la flag (protezione patchless)."""
    body = resp.body_decoded
    if body is None or body is False:
        return ACCEPT

    # [EDIT] Adatta il pattern al formato flag della gara, es: CTF{...}, FLAG{...}
    FLAG_PATTERN = re.compile(rb"[A-Z0-9]{31}=")  # base64-like, 32 char

    if FLAG_PATTERN.search(body):
        # Non fare REJECT qui (romperesti il servizio legittimo),
        # considera DROP o torna ACCEPT se non sei sicura
        # In gara valuta caso per caso
        return REJECT  # [EDIT] cambia se rompe il servizio legittimo

    return ACCEPT


# =============================================================================
# MANGLE — modifica pacchetti al volo (instabile, usa con cautela)
# Disponibile solo su RawPacket. Utile per sanitizzare input.
# =============================================================================

# @pyfilter
# def http_mangle_example(packet: RawPacket) -> int:
#     """Esempio: sostituisce una stringa pericolosa con una innocua."""
#     if b"DANGEROUS" in packet.l4_data:
#         packet.l4_data = packet.l4_data.replace(b"DANGEROUS", b"XXXXXXXXX")
#         return UNSTABLE_MANGLE
#     return ACCEPT