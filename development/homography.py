"""Read automatic per-frame normalized-pitch -> image-pixel homographies.

This is a coordinate adapter, not a confidence classifier or a camera synchronizer.
Missing/invalid matrices and points remain missing; there is no interpolation.
"""
import csv
from pathlib import Path
import numpy as np


class FrameHomographies:
    COLUMNS = ['frame'] + [f'h{i}{j}' for i in range(3) for j in range(3)] + ['reprojection_error', 'valid']

    def __init__(self, path):
        matrices, errors, valid = [], [], []
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != self.COLUMNS:
                raise ValueError('Unsupported homography CSV schema')
            for index, row in enumerate(reader):
                if int(row['frame']) != index or row['valid'] not in ('0', '1'):
                    raise ValueError('Expected consecutive zero-based frames and binary validity')
                matrices.append([float(row[key]) for key in self.COLUMNS[1:10]])
                errors.append(float(row['reprojection_error']))
                valid.append(row['valid'] == '1')
        if not matrices:
            raise ValueError('Empty homography CSV')
        self.matrices = np.asarray(matrices, float).reshape(-1, 3, 3)
        self.errors = np.asarray(errors, float)
        self.valid = np.asarray(valid, bool)
        self.usable = self.valid & np.isfinite(self.matrices).all(axis=(1, 2))
        for index in np.flatnonzero(self.usable):
            try:
                inverse = np.linalg.inv(self.matrices[index])
                self.usable[index] = np.isfinite(inverse).all()
            except np.linalg.LinAlgError:
                self.usable[index] = False

    def metadata(self, tracking_frames):
        return {'available': True, 'frames': len(self.matrices),
                'provider_valid_frames': int(self.valid.sum()),
                'usable_matrix_frames': int(self.usable.sum()),
                'tracking_frame_count_matches': len(self.matrices) == tracking_frames,
                'direction': 'normalized_pitch_to_image_pixels',
                'frame_base': 0, 'interpolated': False}

    def frames(self, start, count):
        if start < 0 or count < 1 or count > 500:
            raise ValueError('Homography frame range invalid')
        result = []
        for frame in range(start, start + count):
            if frame >= len(self.matrices):
                result.append(None)
                continue
            error = self.errors[frame]
            result.append({'provider_valid': bool(self.valid[frame]),
                           'usable': bool(self.usable[frame]),
                           'matrix': self.matrices[frame].tolist() if self.usable[frame] else None,
                           'reprojection_error': float(error) if np.isfinite(error) else None})
        return result

    def project(self, frame, xy, pitch=None):
        """Forward: normalized pitch -> pixels. With pitch: pixels -> metres.

        A point's NaN or zero projective denominator never receives a replacement.
        Applying a ground-plane mapping to an airborne ball does not recover height.
        """
        points = np.asarray(xy, float)
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError('Expected Nx2 points')
        if frame < 0 or frame >= len(self.matrices):
            raise ValueError('Homography frame out of range')
        scale = None
        if pitch is not None:
            scale = np.asarray(pitch, float)
            if scale.shape != (2,) or not np.isfinite(scale).all() or (scale <= 0).any():
                raise ValueError('Expected positive pitch dimensions in metres')
        result = np.full(points.shape, np.nan)
        if not self.usable[frame]:
            return result
        matrix = self.matrices[frame] if scale is None else np.linalg.inv(self.matrices[frame])
        finite = np.isfinite(points).all(axis=1)
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            projected = np.column_stack((points[finite], np.ones(finite.sum()))) @ matrix.T
            projected = projected[:, :2] / projected[:, 2:3]
            if scale is not None:
                projected *= scale
        projected[~np.isfinite(projected).all(axis=1)] = np.nan
        result[finite] = projected
        return result
