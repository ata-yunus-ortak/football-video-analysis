"""Check a local feasibility checkpoint changed and reloads on synthetic pixels."""
import argparse
import json
from pathlib import Path
import os
import numpy as np
from tools.metrica_data import external_output, sha256
from tools.ball_candidate_selection import write


def run(training, initial, out):
    training = Path(training)
    report = json.loads((training/'report.json').read_text())
    if not report['training_completed'] or report['provided_fixture_used'] or report['selected_release']:
        raise ValueError('Completed external feasibility run required')
    if sha256(initial) != report['initial_weights_sha256']:
        raise ValueError('Initialization changed')
    candidates = [k for k in report['checkpoint_sha256'] if k.endswith('checkpoint_best_total.pth')]
    if len(candidates) != 1:
        raise ValueError('One exported best checkpoint required')
    path = training/candidates[0]
    if sha256(path) != report['checkpoint_sha256'][candidates[0]]:
        raise ValueError('Checkpoint changed')
    out = external_output(out); out.mkdir(parents=True, exist_ok=False)
    os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import torch
    before = torch.load(initial, map_location='cpu', weights_only=True)['model']
    after = torch.load(path, map_location='cpu', weights_only=True)['model']
    common = [k for k in before if k in after and before[k].shape == after[k].shape
              and torch.is_floating_point(before[k]) and 'backbone' in k]
    changed = [k for k in common if not torch.equal(before[k], after[k])]
    if not common or not changed or any(not torch.isfinite(t).all() for t in after.values() if torch.is_tensor(t)):
        raise ValueError('No finite learned backbone update established')
    del before, after
    from rfdetr import RFDETRNano
    detector = RFDETRNano.from_checkpoint(str(path), device='cuda', trust_checkpoint=False)
    # Blank pixels establish API execution only, not detector quality.
    result = detector.predict(np.zeros((384, 384, 3), dtype=np.uint8), threshold=0.)
    if not np.isfinite(result.xyxy).all() or not np.isfinite(result.confidence).all():
        raise ValueError('Reloaded inference produced nonfinite values')
    verified = {'training_report_sha256': sha256(training/'report.json'),
        'checkpoint_sha256': sha256(path), 'shared_backbone_tensors': len(common),
        'changed_backbone_tensors': len(changed), 'synthetic_inference_completed': True,
        'synthetic_candidate_count': len(result), 'class_names': detector.class_names,
        'synthetic_class_ids': sorted(set(result.class_id.tolist())),
        'provided_fixture_used': False, 'real_image_evaluated': False,
        'accuracy_validated': False, 'selected_release': False}
    write(out/'report.json', verified); print(json.dumps(verified, indent=2))
    return verified


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('training', 'initial', 'out'):
        p.add_argument('--'+k, required=True)
    a = p.parse_args(); run(a.training, a.initial, a.out)
