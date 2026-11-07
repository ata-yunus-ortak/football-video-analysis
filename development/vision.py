"""Optional local detection adapters. Imports of large dependencies are lazy.

Outputs are image observations, not possession, team identities or ball height.
RF-DETR Nano/Small use the official Apache-2.0 COCO checkpoints. All algorithm
settings must be supplied explicitly by an external experiment registration.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class VisionConfig:
    size: str
    threshold: float
    sliced: bool
    slice_height: int
    slice_width: int
    overlap_ratio: float
    track_activation_threshold: float
    track_matching_threshold: float
    lost_track_s: float
    min_consecutive_frames: int

    def __post_init__(self):
        if self.size not in ('nano', 'small') or type(self.sliced) is not bool:
            raise ValueError('Only reviewed Nano/Small and explicit slicing choice supported')
        for name in ('threshold', 'track_activation_threshold', 'track_matching_threshold'):
            value = getattr(self, name)
            if not np.isfinite(value) or not 0 < value <= 1:
                raise ValueError('Finite confidence/matching thresholds in (0,1] required')
        if (not np.isfinite(self.overlap_ratio) or not 0 <= self.overlap_ratio < 1
                or not np.isfinite(self.lost_track_s) or self.lost_track_s <= 0
                or any(type(v) is not int or v < 1 for v in
                       (self.slice_height, self.slice_width, self.min_consecutive_frames))):
            raise ValueError('Positive tile/track sizes and valid overlap required')


def ground_projection(xy, homography):
    """Project a pixel on an assumed ground plane; return NaN at the horizon."""
    points, h = np.asarray(xy, float), np.asarray(homography, float)
    if points.ndim != 2 or points.shape[1] != 2 or h.shape != (3, 3) or not np.isfinite(h).all():
        raise ValueError('Nx2 points and finite 3x3 image-to-metre homography required')
    if np.linalg.matrix_rank(h) < 3:
        raise ValueError('Singular homography')
    projected = np.column_stack((points, np.ones(len(points)))) @ h.T
    valid = np.isfinite(projected).all(1) & (np.abs(projected[:, 2]) > 1e-12)
    result = np.full((len(points), 2), np.nan)
    result[valid] = projected[valid, :2] / projected[valid, 2, None]
    return result


def observation_rows(detections, tracked, class_names, width, height):
    """Keep unconfirmed people and all ball candidates; missing track != absent."""
    tracks = {}
    if tracked.tracker_id is not None:
        for box, cid, tid in zip(tracked.xyxy, tracked.class_id, tracked.tracker_id):
            tracks.setdefault((int(cid), *box.tolist()), []).append(int(tid))
    rows = []
    for box, score, cid in zip(detections.xyxy, detections.confidence, detections.class_id):
        name = class_names.get(int(cid))
        ids = tracks.get((int(cid), *box.tolist()), []) if name == 'person' else []
        if name not in ('person', 'sports ball'):
            continue
        if (not np.isfinite(box).all() or not np.isfinite(score) or not 0 <= score <= 1
                or box[2] <= box[0] or box[3] <= box[1]):
            continue
        original_box = box.copy()
        box = np.clip(box, [0, 0, 0, 0], [width, height, width, height])
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        rows.append({'kind': name, 'class_id': int(cid), 'confidence': float(score),
                     'box_xyxy': box.tolist(), 'track_id': ids[0] if len(ids) == 1 else None,
                     'team': None, 'measurement': True,
                     'anchor_xy': [float((box[0] + box[2]) / 2),
                                   float(box[3] if name == 'person' else (box[1] + box[3]) / 2)],
                     'anchor_kind': 'feet_candidate' if name == 'person' else 'image_ball_center',
                     'anchor_truncated': bool(not np.array_equal(original_box, box)
                         or box[0] <= 0 or box[1] <= 0 or box[2] >= width or box[3] >= height),
                     'ball_height_known': False})
    return rows


class LocalVision:
    def __init__(self, cfg, weights, fps, device):
        import supervision as sv
        from rfdetr import RFDETRNano, RFDETRSmall
        from rfdetr.assets.coco_classes import COCO_CLASSES
        if not np.isfinite(fps) or fps <= 0 or device not in ('cpu', 'cuda'):
            raise ValueError('Positive video FPS and explicit cpu/cuda device required')
        self.cfg, self.sv, self.fps = cfg, sv, float(fps)
        self.names = dict(COCO_CLASSES)
        cls = RFDETRNano if cfg.size == 'nano' else RFDETRSmall
        self.detector = cls(pretrain_weights=str(weights), device=device, trust_checkpoint=False)
        self.reset_tracking()
        self.sliced_model = None
        if cfg.sliced:
            from sahi.models.roboflow import RoboflowDetectionModel
            self.sliced_model = RoboflowDetectionModel(model=self.detector,
                confidence_threshold=cfg.threshold, category_mapping=self.names, device=device)

    def reset_tracking(self):
        cfg = self.cfg
        self.tracker = self.sv.ByteTrack(track_activation_threshold=cfg.track_activation_threshold,
            minimum_matching_threshold=cfg.track_matching_threshold,
            lost_track_buffer=max(1, int(np.ceil(cfg.lost_track_s * 30))),
            frame_rate=self.fps, minimum_consecutive_frames=cfg.min_consecutive_frames)

    def process(self, rgb):
        if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
            raise ValueError('RGB uint8 image required')
        if self.sliced_model is None:
            detections = self.detector.predict(rgb, threshold=self.cfg.threshold)
        else:
            from sahi.predict import get_sliced_prediction
            result = get_sliced_prediction(rgb, self.sliced_model,
                slice_height=self.cfg.slice_height, slice_width=self.cfg.slice_width,
                overlap_height_ratio=self.cfg.overlap_ratio, overlap_width_ratio=self.cfg.overlap_ratio,
                verbose=0)
            objects = result.object_prediction_list
            detections = self.sv.Detections(
                xyxy=np.asarray([p.bbox.to_xyxy() for p in objects], np.float32).reshape(-1, 4),
                confidence=np.asarray([p.score.value for p in objects], np.float32),
                class_id=np.asarray([p.category.id for p in objects], int))
        people = np.array([self.names.get(int(cid)) == 'person' for cid in detections.class_id], bool)
        tracked = self.tracker.update_with_detections(detections[people])
        return observation_rows(detections, tracked, self.names, rgb.shape[1], rgb.shape[0])
