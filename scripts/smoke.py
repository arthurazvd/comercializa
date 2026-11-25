"""Smoke Test: exige HTTP 200 direto, JSON de saúde e, em produção, SHA aprovado."""
import argparse
import json
import time
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--revision')
    parser.add_argument('--attempts', type=int, default=1)
    parser.add_argument('--delay', type=int, default=5)
    args = parser.parse_args()
    url = args.url.rstrip('/') + '/health'
    if args.revision and not url.startswith('https://'):
        raise SystemExit('Use HTTPS no ambiente público.')
    opener = build_opener(NoRedirect())
    for attempt in range(1, args.attempts + 1):
        try:
            with opener.open(Request(url, headers={'Cache-Control': 'no-cache'}), timeout=15) as response:
                revision = response.headers.get('X-Comercializa-Revision')
                if response.status != 200 or json.load(response) != {'status': 'ok'}:
                    raise ValueError('Resposta de saúde inválida')
                if args.revision and revision != args.revision:
                    raise ValueError(f'Revisão inesperada: {revision}')
                print(f'{url} HTTP 200 | status=ok | revision={revision}', flush=True)
                return
        except (OSError, ValueError) as exc:
            print(f'Tentativa {attempt}: {exc}', flush=True)
            if attempt < args.attempts:
                time.sleep(args.delay)
    raise SystemExit('Smoke Test falhou.')


if __name__ == '__main__':
    main()
