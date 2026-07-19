#!/usr/bin/env /opt/miniconda3/bin/python3
"""
Image Comparison Benchmark Script
Compares XFeat, ALIKED, LightGlue (DISK), and ORB for video frame matching.
Generates a self-contained HTML report with charts and visualizations.
"""

import base64
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch

import kornia as K
import kornia.feature as KF


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkConfig:
    video_path: str = "data/242d929f1b68303b2f7edbff10c14427.mp4"
    query_path: str = "query_image/f04eb4d677dfc38ac2304575aaf80dfa.jpg"
    output_dir: str = "reports"
    vis_dir: str = "reports/visualizations"
    max_dim: int = 1024
    extraction_fps: float = 1.0
    device_preference: str = "mps"
    warmup_runs: int = 2


@dataclass
class MatchResult:
    algorithm: str
    frame_index: int
    timestamp_sec: float
    num_matches: int
    avg_confidence: float
    composite_score: float
    elapsed_ms: float
    query_kp_count: int
    frame_kp_count: int


@dataclass
class VisData:
    algorithm: str
    frame_index: int
    query_img_bgr: np.ndarray
    frame_img_bgr: np.ndarray
    query_kp: list  # cv2.KeyPoint list
    frame_kp: list
    match_pairs: list  # list of cv2.DMatch or (idx1, idx2) tuples


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_device(preference: str = "mps") -> torch.device:
    """Resolve best available device."""
    if preference == "mps" and torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def sync_device(device: torch.device) -> None:
    """Synchronize device for accurate timing."""
    if device.type == "mps":
        torch.mps.synchronize()
    elif device.type == "cuda":
        torch.cuda.synchronize()


def resize_bgr(img_bgr: np.ndarray, max_dim: int) -> np.ndarray:
    """Resize so longest side == max_dim, preserving aspect ratio."""
    h, w = img_bgr.shape[:2]
    scale = max_dim / max(h, w)
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        img_bgr = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img_bgr


def bgr_to_tensor(img_bgr: np.ndarray, device: torch.device) -> torch.Tensor:
    """BGR numpy → (1,3,H,W) float32 tensor in [0,1]."""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    t = torch.from_numpy(img_rgb).permute(2, 0, 1).float() / 255.0
    return t.unsqueeze(0).to(device)


def extract_frames_at_fps(
    video_path: str, target_fps: float
) -> list[tuple[int, float, np.ndarray]]:
    """Extract frames at target fps. Returns (frame_index, timestamp_sec, bgr_array)."""
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = max(1, int(round(video_fps / target_fps)))

    frames = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            timestamp = frame_idx / video_fps
            frames.append((frame_idx, timestamp, frame))
        frame_idx += 1
    cap.release()
    return frames


def compute_composite(num_matches: int, avg_confidence: float) -> float:
    """Composite score: 0.6 * log1p(matches)/log1p(4096) + 0.4 * confidence."""
    if num_matches == 0:
        return 0.0
    match_score = math.log1p(num_matches) / math.log1p(4096)
    return float(0.6 * match_score + 0.4 * avg_confidence)


# ---------------------------------------------------------------------------
# Algorithm: XFeat
# ---------------------------------------------------------------------------

def run_xfeat_benchmark(
    query_tensor: torch.Tensor,
    frame_tensors: list[tuple[int, float, torch.Tensor]],
    device: torch.device,
    warmup_runs: int,
) -> tuple[list[MatchResult], list[VisData]]:
    print("  Loading XFeat model...")
    detector = KF.XFeat.from_pretrained().to(device).eval()

    # Warmup
    with torch.inference_mode():
        for _ in range(warmup_runs):
            _ = detector.detectAndCompute(query_tensor)
        sync_device(device)

    # Query features
    with torch.inference_mode():
        query_out = detector.detectAndCompute(query_tensor)[0]

    results, vis_list = [], []
    for i, (frame_idx, ts, ft) in enumerate(frame_tensors):
        print(f"  XFeat [{i+1}/{len(frame_tensors)}] frame {frame_idx}", end="\r")
        sync_device(device)
        t0 = time.perf_counter()

        with torch.inference_mode():
            frame_out = detector.detectAndCompute(ft)[0]

            q_desc = query_out["descriptors"]
            f_desc = frame_out["descriptors"]

            if q_desc.shape[0] == 0 or f_desc.shape[0] == 0:
                num_matches, avg_conf = 0, 0.0
            else:
                distances, indices = KF.match_mnn(q_desc, f_desc)
                num_matches = indices.shape[0]
                avg_dist = distances.mean().item() if num_matches > 0 else 2.0
                avg_conf = max(0.0, 1.0 - avg_dist / 2.0)

        sync_device(device)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        results.append(MatchResult(
            algorithm="XFeat", frame_index=frame_idx, timestamp_sec=ts,
            num_matches=num_matches, avg_confidence=avg_conf,
            composite_score=compute_composite(num_matches, avg_conf),
            elapsed_ms=elapsed_ms,
            query_kp_count=query_out["keypoints"].shape[0],
            frame_kp_count=frame_out["keypoints"].shape[0],
        ))
    print()
    return results, vis_list


# ---------------------------------------------------------------------------
# Algorithm: ALIKED
# ---------------------------------------------------------------------------

def run_aliked_benchmark(
    query_tensor: torch.Tensor,
    frame_tensors: list[tuple[int, float, torch.Tensor]],
    device: torch.device,
    warmup_runs: int,
) -> tuple[list[MatchResult], list[VisData]]:
    print("  Loading ALIKED model...")
    detector = KF.ALIKED.from_pretrained("aliked-n16", device=device).eval()

    # Warmup
    with torch.inference_mode():
        for _ in range(warmup_runs):
            _ = detector(query_tensor)
        sync_device(device)

    # Query features
    with torch.inference_mode():
        query_feat = detector(query_tensor)[0]

    results, vis_list = [], []
    for i, (frame_idx, ts, ft) in enumerate(frame_tensors):
        print(f"  ALIKED [{i+1}/{len(frame_tensors)}] frame {frame_idx}", end="\r")
        sync_device(device)
        t0 = time.perf_counter()

        with torch.inference_mode():
            frame_feat = detector(ft)[0]

            q_desc = query_feat.descriptors
            f_desc = frame_feat.descriptors

            if q_desc.shape[0] == 0 or f_desc.shape[0] == 0:
                num_matches, avg_conf = 0, 0.0
            else:
                distances, indices = KF.match_mnn(q_desc, f_desc)
                num_matches = indices.shape[0]
                avg_dist = distances.mean().item() if num_matches > 0 else 2.0
                avg_conf = max(0.0, 1.0 - avg_dist / 2.0)

        sync_device(device)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        results.append(MatchResult(
            algorithm="ALIKED", frame_index=frame_idx, timestamp_sec=ts,
            num_matches=num_matches, avg_confidence=avg_conf,
            composite_score=compute_composite(num_matches, avg_conf),
            elapsed_ms=elapsed_ms,
            query_kp_count=query_feat.keypoints.shape[0],
            frame_kp_count=frame_feat.keypoints.shape[0],
        ))
    print()
    return results, vis_list


# ---------------------------------------------------------------------------
# Algorithm: LightGlue (with DISK detector)
# ---------------------------------------------------------------------------

def run_lightglue_benchmark(
    query_tensor: torch.Tensor,
    frame_tensors: list[tuple[int, float, torch.Tensor]],
    device: torch.device,
    warmup_runs: int,
) -> tuple[list[MatchResult], list[VisData]]:
    print("  Loading DISK + LightGlue models...")
    disk = KF.DISK.from_pretrained("depth", device=device).eval()
    matcher = KF.LightGlue(features="disk").to(device).eval()

    def extract_disk(img_t):
        with torch.inference_mode():
            feats = disk(img_t, n=4096, window_size=5,
                         score_threshold=0.0, pad_if_not_divisible=True)
            kp = feats[0].keypoints.unsqueeze(0)
            desc = feats[0].descriptors.unsqueeze(0)
        return kp, desc

    # Warmup
    for _ in range(warmup_runs):
        q_kp, q_desc = extract_disk(query_tensor)
        data = {
            "image0": {"keypoints": q_kp, "descriptors": q_desc, "image": query_tensor},
            "image1": {"keypoints": q_kp, "descriptors": q_desc, "image": query_tensor},
        }
        _ = matcher(data)
    sync_device(device)

    # Query features
    q_kp, q_desc = extract_disk(query_tensor)

    results, vis_list = [], []
    for i, (frame_idx, ts, ft) in enumerate(frame_tensors):
        print(f"  LightGlue [{i+1}/{len(frame_tensors)}] frame {frame_idx}", end="\r")
        sync_device(device)
        t0 = time.perf_counter()

        with torch.inference_mode():
            f_kp, f_desc = extract_disk(ft)

            if q_kp.shape[1] < 2 or f_kp.shape[1] < 2:
                num_matches, avg_conf = 0, 0.0
            else:
                data = {
                    "image0": {"keypoints": q_kp, "descriptors": q_desc, "image": query_tensor},
                    "image1": {"keypoints": f_kp, "descriptors": f_desc, "image": ft},
                }
                output = matcher(data)
                matched_indices = output["matches"][0]
                match_scores = output["scores"][0]
                num_matches = matched_indices.shape[0]
                avg_conf = match_scores.mean().item() if num_matches > 0 else 0.0

        sync_device(device)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        results.append(MatchResult(
            algorithm="LightGlue", frame_index=frame_idx, timestamp_sec=ts,
            num_matches=num_matches, avg_confidence=avg_conf,
            composite_score=compute_composite(num_matches, avg_conf),
            elapsed_ms=elapsed_ms,
            query_kp_count=q_kp.shape[1],
            frame_kp_count=f_kp.shape[1],
        ))
    print()
    return results, vis_list


# ---------------------------------------------------------------------------
# Algorithm: ORB
# ---------------------------------------------------------------------------

def run_orb_benchmark(
    query_gray: np.ndarray,
    frame_grays: list[tuple[int, float, np.ndarray]],
    warmup_runs: int,
) -> tuple[list[MatchResult], list[VisData]]:
    print("  Setting up ORB...")
    orb = cv2.ORB_create(nfeatures=2000)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    kp_q, desc_q = orb.detectAndCompute(query_gray, None)

    # Warmup
    if warmup_runs > 0 and len(frame_grays) > 0 and desc_q is not None:
        _, _, warmup_gray = frame_grays[0]
        for _ in range(warmup_runs):
            kp_w, desc_w = orb.detectAndCompute(warmup_gray, None)
            if desc_w is not None:
                _ = bf.knnMatch(desc_q, desc_w, k=2)

    results, vis_list = [], []
    for i, (frame_idx, ts, gray) in enumerate(frame_grays):
        print(f"  ORB [{i+1}/{len(frame_grays)}] frame {frame_idx}", end="\r")
        t0 = time.perf_counter()

        kp_f, desc_f = orb.detectAndCompute(gray, None)

        if desc_f is None or desc_q is None or len(kp_f) < 2:
            results.append(MatchResult(
                algorithm="ORB", frame_index=frame_idx, timestamp_sec=ts,
                num_matches=0, avg_confidence=0.0, composite_score=0.0,
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                query_kp_count=len(kp_q) if kp_q else 0, frame_kp_count=0,
            ))
            continue

        raw_matches = bf.knnMatch(desc_q, desc_f, k=2)

        good = []
        for pair in raw_matches:
            if len(pair) == 2:
                m, n = pair
                if m.distance < 0.75 * n.distance:
                    good.append(m)

        num_matches = len(good)
        if num_matches > 0:
            avg_dist = float(np.mean([m.distance for m in good]))
            avg_conf = max(0.0, 1.0 - avg_dist / 256.0)
        else:
            avg_conf = 0.0

        elapsed_ms = (time.perf_counter() - t0) * 1000

        results.append(MatchResult(
            algorithm="ORB", frame_index=frame_idx, timestamp_sec=ts,
            num_matches=num_matches, avg_confidence=avg_conf,
            composite_score=compute_composite(num_matches, avg_conf),
            elapsed_ms=elapsed_ms,
            query_kp_count=len(kp_q) if kp_q else 0,
            frame_kp_count=len(kp_f),
        ))

        # Save vis data for top matches later
        if num_matches > 0:
            vis_list.append(VisData(
                algorithm="ORB", frame_index=frame_idx,
                query_img_bgr=None, frame_img_bgr=None,
                query_kp=kp_q, frame_kp=kp_f, match_pairs=good,
            ))
    print()
    return results, vis_list


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def draw_match_image(
    query_bgr: np.ndarray, frame_bgr: np.ndarray,
    query_kp, frame_kp, match_pairs, algorithm: str,
    result: MatchResult,
) -> np.ndarray:
    """Draw side-by-side match visualization."""
    if isinstance(match_pairs[0], cv2.DMatch) if match_pairs else False:
        # ORB path — cv2.DMatch objects
        vis = cv2.drawMatches(
            query_bgr, query_kp, frame_bgr, frame_kp,
            match_pairs[:50], None,
            matchColor=(0, 255, 0), singlePointColor=(255, 0, 0),
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
        )
    else:
        # Kornia path — (idx1, idx2) tuples + numpy keypoint arrays
        h1, w1 = query_bgr.shape[:2]
        h2, w2 = frame_bgr.shape[:2]
        vis = np.zeros((max(h1, h2), w1 + w2, 3), dtype=np.uint8)
        vis[:h1, :w1] = query_bgr
        vis[:h2, w1:w1 + w2] = frame_bgr

        for idx_q, idx_f in match_pairs[:50]:
            pt1 = tuple(int(x) for x in query_kp[idx_q])
            pt2 = tuple(int(x) + w1 for x in frame_kp[idx_f])
            color = tuple(int(c) for c in np.random.randint(0, 255, 3))
            cv2.line(vis, pt1, pt2, color, 1)
            cv2.circle(vis, pt1, 3, color, -1)
            cv2.circle(vis, pt2, 3, color, -1)

    # Add text overlay
    text = f"{algorithm} | Matches: {result.num_matches} | "
    text += f"Conf: {result.avg_confidence:.3f} | Score: {result.composite_score:.3f}"
    cv2.putText(vis, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    return vis


def save_top_visualizations(
    all_results: dict[str, list[MatchResult]],
    raw_frames: list[tuple[int, float, np.ndarray]],
    query_bgr: np.ndarray,
    kornia_vis: dict[str, list[tuple]],  # algo -> list of (query_kp, frame_kp, indices, frame_idx)
    orb_vis: list[VisData],
    vis_dir: str,
    max_dim: int,
) -> dict[str, list[str]]:
    """Save top-3 match images per algorithm. Returns {algo: [img_paths]}."""
    os.makedirs(vis_dir, exist_ok=True)
    frame_map = {f[0]: f[2] for f in raw_frames}
    saved = {}

    for algo, results in all_results.items():
        top3 = sorted(results, key=lambda r: r.composite_score, reverse=True)[:3]
        paths = []
        for rank, res in enumerate(top3, 1):
            if res.num_matches == 0:
                continue
            frame_bgr = frame_map.get(res.frame_index)
            if frame_bgr is None:
                continue

            frame_bgr_r = resize_bgr(frame_bgr, max_dim)
            query_bgr_r = resize_bgr(query_bgr, max_dim)

            if algo == "ORB":
                # Find matching vis data
                vd = next((v for v in orb_vis if v.frame_index == res.frame_index), None)
                if vd is None:
                    continue
                vis_img = draw_match_image(
                    query_bgr_r, frame_bgr_r,
                    vd.query_kp, vd.frame_kp, vd.match_pairs,
                    algo, res,
                )
            elif algo in kornia_vis:
                entry = next(
                    (e for e in kornia_vis[algo] if e[3] == res.frame_index), None
                )
                if entry is None:
                    continue
                q_kp, f_kp, indices, _ = entry
                q_pts = q_kp.cpu().numpy() if torch.is_tensor(q_kp) else np.array(q_kp)
                f_pts = f_kp.cpu().numpy() if torch.is_tensor(f_kp) else np.array(f_kp)
                idx_np = indices.cpu().numpy() if torch.is_tensor(indices) else np.array(indices)
                pairs = [(int(idx_np[i, 0]), int(idx_np[i, 1])) for i in range(min(50, len(idx_np)))]
                vis_img = draw_match_image(
                    query_bgr_r, frame_bgr_r,
                    q_pts, f_pts, pairs, algo, res,
                )
            else:
                continue

            fname = f"{algo}_top{rank}.png"
            fpath = os.path.join(vis_dir, fname)
            cv2.imwrite(fpath, vis_img)
            paths.append(fpath)
        saved[algo] = paths
    return saved


# ---------------------------------------------------------------------------
# HTML Report Generation
# ---------------------------------------------------------------------------

def img_to_base64(path: str) -> str:
    """Read image file and return base64 data URI."""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"


def generate_html_report(
    all_results: dict[str, list[MatchResult]],
    config: BenchmarkConfig,
    vis_paths: dict[str, list[str]],
    video_info: dict,
) -> str:
    """Generate self-contained HTML report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = get_device(config.device_preference)

    # Compute summary stats per algorithm
    summaries = {}
    for algo, results in all_results.items():
        matches = [r.num_matches for r in results]
        confs = [r.avg_confidence for r in results]
        times = [r.elapsed_ms for r in results]
        scores = [r.composite_score for r in results]
        best = max(results, key=lambda r: r.composite_score)
        summaries[algo] = {
            "avg_matches": float(np.mean(matches)),
            "avg_confidence": float(np.mean(confs)),
            "avg_time_ms": float(np.mean(times)),
            "total_time_s": sum(times) / 1000,
            "median_composite": float(np.median(scores)),
            "best_frame": best.frame_index,
            "best_ts": best.timestamp_sec,
            "best_score": best.composite_score,
        }

    # Rank algorithms by median composite
    ranked = sorted(summaries.items(), key=lambda x: x[1]["median_composite"], reverse=True)
    rank_colors = ["#22c55e", "#eab308", "#f97316", "#ef4444"]  # green, yellow, orange, red

    # Consensus: which frames appear in top-5 of multiple algorithms
    top5_frames = {}
    for algo, results in all_results.items():
        top5 = sorted(results, key=lambda r: r.composite_score, reverse=True)[:5]
        top5_frames[algo] = set(r.frame_index for r in top5)

    all_top5 = set()
    for s in top5_frames.values():
        all_top5 |= s

    consensus = []
    for fid in sorted(all_top5):
        algos_with = [a for a, s in top5_frames.items() if fid in s]
        if len(algos_with) >= 2:
            consensus.append((fid, algos_with))
    consensus.sort(key=lambda x: len(x[1]), reverse=True)

    # Chart data
    algo_names = list(all_results.keys())
    ts_points = sorted(set(r.timestamp_sec for r in list(all_results.values())[0]))

    chart_avg_matches = [summaries[a]["avg_matches"] for a in algo_names]
    chart_avg_conf = [summaries[a]["avg_confidence"] for a in algo_names]
    chart_avg_time = [summaries[a]["avg_time_ms"] for a in algo_names]

    # Per-frame score series
    chart_score_series = {}
    for algo in algo_names:
        results_sorted = sorted(all_results[algo], key=lambda r: r.timestamp_sec)
        chart_score_series[algo] = [r.composite_score for r in results_sorted]

    # Build summary table rows
    table_rows = ""
    for rank_i, (algo, s) in enumerate(ranked):
        bg = rank_colors[rank_i] if rank_i < len(rank_colors) else "#666"
        table_rows += f"""
        <tr>
          <td><span class="badge" style="background:{bg}">{rank_i+1}</span> {algo}</td>
          <td>{s['avg_matches']:.1f}</td>
          <td>{s['avg_confidence']:.3f}</td>
          <td>{s['avg_time_ms']:.1f}</td>
          <td>{s['median_composite']:.3f}</td>
          <td>#{s['best_frame']} (t={s['best_ts']:.1f}s, score={s['best_score']:.3f})</td>
        </tr>"""

    # Build top-5 sections per algorithm
    top5_html = ""
    for algo in algo_names:
        results_sorted = sorted(all_results[algo], key=lambda r: r.composite_score, reverse=True)[:5]
        rows = ""
        for rank_i, r in enumerate(results_sorted, 1):
            rows += f"""
            <tr>
              <td>{rank_i}</td>
              <td>#{r.frame_index}</td>
              <td>{r.timestamp_sec:.1f}s</td>
              <td>{r.num_matches}</td>
              <td>{r.avg_confidence:.3f}</td>
              <td>{r.composite_score:.3f}</td>
              <td>{r.elapsed_ms:.1f}ms</td>
            </tr>"""
        top5_html += f"""
        <div class="algo-section">
          <h3>{algo}</h3>
          <table>{rows}</table>
        </div>"""

    # Visualization images
    vis_html = ""
    for algo in algo_names:
        paths = vis_paths.get(algo, [])
        if not paths:
            continue
        vis_html += f'<div class="algo-section"><h3>{algo} — Top Matches</h3><div class="vis-grid">'
        for p in paths:
            b64 = img_to_base64(p)
            vis_html += f'<div class="vis-card"><img src="{b64}" /></div>'
        vis_html += "</div></div>"

    # Consensus HTML
    consensus_html = ""
    if consensus:
        consensus_html = "<table><tr><th>Frame</th><th>Timestamp</th><th>Algorithms Agreeing</th><th>Count</th></tr>"
        frame_ts_map = {r.frame_index: r.timestamp_sec for r in list(all_results.values())[0]}
        for fid, algos in consensus:
            ts = frame_ts_map.get(fid, 0)
            consensus_html += f"""
            <tr>
              <td>#{fid}</td>
              <td>{ts:.1f}s</td>
              <td>{', '.join(algos)}</td>
              <td>{len(algos)}/{len(algo_names)}</td>
            </tr>"""
        consensus_html += "</table>"
    else:
        consensus_html = "<p>No consensus found (no frame appears in top-5 of 2+ algorithms).</p>"

    # Performance comparison
    orb_total = summaries.get("ORB", {}).get("total_time_s", 1)
    perf_rows = ""
    for algo in algo_names:
        total = summaries[algo]["total_time_s"]
        speedup = orb_total / total if total > 0 else 0
        perf_rows += f"""
        <tr>
          <td>{algo}</td>
          <td>{total:.2f}s</td>
          <td>{summaries[algo]['avg_time_ms']:.1f}ms</td>
          <td>{speedup:.2f}x vs ORB</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Image Compare Benchmark Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0f172a; color: #e2e8f0; padding: 24px; line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ font-size: 28px; margin-bottom: 8px; color: #f8fafc; }}
  h2 {{ font-size: 22px; margin: 32px 0 16px; color: #94a3b8;
       border-bottom: 1px solid #334155; padding-bottom: 8px; }}
  h3 {{ font-size: 18px; margin: 16px 0 8px; color: #cbd5e1; }}
  .meta {{ color: #64748b; margin-bottom: 24px; font-size: 14px; }}
  .meta span {{ margin-right: 16px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }}
  th {{ background: #1e293b; color: #94a3b8; padding: 10px 12px; text-align: left;
       font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #1e293b; }}
  tr:hover {{ background: #1e293b; }}
  .badge {{ display: inline-block; width: 24px; height: 24px; border-radius: 50%;
           text-align: center; line-height: 24px; font-size: 12px; font-weight: 700;
           color: #0f172a; margin-right: 8px; }}
  .chart-container {{ background: #1e293b; border-radius: 12px; padding: 24px; margin: 16px 0; }}
  .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  @media (max-width: 768px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}
  .algo-section {{ background: #1e293b; border-radius: 12px; padding: 20px; margin: 12px 0; }}
  .vis-grid {{ display: flex; flex-wrap: wrap; gap: 12px; }}
  .vis-card {{ flex: 1; min-width: 300px; }}
  .vis-card img {{ width: 100%; border-radius: 8px; border: 1px solid #334155; }}
  .consensus-highlight {{ background: #166534; color: #bbf7d0; padding: 2px 8px;
                          border-radius: 4px; font-size: 13px; }}
</style>
</head>
<body>
<div class="container">

<h1>🔍 Image Comparison Benchmark Report</h1>
<div class="meta">
  <span>📅 {now}</span>
  <span>🎬 {config.video_path} ({video_info['width']}×{video_info['height']}, {video_info['fps']:.0f}fps, {video_info['duration']:.1f}s)</span>
  <span>🖼️ {config.query_path}</span>
  <span>⚙️ Device: {device}</span>
  <span>📊 {len(list(all_results.values())[0])} frames compared</span>
</div>

<h2>📊 Algorithm Comparison Summary</h2>
<table>
  <tr>
    <th>Algorithm</th><th>Avg Matches</th><th>Avg Confidence</th>
    <th>Avg Time (ms)</th><th>Median Score</th><th>Best Frame</th>
  </tr>
  {table_rows}
</table>

<h2>📈 Performance Charts</h2>
<div class="chart-row">
  <div class="chart-container"><canvas id="chartMatches"></canvas></div>
  <div class="chart-container"><canvas id="chartConfidence"></canvas></div>
</div>
<div class="chart-row">
  <div class="chart-container"><canvas id="chartTime"></canvas></div>
  <div class="chart-container"><canvas id="chartScores"></canvas></div>
</div>

<h2>🏆 Top-5 Matching Frames per Algorithm</h2>
{top5_html}

<h2>🖼️ Match Visualizations</h2>
{vis_html}

<h2>🤝 Algorithm Consensus</h2>
<p>Frames that appear in top-5 across multiple algorithms:</p>
{consensus_html}

<h2>⏱️ Performance Comparison</h2>
<table>
  <tr><th>Algorithm</th><th>Total Time</th><th>Avg per Frame</th><th>Relative Speed</th></tr>
  {perf_rows}
</table>

</div>

<script>
const algos = {algo_names};
const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b'];
const bgColors = colors.map(c => c + '33');

new Chart(document.getElementById('chartMatches'), {{
  type: 'bar',
  data: {{
    labels: algos,
    datasets: [{{ label: 'Avg Matches', data: {chart_avg_matches},
      backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 1 }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ title: {{ display: true, text: 'Average Match Count', color: '#e2e8f0' }},
               legend: {{ labels: {{ color: '#94a3b8' }} }} }},
    scales: {{ x: {{ ticks: {{ color: '#94a3b8' }} }}, y: {{ ticks: {{ color: '#94a3b8' }} }} }}
  }}
}});

new Chart(document.getElementById('chartConfidence'), {{
  type: 'bar',
  data: {{
    labels: algos,
    datasets: [{{ label: 'Avg Confidence', data: {chart_avg_conf},
      backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 1 }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ title: {{ display: true, text: 'Average Confidence', color: '#e2e8f0' }},
               legend: {{ labels: {{ color: '#94a3b8' }} }} }},
    scales: {{ x: {{ ticks: {{ color: '#94a3b8' }} }}, y: {{ min: 0, max: 1, ticks: {{ color: '#94a3b8' }} }} }}
  }}
}});

new Chart(document.getElementById('chartTime'), {{
  type: 'bar',
  data: {{
    labels: algos,
    datasets: [{{ label: 'Avg Time (ms)', data: {chart_avg_time},
      backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 1 }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ title: {{ display: true, text: 'Average Processing Time (ms/frame)', color: '#e2e8f0' }},
               legend: {{ labels: {{ color: '#94a3b8' }} }} }},
    scales: {{ x: {{ ticks: {{ color: '#94a3b8' }} }}, y: {{ ticks: {{ color: '#94a3b8' }} }} }}
  }}
}});

new Chart(document.getElementById('chartScores'), {{
  type: 'line',
  data: {{
    labels: {ts_points},
    datasets: [
      {','.join(f'''{{
        label: '{algo}',
        data: {chart_score_series[algo]},
        borderColor: colors[{i}],
        backgroundColor: colors[{i}] + '22',
        tension: 0.3, pointRadius: 2, borderWidth: 2,
      }}''' for i, algo in enumerate(algo_names))}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ title: {{ display: true, text: 'Composite Score over Time', color: '#e2e8f0' }},
               legend: {{ labels: {{ color: '#94a3b8' }} }} }},
    scales: {{
      x: {{ title: {{ display: true, text: 'Time (s)', color: '#94a3b8' }}, ticks: {{ color: '#94a3b8' }} }},
      y: {{ title: {{ display: true, text: 'Score', color: '#94a3b8' }}, min: 0, ticks: {{ color: '#94a3b8' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    config = BenchmarkConfig()
    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(config.vis_dir, exist_ok=True)

    device = get_device(config.device_preference)
    print(f"=== Image Compare Benchmark ===")
    print(f"Device: {device}")

    # 1. Extract frames
    print("\n[1/6] Extracting frames at 1fps...")
    raw_frames = extract_frames_at_fps(config.video_path, config.extraction_fps)
    cap = cv2.VideoCapture(config.video_path)
    video_info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
    }
    cap.release()
    print(f"  Extracted {len(raw_frames)} frames ({video_info['width']}x{video_info['height']}, "
          f"{video_info['fps']:.0f}fps, {video_info['duration']:.1f}s)")

    # 2. Prepare images
    print("\n[2/6] Preparing images...")
    query_bgr = cv2.imread(config.query_path)
    query_bgr_resized = resize_bgr(query_bgr, config.max_dim)
    query_tensor = bgr_to_tensor(query_bgr_resized, device)
    query_gray = cv2.cvtColor(query_bgr_resized, cv2.COLOR_BGR2GRAY)
    print(f"  Query: {query_bgr.shape[1]}x{query_bgr.shape[0]} → {query_bgr_resized.shape[1]}x{query_bgr_resized.shape[0]}")

    # Prepare frame data (tensor + grayscale versions)
    frame_tensors = []
    frame_grays = []
    for frame_idx, ts, frame_bgr in raw_frames:
        fbgr_r = resize_bgr(frame_bgr, config.max_dim)
        ft = bgr_to_tensor(fbgr_r, device)
        fg = cv2.cvtColor(fbgr_r, cv2.COLOR_BGR2GRAY)
        frame_tensors.append((frame_idx, ts, ft))
        frame_grays.append((frame_idx, ts, fg))
    print(f"  Frames: resized to max {config.max_dim}px")

    # 3. Run benchmarks
    all_results = {}
    kornia_vis = {}

    print("\n[3/6] Running XFeat...")
    try:
        # We need to collect vis data during benchmarking
        results, _ = run_xfeat_benchmark(query_tensor, frame_tensors, device, config.warmup_runs)
        all_results["XFeat"] = results

        # Re-run top-3 for visualization
        top3 = sorted(results, key=lambda r: r.composite_score, reverse=True)[:3]
        xfeat_det = KF.XFeat.from_pretrained().to(device).eval()
        vis_entries = []
        with torch.inference_mode():
            q_out = xfeat_det.detectAndCompute(query_tensor)[0]
            for res in top3:
                if res.num_matches == 0:
                    continue
                ft = next(f for f in frame_tensors if f[0] == res.frame_index)
                f_out = xfeat_det.detectAndCompute(ft[2])[0]
                dists, indices = KF.match_mnn(q_out["descriptors"], f_out["descriptors"])
                vis_entries.append((q_out["keypoints"], f_out["keypoints"], indices, res.frame_index))
        kornia_vis["XFeat"] = vis_entries
    except Exception as e:
        print(f"  ⚠️ XFeat failed: {e}")
        all_results["XFeat"] = []

    print("\n[4/6] Running ALIKED...")
    try:
        results, _ = run_aliked_benchmark(query_tensor, frame_tensors, device, config.warmup_runs)
        all_results["ALIKED"] = results

        top3 = sorted(results, key=lambda r: r.composite_score, reverse=True)[:3]
        aliked_det = KF.ALIKED.from_pretrained("aliked-n16", device=device).eval()
        vis_entries = []
        with torch.inference_mode():
            q_feat = aliked_det(query_tensor)[0]
            for res in top3:
                if res.num_matches == 0:
                    continue
                ft = next(f for f in frame_tensors if f[0] == res.frame_index)
                f_feat = aliked_det(ft[2])[0]
                dists, indices = KF.match_mnn(q_feat.descriptors, f_feat.descriptors)
                vis_entries.append((q_feat.keypoints, f_feat.keypoints, indices, res.frame_index))
        kornia_vis["ALIKED"] = vis_entries
    except Exception as e:
        print(f"  ⚠️ ALIKED failed: {e}")
        all_results["ALIKED"] = []

    print("\n[5/6] Running LightGlue (DISK)...")
    try:
        results, _ = run_lightglue_benchmark(query_tensor, frame_tensors, device, config.warmup_runs)
        all_results["LightGlue"] = results
        # LightGlue vis: re-run top-3
        top3 = sorted(results, key=lambda r: r.composite_score, reverse=True)[:3]
        disk = KF.DISK.from_pretrained("depth", device=device).eval()
        lg_matcher = KF.LightGlue(features="disk").to(device).eval()
        vis_entries = []
        with torch.inference_mode():
            q_feats = disk(query_tensor, n=4096, pad_if_not_divisible=True)
            q_kp = q_feats[0].keypoints
            q_desc = q_feats[0].descriptors
            for res in top3:
                if res.num_matches == 0:
                    continue
                ft = next(f for f in frame_tensors if f[0] == res.frame_index)
                f_feats = disk(ft[2], n=4096, pad_if_not_divisible=True)
                f_kp = f_feats[0].keypoints
                f_desc = f_feats[0].descriptors
                data = {
                    "image0": {"keypoints": q_kp.unsqueeze(0), "descriptors": q_desc.unsqueeze(0), "image": query_tensor},
                    "image1": {"keypoints": f_kp.unsqueeze(0), "descriptors": f_desc.unsqueeze(0), "image": ft[2]},
                }
                output = lg_matcher(data)
                matched = output["matches"][0]
                if matched.shape[0] > 0:
                    idx_q = matched[:, 0].cpu().numpy()
                    idx_f = matched[:, 1].cpu().numpy()
                    indices_np = np.stack([idx_q, idx_f], axis=1)
                    vis_entries.append((q_kp, f_kp, torch.from_numpy(indices_np), res.frame_index))
        kornia_vis["LightGlue"] = vis_entries
    except Exception as e:
        print(f"  ⚠️ LightGlue failed: {e}")
        all_results["LightGlue"] = []

    print("\n[6/6] Running ORB...")
    try:
        results, orb_vis = run_orb_benchmark(query_gray, frame_grays, config.warmup_runs)
        all_results["ORB"] = results
    except Exception as e:
        print(f"  ⚠️ ORB failed: {e}")
        all_results["ORB"] = []
        orb_vis = []

    # Remove algorithms with no results
    all_results = {k: v for k, v in all_results.items() if v}

    if not all_results:
        print("\n❌ All algorithms failed. Check dependencies and try again.")
        return

    # 4. Save visualizations
    print("\nGenerating visualizations...")
    vis_paths = save_top_visualizations(
        all_results, raw_frames, query_bgr,
        kornia_vis, orb_vis, config.vis_dir, config.max_dim,
    )

    # 5. Generate HTML report
    print("Generating HTML report...")
    html = generate_html_report(all_results, config, vis_paths, video_info)
    report_path = os.path.join(config.output_dir, "benchmark_report.html")
    with open(report_path, "w") as f:
        f.write(html)
    print(f"\n✅ Report saved to: {report_path}")

    # 6. Quick summary
    print("\n" + "=" * 60)
    print("QUICK SUMMARY")
    print("=" * 60)
    for algo, results in all_results.items():
        best = max(results, key=lambda r: r.composite_score)
        avg_time = float(np.mean([r.elapsed_ms for r in results]))
        print(f"  {algo:12s} | Best: frame #{best.frame_index} "
              f"(score={best.composite_score:.3f}) | "
              f"Avg: {avg_time:.1f}ms/frame")
    print("=" * 60)


if __name__ == "__main__":
    main()
