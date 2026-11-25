"""Solicita deploy de um SHA específico; nunca considera somente o aceite como sucesso."""
import json
import os
import time
from urllib.request import Request, urlopen


def main():
    token = os.environ['RENDER_API_KEY']
    service = os.environ['RENDER_SERVICE_ID']
    revision = os.environ['GITHUB_SHA']
    if not token or not service:
        raise SystemExit('Configure RENDER_API_KEY e RENDER_SERVICE_ID nos secrets.')
    base = f'https://api.render.com/v1/services/{service}/deploys'

    def request(url, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        req = Request(url, data=data, headers={
            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        with urlopen(req, timeout=30) as response:
            return json.load(response)

    deployment = request(base, {'commitId': revision})
    deploy_id = deployment['id']
    print(f'Deploy solicitado: {deploy_id}; SHA: {revision}', flush=True)
    for _ in range(100):
        deployment = request(f'{base}/{deploy_id}')
        status = deployment['status']
        print(f'{deploy_id}: {status}', flush=True)
        if status == 'live':
            if deployment.get('commit', {}).get('id') != revision:
                raise SystemExit('Deploy Live não corresponde ao SHA aprovado.')
            return
        if status not in {'created', 'queued', 'build_in_progress', 'pre_deploy_in_progress', 'update_in_progress'}:
            raise SystemExit(f'Deploy não publicado: {status}')
        time.sleep(15)
    raise SystemExit('Tempo limite aguardando deploy Live.')


if __name__ == '__main__':
    main()
