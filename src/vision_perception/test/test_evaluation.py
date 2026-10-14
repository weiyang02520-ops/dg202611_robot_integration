"""V1 offline bbox evaluation (plan §10.1) — no ROS / no ONNX / no camera."""

from __future__ import annotations

import json
from pathlib import Path

from vision_perception.evaluation import (
    EvalBox,
    ImageEvalCase,
    cases_from_offline_batches,
    evaluate_cases,
    evaluate_offline_payload,
    match_same_class_iou,
)


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_match_counts_tp_fp_fn():
    gt = [EvalBox("bottle", 0, 0, 10, 10)]
    pred = [
        EvalBox("bottle", 1, 1, 11, 11),  # IoU high
        EvalBox("bottle", 50, 50, 60, 60),  # FP
    ]
    counts = match_same_class_iou(gt, pred, iou_threshold=0.5)
    assert counts.tp == 1
    assert counts.fp == 1
    assert counts.fn == 0


def test_zero_denominator_not_reported_as_perfect():
    metrics = evaluate_cases(
        [
            ImageEvalCase(
                source_image_id="bg.npy",
                ground_truth=[],
                predictions=[],
            )
        ]
    )
    bottle = metrics["per_class"]["bottle"]
    assert bottle["tp"] == 0 and bottle["fp"] == 0 and bottle["fn"] == 0
    assert bottle["precision"] is None
    assert bottle["recall"] is None
    assert bottle["precision_computable"] is False
    assert bottle["recall_computable"] is False


def test_background_fp_does_not_use_frame_count_as_denominator():
    metrics = evaluate_cases(
        [
            ImageEvalCase("a", [], [EvalBox("cup", 0, 0, 5, 5)]),
            ImageEvalCase("b", [], []),  # empty GT scene with no preds
        ]
    )
    cup = metrics["per_class"]["cup"]
    assert cup["fp"] == 1
    assert cup["tp"] == 0
    assert cup["precision"] == 0.0
    assert cup["precision_computable"] is True


def test_example_annotations_pair_with_golden_format_batches():
    golden = json.loads(
        (EXAMPLES / "golden_format_batch.json").read_text(encoding="utf-8")
    )
    metrics = evaluate_offline_payload(
        golden,
        str(EXAMPLES / "eval_annotations.example.json"),
        iou_threshold=0.5,
    )
    assert metrics["stage"] == "V1_OFFLINE_EVAL"
    assert metrics["arm_ready"] == "NO"
    assert metrics["camera_contract"] == "NOT_RUN"
    bottle = metrics["per_class"]["bottle"]
    # Golden bottle vs example annotation should match as TP at IoU 0.5.
    assert bottle["tp"] == 1
    assert bottle["fn"] == 0


def test_gt_only_image_counts_as_fn():
    batches = [
        {
            "source_image_id": "seen.jpg",
            "detections": [],
        }
    ]
    annotations = {
        "seen.jpg": [],
        "missed.jpg": [EvalBox("cup", 0, 0, 8, 8)],
    }
    cases = cases_from_offline_batches(batches, annotations)
    metrics = evaluate_cases(cases)
    assert metrics["per_class"]["cup"]["fn"] == 1
