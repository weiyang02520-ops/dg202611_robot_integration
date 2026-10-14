"""RGB-primary depth pairing (plan §7.1). Pure Python / NumPy, no rclpy."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional, Tuple

from vision_perception.depth_io import DepthFrame, stamp_delta_sec, stamp_to_ns


@dataclass
class PairResult:
    depth: Optional[DepthFrame]
    skew_sec: Optional[float]
    reason: str  # OK / DEPTH_UNPAIRED


class DepthFrameBuffer:
    """Finite depth queue for RGB-primary pairing."""

    def __init__(
        self,
        *,
        tolerance_sec: float = 0.010,
        max_size: int = 10,
    ):
        if tolerance_sec <= 0:
            raise ValueError("tolerance_sec must be > 0")
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self.tolerance_sec = float(tolerance_sec)
        self.max_size = int(max_size)
        self._frames: Deque[DepthFrame] = deque()
        self.dropped_oldest = 0
        self.paired = 0
        self.unpaired = 0

    def push(self, frame: DepthFrame) -> None:
        self._frames.append(frame)
        while len(self._frames) > self.max_size:
            self._frames.popleft()
            self.dropped_oldest += 1

    def clear(self) -> None:
        self._frames.clear()

    def __len__(self) -> int:
        return len(self._frames)

    def pair_for_rgb(
        self, stamp_sec: int, stamp_nanosec: int
    ) -> PairResult:
        """Find exact stamp match, else nearest unused depth within tolerance.

        On ties (equal |delta|), prefer the earlier depth stamp. Consumes the
        chosen depth so each depth pairs with at most one RGB.
        """
        if not self._frames:
            self.unpaired += 1
            return PairResult(depth=None, skew_sec=None, reason="DEPTH_UNPAIRED")

        rgb_ns = stamp_to_ns(stamp_sec, stamp_nanosec)
        best_i = -1
        best_key: Optional[Tuple[int, int, int]] = None
        for i, frame in enumerate(self._frames):
            d_ns = stamp_to_ns(frame.stamp_sec, frame.stamp_nanosec)
            delta = abs(d_ns - rgb_ns)
            # Exact match preferred (delta==0). Tolerance applied later.
            key = (delta, d_ns, i)  # earlier depth wins ties
            if best_key is None or key < best_key:
                best_key = key
                best_i = i

        assert best_i >= 0 and best_key is not None
        frame = self._frames[best_i]
        skew = stamp_delta_sec(
            stamp_sec, stamp_nanosec, frame.stamp_sec, frame.stamp_nanosec
        )
        if skew > self.tolerance_sec + 1e-12:
            self.unpaired += 1
            return PairResult(depth=None, skew_sec=skew, reason="DEPTH_UNPAIRED")

        del self._frames[best_i]
        self.paired += 1
        return PairResult(depth=frame, skew_sec=skew, reason="OK")
