from firegex.nfproxy import pyfilter, ACCEPT, REJECT
from firegex.nfproxy.models import HttpRequest

@pyfilter
def filter_with_args(http_request: HttpRequest) -> int:
    print(f"Received HTTP request: {http_request.url}")
    if http_request.url:
        if "Forbidden" in http_request.url:
            return REJECT
    return ACCEPT