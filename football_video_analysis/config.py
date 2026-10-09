"""Per-video settings; no match-specific track IDs or pitch coordinates."""

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path


@dataclass
class Config:
    max_ball_gap_frames: int = 3
    possession_grace_frames: int = 2
    max_player_ball_distance_px: float = 32.0
    ambiguity_margin_px: float = 2.0
    max_speed_kmh: float = 45.0
    calibration: dict | None = None
    team_colors_bgr: dict = field(default_factory=dict)
    team_overrides: dict = field(default_factory=dict)
    detection_confidence: float = 0.25

    def validate(self):
        for name in ("max_ball_gap_frames", "possession_grace_frames"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        for name in ("max_player_ball_distance_px", "max_speed_kmh"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(self.ambiguity_margin_px) or self.ambiguity_margin_px < 0:
            raise ValueError("ambiguity_margin_px must be finite and nonnegative")
        if not 0 < self.detection_confidence <= 1:
            raise ValueError("detection_confidence must be in (0, 1]")
        for colors in (self.team_colors_bgr,):
            if colors and set(colors) != {"1", "2"}:
                raise ValueError("team_colors_bgr must contain both string keys 1 and 2")
            for color in colors.values():
                if len(color) != 3 or any(not isinstance(c, (int, float)) or not 0 <= c <= 255 for c in color):
                    raise ValueError("team colors must contain three BGR values in [0, 255]")
        if any(type(team) is not int or team not in (1, 2) for team in self.team_overrides.values()):
            raise ValueError("team overrides must map string track IDs to team 1 or 2")
        return self

    def to_dict(self):
        return asdict(self)


def load_config(path: str | Path | None) -> Config:
    if path is None:
        return Config().validate()
    with Path(path).open(encoding="utf-8") as handle:
        settings = json.load(handle)
    if not isinstance(settings, dict):
        raise ValueError("Configuration must be a JSON object")
    unknown = set(settings) - set(Config.__dataclass_fields__)
    if unknown:
        raise ValueError(f"Unknown configuration fields: {', '.join(sorted(unknown))}")
    return Config(**settings).validate()
