# =============================================================================
# FIREGEX — Template pyfilter TCP RAW per A/D CTF
# Per servizi binari, netcat-like, custom protocol, ecc.
# Testa con: fgex nfproxy filter_tcp_template.py 127.0.0.1 <porta> --proto tcp
# =============================================================================

from firegex.nfproxy import (
    pyfilter, ACCEPT, REJECT, DROP, UNSTABLE_MANGLE,
    FullStreamAction, ExceptionAction
)
from firegex.nfproxy.models import (
    RawPacket,
    TCPInputStream,   # alias: TCPClientStream  — solo pacchetti client → server
    TCPOutputStream,  # alias: TCPServerStream  — solo pacchetti server → client
)
import re
import struct

# =============================================================================
# CONFIGURAZIONE GLOBALE DEL FLUSSO
# =============================================================================

# [EDIT] Dimensione massima dello stream accumulato (per direzione)
FGEX_STREAM_MAX_SIZE = 256 * 1024  # 256 KB — abbassa per servizi semplici

# Cosa fare se il limite viene superato
FGEX_FULL_STREAM_ACTION = FullStreamAction.REJECT


# =============================================================================
# STATO DEL FLOW (globals per connessione)
# Ogni connessione TCP ha il suo spazio globale isolato.
# Puoi usare variabili globali per tenere stato tra un pacchetto e l'altro
# dello stesso stream, senza rischi di race condition tra flow diversi.
# =============================================================================

# Esempi di stato che potresti voler tracciare:
_packet_count = 0          # quanti pacchetti ha mandato il client
_authenticated = False     # il client ha completato il login?
_phase = "init"            # fase del protocollo custom


# =============================================================================
# BLOCKLIST — pattern vietati (adattali agli exploit che vedi in gara)
# =============================================================================

BANNED_BYTES: list[bytes] = [
    # b"\x00" * 100,       # NOP sled / padding flood
    # b"/etc/passwd",      # LFI
    # b"../",              # path traversal
    # b"__import__",       # Python injection
    # b";/bin/sh",         # command injection
    # b"\x90" * 20,        # NOP sled shellcode
]

BANNED_PATTERNS: list[re.Pattern] = [
    # re.compile(rb"\.\./+"),                        # path traversal varianti
    # re.compile(rb"(?i)sh\s*-[ic]"),                # shell invocation
    # re.compile(rb"[\x00-\x08\x0e-\x1f]{10,}"),    # burst di byte di controllo
    # re.compile(rb"/proc/self"),                    # info leak Linux
]


# =============================================================================
# FILTRO 1 — RawPacket
# Chiamato ad ogni singolo pacchetto (anche frammentato).
# Usa packet.data (stream riassemblato da libtins) o
# packet.l4_data (payload grezzo del pacchetto nfqueue, modificabile).
# =============================================================================

@pyfilter
def raw_packet_guard(packet: RawPacket) -> int:
    """
    Blocca pacchetti con payload pericolosi a livello di singolo pacchetto.
    Usa packet.data per la visione stream-assembled (read-only),
    packet.l4_data per il payload grezzo (modificabile con UNSTABLE_MANGLE).
    """
    global _packet_count
    _packet_count += 1

    # [EDIT] Blocca se il client manda troppi pacchetti (flood/fuzzing)
    # if _packet_count > 1000:
    #     return REJECT

    # Stringhe vietate nel payload del singolo pacchetto
    for pattern in BANNED_BYTES:
        if pattern in packet.data:
            return REJECT

    for pattern in BANNED_PATTERNS:
        if pattern.search(packet.data):
            return REJECT

    return ACCEPT


# =============================================================================
# FILTRO 2 — TCPInputStream (client → server)
# Accumula l'intero stream in ingresso.
# Chiamato ad ogni pacchetto in entrata: stream.data cresce nel tempo.
# Utile quando il payload exploit è spalmato su più pacchetti.
# =============================================================================

@pyfilter
def input_stream_guard(stream: TCPInputStream) -> int:
    """
    Analizza lo stream cumulativo inviato dal client.
    stream.data contiene tutto ciò che il client ha mandato finora.
    """
    data = stream.data

    # Stringhe vietate nello stream accumulato
    for pattern in BANNED_BYTES:
        if pattern in data:
            return REJECT

    for pattern in BANNED_PATTERNS:
        if pattern.search(data):
            return REJECT

    # [EDIT] Esempio: protocollo custom con magic byte obbligatorio
    # Se il primo pacchetto non inizia col magic byte atteso → rigetta
    # MAGIC = b"\xde\xad\xbe\xef"
    # if len(data) >= 4 and data[:4] != MAGIC:
    #     return REJECT

    # [EDIT] Esempio: limita la lunghezza di un singolo "comando" nel protocollo
    # Utile se il server legge linee (es: \n-terminated commands)
    # for line in data.split(b"\n"):
    #     if len(line) > 512:
    #         return REJECT

    return ACCEPT


# =============================================================================
# FILTRO 3 — TCPOutputStream (server → client)
# Accumula l'intero stream in uscita dal server.
# Utile per censurare flag o dati sensibili nella risposta.
# =============================================================================

@pyfilter
def output_stream_guard(stream: TCPOutputStream) -> int:
    """
    Analizza lo stream cumulativo inviato dal server al client.
    Utile per intercettare flag leak nelle risposte.
    """
    data = stream.data

    # [EDIT] Adatta il pattern al formato flag della gara
    FLAG_PATTERN = re.compile(rb"[A-Z0-9]{31}=")  # esempio: base64-like 32 char

    if FLAG_PATTERN.search(data):
        # ATTENZIONE: REJECT qui chiude la connessione.
        # Valuta se il servizio legittimo restituisce mai questo pattern.
        return REJECT  # [EDIT] considera DROP se REJECT rompe la logica del servizio

    return ACCEPT


# =============================================================================
# FILTRO 4 — Protezione protocollo binary strutturato
# Esempio: protocollo con header fisso (tipo TLV, lunghezza + tipo + payload)
# [EDIT] Adatta la struttura al protocollo del servizio in gara
# =============================================================================

# Struttura esempio: [ magic: 2B ][ type: 1B ][ length: 2B ][ payload: Nb ]
PROTO_MAGIC = b"\xca\xfe"
PROTO_MAX_PAYLOAD = 4096
PROTO_VALID_TYPES = {0x01, 0x02, 0x03}  # [EDIT] tipi di messaggio validi

@pyfilter
def binary_protocol_guard(stream: TCPInputStream) -> int:
    """
    Valida un protocollo binario strutturato.
    Attiva solo se il tuo servizio usa un formato binario custom.
    Decommenta e adatta la struttura al protocollo reale.
    """
    # data = stream.data
    # if len(data) < 5:
    #     return ACCEPT  # header non ancora arrivato, aspetta
    #
    # magic   = data[0:2]
    # pkt_type = data[2]
    # length  = struct.unpack(">H", data[3:5])[0]
    #
    # if magic != PROTO_MAGIC:
    #     return REJECT
    # if pkt_type not in PROTO_VALID_TYPES:
    #     return REJECT
    # if length > PROTO_MAX_PAYLOAD:
    #     return REJECT

    return ACCEPT


# =============================================================================
# FILTRO 5 — Rate limiting per connessione
# Blocca client che mandano dati troppo velocemente (fuzzer, exploit loop)
# =============================================================================

_stream_high_water = 0  # byte già visti all'ultima chiamata

@pyfilter
def rate_limit_guard(stream: TCPInputStream) -> int:
    """
    Blocca se in un singolo burst arrivano troppi dati.
    Non è un rate limit temporale reale (non abbiamo accesso al clock qui),
    ma limita la quantità di dati nuovi per ogni chiamata al filtro.
    """
    global _stream_high_water

    new_bytes = stream.total_stream_size - _stream_high_water
    _stream_high_water = stream.total_stream_size

    # [EDIT] soglia: quanti byte nuovi per pacchetto sono accettabili?
    MAX_BURST = 8192  # 8 KB per "chunk"
    if new_bytes > MAX_BURST:
        return REJECT

    return ACCEPT


# =============================================================================
# MANGLE — modifica il payload al volo (instabile, usa con cautela)
# Disponibile solo su RawPacket.
# NOTA: packet.data è read-only; modifica packet.l4_data per il mangle.
#       l4_data è il payload grezzo nfqueue, può differire da data (stream assembled).
# =============================================================================

# @pyfilter
# def sanitize_payload(packet: RawPacket) -> int:
#     """
#     Esempio: sostituisce una stringa pericolosa con padding neutro
#     mantenendo la stessa lunghezza (importante per TCP!).
#     """
#     target = b"DANGEROUS_CMD"
#     if target in packet.l4_data:
#         replacement = b"X" * len(target)  # stessa lunghezza → no desync TCP
#         packet.l4_data = packet.l4_data.replace(target, replacement)
#         return UNSTABLE_MANGLE
#     return ACCEPT