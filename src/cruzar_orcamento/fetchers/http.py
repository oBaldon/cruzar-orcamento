from __future__ import annotations
import os, time, random, requests, tempfile, shutil

# headers mais “reais”
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.caixa.gov.br/Downloads/sinapi-relatorios-mensais/",
    "Connection": "keep-alive",
}

def head_ok(url: str, timeout: float = 15.0) -> bool:
    try:
        r = requests.head(url, headers=DEFAULT_HEADERS, allow_redirects=True, timeout=timeout)
        return 200 <= r.status_code < 300
    except requests.RequestException:
        return False

def url_exists(url: str, timeout: float = 15.0) -> bool:
    # 1) HEAD
    try:
        r = requests.head(url, headers=DEFAULT_HEADERS, allow_redirects=True, timeout=timeout)
        if 200 <= r.status_code < 300:
            return True
    except requests.RequestException:
        pass
    # 2) GET range (200/206)
    try:
        hdrs = dict(DEFAULT_HEADERS, **{"Range": "bytes=0-0"})
        r = requests.get(url, headers=hdrs, stream=True, allow_redirects=True, timeout=timeout)
        return r.status_code in (200, 206)
    except requests.RequestException:
        return False

def _looks_like_zip_response(resp: requests.Response) -> bool:
    ct = (resp.headers.get("Content-Type") or "").lower()
    return ("zip" in ct) or ("octet-stream" in ct)

def download_file(url: str, dest_path: str, timeout: float = 120.0,
                  retries: int = 4, backoff: float = 1.6, min_bytes: int = 1024) -> None:
    """
    Baixa com retries e grava de forma atômica (tmp + rename).
    Valida tamanho mínimo; se Content-Type parecer HTML, trata como falha.
    """
    last = None
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)

    for attempt in range(retries):
        try:
            with requests.get(url, headers=DEFAULT_HEADERS, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                # evita pegar páginas HTML/erro no lugar do ZIP/arquivo
                if "text/html" in (r.headers.get("Content-Type") or "").lower():
                    raise RuntimeError(f"Resposta HTML inesperada (status {r.status_code})")

                with tempfile.NamedTemporaryFile("wb", delete=False, dir=os.path.dirname(dest_path)) as tmp:
                    tmp_path = tmp.name
                    total = 0
                    for chunk in r.iter_content(262_144):
                        if not chunk:
                            continue
                        tmp.write(chunk)
                        total += len(chunk)

                if total < min_bytes:
                    raise RuntimeError(f"Arquivo muito pequeno ({total} bytes)")

                # rename atômico
                os.replace(tmp_path, dest_path)
                return

        except Exception as e:
            last = e
            # jitter para não bater sempre igual
            sleep_s = (backoff ** attempt) + random.uniform(0, 0.5)
            time.sleep(sleep_s)
            # cleanup tmp se ficou
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    raise RuntimeError(f"Falha ao baixar {url}: {last}")
