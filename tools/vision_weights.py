"""Fetch only reviewed official Apache RF-DETR weights outside the source tree."""
import argparse
import hashlib
import json
from urllib.request import urlopen
from .metrica_data import external_output, sha256


# Official rfdetr 1.11.2 model_weights.py assets, not third-party fine-tunes.
ASSETS = {
    'nano': ('https://storage.googleapis.com/rfdetr/nano_coco/checkpoint_best_regular.pth',
             'fb6504cce7fbdc783f7a46991f07639f'),
    'small': ('https://storage.googleapis.com/rfdetr/small_coco/checkpoint_best_regular.pth',
              'fb37061c1af7bace359c91b723a8d5c1'),
}


def download(size, out):
    url, expected = ASSETS[size]
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    registration = {'size': size, 'source_url': url, 'published_md5': expected,
        'license': 'Apache-2.0', 'license_url': 'https://roboflow.com/model-licenses/rf-detr',
        'asset_registry': 'rfdetr==1.11.2/rfdetr/assets/model_weights.py',
        'selected_model': False, 'before_download': True}
    (out / 'registration.json').write_text(json.dumps(registration, indent=2), encoding='utf-8')
    target = out / ('rf-detr-' + size + '.pth')
    temporary = target.with_suffix('.pth.part')
    md5 = hashlib.md5()
    with urlopen(url, timeout=60) as response, temporary.open('xb') as stream:
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            md5.update(chunk)
            stream.write(chunk)
    if md5.hexdigest() != expected:
        raise ValueError('Checkpoint differs from the published asset digest; partial file retained')
    temporary.rename(target)
    registration.update(before_download=False, sha256=sha256(target), bytes=target.stat().st_size)
    (out / 'manifest.json').write_text(json.dumps(registration, indent=2), encoding='utf-8')
    return registration


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', choices=ASSETS, required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(download(args.size, args.out), indent=2))
