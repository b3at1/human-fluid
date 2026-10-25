"""Read-only model discovery; keys are prompted privately, never saved or printed.

Run with backend/.venv/bin/python scripts/list_ai_models.py --base-url <base>
This sends only GET <base>/models, never an inference request.
"""
import argparse
import getpass
from urllib.parse import urlsplit
import httpx


class ModelDiscoveryError(Exception):
    pass


def list_models(base_url: str, key: str, *, transport=None) -> list[dict[str, str]]:
    url = urlsplit(base_url)
    local = url.hostname in ('localhost', '127.0.0.1', '::1')
    if (
        not url.hostname or url.username is not None or url.password is not None
        or url.query or url.fragment
        or not (url.scheme == 'https' or (url.scheme == 'http' and local))
    ):
        raise ModelDiscoveryError('Use an HTTPS API base URL without credentials, query, or fragment.')
    if not key.strip() or any(c in key for c in '\r\n'):
        raise ModelDiscoveryError('An API key is required.')
    try:
        with httpx.Client(timeout=15, follow_redirects=False, trust_env=False, transport=transport) as client:
            with client.stream('GET', base_url.rstrip('/') + '/models', headers={'Authorization': 'Bearer ' + key}) as response:
                if response.status_code != 200:
                    raise ModelDiscoveryError(f'Model listing returned HTTP {response.status_code}. Check the base URL, key, and API permissions. No inference request was made.')
                raw = bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 1048576:
                        raise ModelDiscoveryError('Model list exceeded the 1 MB response limit.')
        import json
        data = json.loads(raw)
        rows = data.get('data') if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ModelDiscoveryError('This endpoint did not return a compatible model list. Its chat API may still work; use the exact model ID from its documentation.')
        models = []
        for row in rows[:2000]:
            if not isinstance(row, dict):
                continue
            model_id = row.get('id')
            name = row.get('name', '')
            if not isinstance(model_id, str) or not model_id or len(model_id) > 300:
                continue
            if not isinstance(name, str):
                name = ''
            # Untrusted labels must not inject terminal control sequences or echo a key.
            name = name[:300]
            if key in model_id or key in name or any(not c.isprintable() for c in model_id + name):
                continue
            models.append({'id': model_id, 'name': name})
        return models
    except ModelDiscoveryError:
        raise
    except (httpx.HTTPError, ValueError, TypeError):
        raise ModelDiscoveryError('Could not read a compatible model list. Check the API URL and network connection. No inference request was made.') from None


def main():
    parser = argparse.ArgumentParser(description='List provider model IDs without sending a prompt or saving your API key.')
    parser.add_argument('--base-url', help='API prefix, e.g. https://your-provider.example/api; omit /chat/completions')
    parser.add_argument('--filter', default='opus', help='Case-insensitive ID/name filter; use an empty string to list all models')
    args = parser.parse_args()
    base = args.base_url or input('API base URL (from your provider documentation): ').strip()
    print('Only GET ' + base.rstrip('/') + '/models will be requested; no prompt will be sent.')
    key = getpass.getpass('API key (hidden; not saved): ')
    try:
        rows = list_models(base, key)
    except ModelDiscoveryError as error:
        raise SystemExit(str(error)) from None
    selected = [r for r in rows if args.filter.casefold() in (r['id'] + ' ' + r['name']).casefold()]
    if not selected:
        print('No matching model IDs were returned. Check your model access or run with --filter "".')
    for row in selected:
        print(row['id'] + ('  —  ' + row['name'] if row['name'] else ''))
    print('Model discovery does not verify inference compatibility or output-token cap enforcement.')


if __name__ == '__main__':
    main()
