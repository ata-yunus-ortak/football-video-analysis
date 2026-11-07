"""Local external-data training feasibility; not a release-selection command."""
import argparse
from importlib.metadata import version
import json
import os
import sys
from pathlib import Path
from tools.metrica_data import external_output, sha256
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member


def run(data, plan_path, weights, out):
    # Rich's metric table contains Unicode box drawing; Windows redirected
    # cp1254 streams otherwise fail after training but before checkpoint export.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    data = Path(data); plan = json.loads(Path(plan_path).read_text())
    manifest_path = data/'manifest.json'; manifest = json.loads(manifest_path.read_text())
    registration = json.loads((data/'before-access.json').read_text())
    if (plan['provided_fixture_used'] or manifest['provided_fixture_used'] or plan['run_test']
            or plan['cloud_logging'] or plan['epochs'] != 1
            or registration['plan_sha256'] != sha256(plan_path)):
        raise ValueError('Registered local one-epoch external feasibility plan required')
    expected = 'd8d6b9ee57d4d0ed2b1f305163624712a0532cb7bce0c747317984fc5457440d'
    if sha256(weights) != expected:
        raise ValueError('Registered Apache-2.0 Nano initialization required')
    for split in ('train', 'valid'):
        if sha256(data/split/'_annotations.coco.json') != manifest['annotation_sha256'][split]:
            raise ValueError('COCO annotations changed')
    for receipt in manifest['images']:
        if receipt['split'] in ('train', 'valid') and sha256(safe_member(data, receipt['file'])) != receipt['sha256']:
            raise ValueError('Training/validation pixels changed')
    out = external_output(out); out.mkdir(parents=True, exist_ok=False)
    os.environ['WANDB_DISABLED'] = 'true'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    before = {'plan': plan, 'plan_sha256': sha256(plan_path), 'data_manifest_sha256': sha256(manifest_path),
        'initial_weights_sha256': expected, 'source_sha256': sha256(__file__),
        'versions': {p: version(p) for p in ('rfdetr', 'torch', 'torchvision')},
        'provided_fixture_used': False, 'test_evaluated': False, 'selected_release': False}
    write(out/'before-training.json', before)
    try:
        from rfdetr import RFDETRNano
        detector = RFDETRNano(pretrain_weights=str(weights), device='cuda', trust_checkpoint=False)
        detector.train(dataset_dir=str(data), output_dir=str(out/'training'),
            epochs=1, batch_size=plan['batch_size'], grad_accum_steps=plan['grad_accum_steps'],
            num_workers=0, seed=plan['seed'], multi_scale=False, expanded_scales=False,
            use_ema=False, run_test=False, tensorboard=False, wandb=False, mlflow=False,
            clearml=False, save_dataset_grids=False, amp_dtype='fp16', device='cuda',
            eval_backend='faster_coco_eval')
        checkpoints = {str(p.relative_to(out)): sha256(p) for p in (out/'training').glob('*.pth')}
        checkpoints.update({str(p.relative_to(out)): sha256(p) for p in (out/'training').glob('*.ckpt')})
        write(out/'report.json', {**before, 'training_completed': True, 'checkpoint_sha256': checkpoints,
            'accuracy_claim': False, 'limitation': plan['limitations']})
        print('One-epoch external training completed; no model promoted.', flush=True)
    except Exception as e:
        write(out/'report.json', {**before, 'training_completed': False,
                                  'error_type': type(e).__name__, 'error': str(e)})
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('data', 'weights', 'out'):
        p.add_argument('--'+k, required=True)
    p.add_argument('--plan', default='ball-detector-training-plan.json')
    a = p.parse_args(); run(a.data, a.plan, a.weights, a.out)
