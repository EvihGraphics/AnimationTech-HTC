"""Capture learning-oriented blog media from notebook cells.

Each screenshot is a learning card: a code-cell summary plus the concrete
result produced by that cell. Plot/log/table results are extracted from the
executed notebook outputs. Viewer/timeline results are captured from a live
JupyterLab session after running the notebook, then composited with the code
cell and widget controls.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.parse
import urllib.request
from pathlib import Path

import nbformat
from PIL import Image, ImageDraw, ImageFont, ImageOps
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BAD_TEXT = ("Traceback", "IndexError", "ModuleNotFoundError", "output_type: error")
LIVE_OUTPUT_TYPES = {"viewer", "timeline_viewer", "widget_controls", "animation_viewer"}
TEXT_OUTPUT_TYPES = {
    "log",
    "table",
    "code_log",
    "latex",
    "formula",
    "matrix",
    "command_log",
    "artifact_summary",
    "diagram",
}
PLOT_OUTPUT_TYPES = {"plot"}
MODULE_OUTPUT_TYPES = {"source_excerpt", "command_log", "artifact_summary", "diagram"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def selected_cases(manifest: dict, slugs: list[str]) -> list[dict]:
    cases = manifest["cases"]
    if not slugs:
        return cases
    wanted = set(slugs)
    picked = [case for case in cases if case["slug"] in wanted]
    missing = wanted.difference({case["slug"] for case in picked})
    if missing:
        raise SystemExit(f"Unknown media manifest slug(s): {', '.join(sorted(missing))}")
    return picked


def load_font(path: str, size: int, fallback=None):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return fallback or ImageFont.load_default()


FONT_TEXT = load_font(r"C:\Windows\Fonts\msyh.ttc", 22)
FONT_TEXT_BOLD = load_font(r"C:\Windows\Fonts\msyhbd.ttc", 26, FONT_TEXT)
FONT_CODE = load_font(r"C:\Windows\Fonts\consola.ttf", 19)
FONT_SMALL = load_font(r"C:\Windows\Fonts\msyh.ttc", 18, FONT_TEXT)


def wrap_text(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for raw in str(text).splitlines() or [""]:
        if not raw:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(raw, width=width, replace_whitespace=False) or [""])
    return lines


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill, width_chars: int, line_gap: int = 6) -> int:
    x, y = xy
    for line in wrap_text(text, width_chars):
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line or " ", font=font)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def normalize_source(source: str, max_lines: int) -> str:
    lines = source.strip("\n").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    head_count = max(4, max_lines // 2)
    tail_count = max(3, max_lines - head_count - 1)
    return "\n".join(lines[:head_count] + ["# ..."] + lines[-tail_count:])


def render_text_card(title: str, lines: list[str], width: int, font=FONT_CODE) -> Image.Image:
    padding = 22
    line_height = 24
    title_height = 34
    height = padding * 2 + title_height + max(1, len(lines)) * line_height
    image = Image.new("RGB", (width, height), (247, 249, 252))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=10, outline=(198, 208, 220), width=2)
    draw.text((padding, padding), title, font=FONT_TEXT_BOLD, fill=(36, 45, 60))
    y = padding + title_height
    for line in lines or [""]:
        draw.text((padding, y), line[:180], font=font, fill=(23, 34, 48))
        y += line_height
    return image


def render_code_card(source: str, width: int, max_lines: int, title: str = "Code cell") -> Image.Image:
    code = normalize_source(source, max_lines)
    return render_text_card(title, code.splitlines(), width, FONT_CODE)


def render_explanation_card(step: dict, width: int) -> Image.Image:
    padding = 22
    lines = []
    lines.append(f"Purpose: {step.get('code_purpose', '')}")
    lines.append(f"Result: {step.get('result_meaning', '')}")
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(wrap_text(line, 74))
    height = padding * 2 + max(1, len(wrapped)) * 30
    image = Image.new("RGB", (width, height), (255, 251, 235))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=10, outline=(221, 190, 124), width=2)
    y = padding
    for line in wrapped:
        draw.text((padding, y), line, font=FONT_SMALL, fill=(70, 55, 24))
        y += 30
    return image


def fit_image(image: Image.Image, max_width: int) -> Image.Image:
    image = image.convert("RGB")
    if image.width <= max_width:
        return image
    ratio = max_width / image.width
    return image.resize((max_width, max(1, int(image.height * ratio))), Image.Resampling.LANCZOS)


def step_label(step: dict) -> str:
    if "cell_index" in step:
        return f"Cell {step['cell_index']}"
    return step.get("source_label") or step.get("symbol") or "Source"


def build_learning_card(step: dict, source: str, result_images: list[Image.Image], card_conf: dict) -> Image.Image:
    width = int(card_conf.get("width", 1280))
    max_code_lines = int(card_conf.get("max_code_lines", 18))
    gap = 18
    margin = 28
    title_lines = wrap_text(f"{step_label(step)} - {step['title']}", 70)
    title_height = 36 + len(title_lines) * 34
    code_title = "Code cell" if "cell_index" in step else "Source excerpt"
    code_card = fit_image(render_code_card(source, width, max_code_lines, code_title), width)
    explanation = fit_image(render_explanation_card(step, width), width)
    fitted_results = [fit_image(img, width) for img in result_images if img is not None]
    if not fitted_results:
        fitted_results = [render_text_card("Output", ["This cell prepares state for later visual outputs."], width, FONT_TEXT)]

    total_height = margin * 2 + title_height + code_card.height + explanation.height + gap * (2 + len(fitted_results))
    total_height += sum(img.height for img in fitted_results)
    canvas = Image.new("RGB", (width + margin * 2, total_height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    y = margin
    for line in title_lines:
        draw.text((margin, y), line, font=FONT_TEXT_BOLD, fill=(20, 28, 42))
        y += 34
    y += gap
    canvas.paste(code_card, (margin, y))
    y += code_card.height + gap
    for img in fitted_results:
        canvas.paste(img, (margin, y))
        y += img.height + gap
    canvas.paste(explanation, (margin, y))
    return canvas


def compose_learning_card(step: dict, source: str, result_images: list[Image.Image], target_path: Path, card_conf: dict) -> None:
    canvas = build_learning_card(step, source, result_images, card_conf)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target_path)
    validate_png(target_path)


def output_text(output) -> str:
    if "text" in output:
        value = output.get("text", "")
        return "".join(value) if isinstance(value, list) else str(value)
    data = output.get("data", {})
    for key in ("text/plain", "text/html", "text/latex"):
        if key in data:
            value = data[key]
            return "".join(value) if isinstance(value, list) else str(value)
    return ""


def image_from_executed_output(nb, step: dict) -> Image.Image | None:
    cell = nb.cells[int(step["cell_index"])]
    for output in cell.get("outputs", []):
        data = output.get("data", {})
        if "image/png" in data:
            raw = data["image/png"]
            if isinstance(raw, list):
                raw = "".join(raw)
            return Image.open(io.BytesIO(base64.b64decode(raw))).convert("RGB")
    return None


def text_image_from_executed_output(nb, step: dict, width: int) -> Image.Image:
    cell = nb.cells[int(step["cell_index"])]
    chunks: list[str] = []
    for output in cell.get("outputs", []):
        text = output_text(output).strip()
        if text:
            chunks.append(text)
    if not chunks:
        chunks.append("No direct textual output. The cell mutates notebook state for later visualization.")
    text = "\n".join(chunks)
    lines = []
    for line in text.splitlines():
        lines.extend(wrap_text(line, 110))
    if len(lines) > 45:
        lines = lines[:22] + ["..."] + lines[-18:]
    return render_text_card("Cell output", lines, width, FONT_CODE)


def extract_source_excerpt(path: Path, step: dict) -> str:
    if not path.exists():
        return f"Missing source file: {path}"
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    source_range = step.get("source_range")
    if isinstance(source_range, list) and len(source_range) == 2:
        start = max(1, int(source_range[0]))
        end = min(len(lines), int(source_range[1]))
        return "\n".join(f"{line_no:04d}: {lines[line_no - 1]}" for line_no in range(start, end + 1))

    symbol = step.get("symbol")
    if symbol:
        start_index = None
        for index, line in enumerate(lines):
            if line.startswith(f"def {symbol}") or line.startswith(f"class {symbol}") or line.startswith(f"{symbol} ="):
                start_index = index
                break
        if start_index is not None:
            end_index = min(len(lines), start_index + int(step.get("source_context_lines", 24)))
            return "\n".join(f"{line_no + 1:04d}: {lines[line_no]}" for line_no in range(start_index, end_index))

    return "\n".join(f"{line_no + 1:04d}: {line}" for line_no, line in enumerate(lines[: int(step.get("source_context_lines", 24))]))


def text_lines_from_file(path: Path) -> list[str]:
    if not path.exists():
        return [f"Missing file: {path}"]
    text = path.read_text(encoding="utf-8-sig", errors="replace").strip()
    if not text:
        return ["Command completed successfully with no stdout/stderr output."]
    return text.splitlines()


def summarize_artifact(path: Path) -> list[str]:
    if not path.exists():
        return [f"Missing artifact: {path}"]
    lines = [f"path: {path}", f"size_bytes: {path.stat().st_size}"]
    if path.suffix.lower() == ".dat":
        try:
            import pickle

            with path.open("rb") as handle:
                payload = pickle.load(handle)
            if isinstance(payload, tuple) and len(payload) == 3:
                indices, normals, frames = payload
                lines.extend(
                    [
                        f"indices_count: {len(indices)}",
                        f"normals_count: {len(normals)}",
                        f"frame_count: {len(frames)}",
                    ]
                )
                if frames:
                    lines.append(f"vertices_per_frame: {len(frames[0])}")
        except Exception as exc:  # pragma: no cover - summary should degrade gracefully.
            lines.append(f"pickle_summary_error: {type(exc).__name__}: {exc}")
    return lines


def module_result_images(root: Path, step: dict, width: int) -> list[Image.Image]:
    output_type = step.get("output_type")
    if output_type == "command_log":
        log_path = root / step.get("log_path", "")
        return [render_text_card("Command log", text_lines_from_file(log_path), width, FONT_CODE)]
    if output_type == "artifact_summary":
        artifact_path = root / step.get("artifact_path", "")
        return [render_text_card("Artifact summary", summarize_artifact(artifact_path), width, FONT_CODE)]
    if output_type == "diagram":
        return [render_text_card("Module flow", step.get("diagram_lines", []), width, FONT_TEXT)]
    return [render_text_card("Source evidence", [step.get("result_meaning", "Source excerpt explains this module behavior.")], width, FONT_TEXT)]


def notebook_has_error_outputs(notebook_path: Path) -> list[str]:
    notebook = nbformat.read(notebook_path, as_version=4)
    errors: list[str] = []
    for cell_index, cell in enumerate(notebook.cells):
        if cell.get("cell_type") != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(f"cell {cell_index}: {output.get('ename', 'error')}")
    return errors


def find_live_jupyter_server() -> dict:
    root = repo_root()
    runtime_dir = root / ".jupyter-runtime"
    candidates = sorted(runtime_dir.glob("jpserver-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    socket.setdefaulttimeout(1.0)
    for runtime_file in candidates:
        try:
            info = json.loads(runtime_file.read_text(encoding="utf-8"))
            if Path(info.get("root_dir", "")).resolve() != root:
                continue
            status_url = info["url"].rstrip("/") + "/api/status?token=" + info.get("token", "")
            with urllib.request.urlopen(status_url, timeout=1.0) as response:
                if response.status == 200:
                    return info
        except Exception:
            continue
    raise RuntimeError("No live JupyterLab server found. Run tools/start_animationpapers_lab.ps1 -NoOpen first.")


def lab_url(server: dict, case: dict) -> str:
    notebook = urllib.parse.quote(case["notebook"]).replace("%2F", "/")
    workspace = "blog-media-" + case["slug"]
    return f"{server['url'].rstrip('/')}/lab/workspaces/{workspace}/tree/{notebook}?reset&token={server['token']}"


def click_jupyter_news_no(page) -> None:
    try:
        page.get_by_text("No", exact=True).click(timeout=1200)
    except Exception:
        pass


def api_kernel_state(server: dict, notebook_path: str) -> str | None:
    url = server["url"].rstrip("/") + "/api/sessions?token=" + urllib.parse.quote(server["token"])
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            sessions = json.load(response)
    except Exception:
        return None
    normalized = notebook_path.replace("\\", "/")
    for session in sessions:
        if session.get("path", "").replace("\\", "/") == normalized:
            kernel = session.get("kernel") or {}
            return kernel.get("execution_state")
    return None


def run_all_cells(page, server: dict, case: dict, timeout_seconds: int) -> None:
    page.get_by_text("Run", exact=True).click(timeout=10_000)
    page.wait_for_timeout(300)
    page.get_by_text("Run All Cells", exact=True).click(timeout=10_000)
    page.wait_for_timeout(2000)
    deadline = time.time() + timeout_seconds
    stable_idle = 0
    while time.time() < deadline:
        click_jupyter_news_no(page)
        api_state = api_kernel_state(server, case["notebook"])
        running_prompts = page.locator(".jp-InputPrompt").filter(has_text="[*]").count()
        busy = api_state == "busy" or (api_state is None and running_prompts > 0)
        if not busy:
            stable_idle += 1
            if stable_idle >= 3:
                return
        else:
            stable_idle = 0
        page.wait_for_timeout(1500)
    raise TimeoutError(f"Notebook did not become idle within {timeout_seconds} seconds.")


def scan_page_for_errors(page, slug: str) -> None:
    text = page.locator("body").inner_text(timeout=30_000)
    found = [token for token in BAD_TEXT if token in text]
    if found:
        raise RuntimeError(f"{slug}: live notebook contains error text: {', '.join(found)}")
    error_outputs = page.locator(".jp-OutputArea-output.jp-mod-error").count()
    if error_outputs:
        raise RuntimeError(f"{slug}: live notebook has {error_outputs} red error output(s).")


def cell_output_locator(page, cell_index: int):
    cell = page.locator(".jp-Notebook-cell").nth(cell_index)
    output = cell.locator(".jp-OutputArea").first
    return cell, output


def set_first_slider(output, fraction: float) -> bool:
    sliders = output.locator("input[type='range']")
    if sliders.count() == 0:
        return False
    slider = sliders.first
    slider.evaluate(
        """(node, fraction) => {
            const min = Number(node.min || 0);
            const max = Number(node.max || 100);
            const value = min + (max - min) * fraction;
            node.value = String(value);
            node.dispatchEvent(new Event('input', {bubbles: true}));
            node.dispatchEvent(new Event('change', {bubbles: true}));
        }""",
        fraction,
    )
    return True


def set_sliders(output, step: dict) -> None:
    slider_fractions = step.get("slider_fractions")
    if isinstance(slider_fractions, list):
        sliders = output.locator("input[type='range']")
        for index, fraction in enumerate(slider_fractions):
            if index < sliders.count():
                sliders.nth(index).evaluate(
                    """(node, fraction) => {
                        const min = Number(node.min || 0);
                        const max = Number(node.max || 100);
                        const value = min + (max - min) * fraction;
                        node.value = String(value);
                        node.dispatchEvent(new Event('input', {bubbles: true}));
                        node.dispatchEvent(new Event('change', {bubbles: true}));
                    }""",
                    float(fraction),
                )
        return
    set_first_slider(output, float(step.get("slider_fraction", 0.5)))


def set_checkboxes(output, indices: list[int]) -> None:
    if not indices:
        return
    boxes = output.locator("input[type='checkbox']")
    for index in indices:
        if index < boxes.count():
            boxes.nth(index).evaluate(
                """(node) => {
                    node.checked = true;
                    node.dispatchEvent(new Event('input', {bubbles: true}));
                    node.dispatchEvent(new Event('change', {bubbles: true}));
                }"""
            )


def element_to_image(locator, label: str) -> Image.Image | None:
    if locator.count() == 0:
        return None
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        path = Path(handle.name)
    try:
        locator.screenshot(path=str(path), timeout=12_000)
        image = Image.open(path).convert("RGB")
        if image.width < 20 or image.height < 20:
            return None
        if label:
            return add_image_label(image, label)
        return image
    except PlaywrightTimeoutError:
        return None
    finally:
        path.unlink(missing_ok=True)


def add_image_label(image: Image.Image, label: str) -> Image.Image:
    label_height = 36
    output = Image.new("RGB", (image.width, image.height + label_height), (245, 247, 250))
    draw = ImageDraw.Draw(output)
    draw.text((14, 7), label, font=FONT_SMALL, fill=(48, 57, 72))
    output.paste(image, (0, label_height))
    return output


def capture_live_result(page, step: dict) -> list[Image.Image]:
    cell, output = cell_output_locator(page, int(step["cell_index"]))
    cell.scroll_into_view_if_needed(timeout=10_000)
    page.wait_for_timeout(500)
    if output.count() > 0:
        set_checkboxes(output, step.get("checkbox_indices", []))
        set_sliders(output, step)
    page.wait_for_timeout(1200)

    images: list[Image.Image] = []
    controls = element_to_image(output, "Cell output controls / widget state") if output.count() > 0 else None
    if controls is not None and controls.height >= 50:
        images.append(controls)

    target_canvas = output.locator("canvas").last if output.count() > 0 and output.locator("canvas").count() > 0 else None
    canvas = target_canvas or page.locator("canvas").last
    if canvas.count() > 0:
        canvas.scroll_into_view_if_needed(timeout=10_000)
        page.wait_for_timeout(500)
        canvas_image = element_to_image(canvas, "Live animation viewer / canvas")
        if canvas_image is not None:
            images.append(canvas_image)

    if not images:
        fallback = element_to_image(cell, "Cell output")
        if fallback is not None:
            images.append(fallback)
    return images


def png_size(path: Path) -> tuple[int, int] | None:
    header = path.read_bytes()[:24]
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    return struct.unpack(">II", header[16:24])


def validate_png(path: Path) -> None:
    size = png_size(path)
    if size is None:
        raise RuntimeError(f"{path} is not a readable PNG")
    width, height = size
    if width < 800 or height < 450:
        raise RuntimeError(f"{path} is too small for a learning screenshot: {width}x{height}")
    if path.stat().st_size < 10_000:
        raise RuntimeError(f"{path} is suspiciously tiny: {path.stat().st_size} bytes")


def encode_webm(frames: list[Path], output_path: Path, fps: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode WebM walkthroughs.")
    pattern = str(frames[0].parent / "frame_%04d.png")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            pattern,
            "-an",
            "-c:v",
            "libvpx-vp9",
            "-b:v",
            "0",
            "-crf",
            "38",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def ffprobe_duration(video_path: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def validate_video(video_path: Path, max_seconds: int, max_bytes: int) -> None:
    size = video_path.stat().st_size
    if size <= 0:
        raise RuntimeError(f"{video_path} is empty.")
    if size > max_bytes:
        raise RuntimeError(f"{video_path} is too large: {size} bytes.")
    duration = ffprobe_duration(video_path)
    if duration is not None and duration > max_seconds + 0.75:
        raise RuntimeError(f"{video_path} is too long: {duration:.2f}s.")


def make_video_from_cards(case: dict, video_conf: dict, assets_dir: Path) -> None:
    frames_dir = Path(tempfile.mkdtemp(prefix=f"blog_media_{case['slug']}_frames_"))
    target_count = max(12, min(48, int(video_conf["max_seconds"]) * int(video_conf.get("fps", 4))))
    steps = case["steps"]
    frames: list[Path] = []
    for index in range(target_count):
        step = steps[int(index * len(steps) / target_count)]
        source = assets_dir / step["file"]
        with Image.open(source) as image:
            frame = ImageOps.contain(image.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (1280, 720), (255, 255, 255))
            canvas.paste(frame, ((1280 - frame.width) // 2, (720 - frame.height) // 2))
            frame_path = frames_dir / f"frame_{index:04d}.png"
            canvas.save(frame_path)
            frames.append(frame_path)
    output_path = assets_dir / video_conf["file"]
    encode_webm(frames, output_path, int(video_conf.get("fps", 4)))
    validate_video(output_path, int(video_conf["max_seconds"]), int(video_conf["max_bytes"]))


def fit_video_frame(image: Image.Image) -> Image.Image:
    frame = ImageOps.contain(image.convert("RGB"), (1280, 720), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (1280, 720), (255, 255, 255))
    canvas.paste(frame, ((1280 - frame.width) // 2, (720 - frame.height) // 2))
    return canvas


def choose_live_video_step(case: dict) -> dict | None:
    for output_type in ("timeline_viewer", "viewer", "animation_viewer", "widget_controls"):
        for step in case["steps"]:
            if step.get("output_type") == output_type:
                return step
    return None


def make_video_from_live(page, case: dict, source_nb, video_conf: dict, assets_dir: Path, card_conf: dict) -> None:
    base_step = choose_live_video_step(case)
    if base_step is None:
        make_video_from_cards(case, video_conf, assets_dir)
        return

    frames_dir = Path(tempfile.mkdtemp(prefix=f"blog_media_{case['slug']}_live_frames_"))
    target_count = max(12, min(48, int(video_conf["max_seconds"]) * int(video_conf.get("fps", 4))))
    sample_count = min(12, target_count)
    source = source_nb.cells[int(base_step["cell_index"])].source
    sample_frames: list[Image.Image] = []

    for sample_index in range(sample_count):
        fraction = sample_index / max(1, sample_count - 1)
        step = dict(base_step)
        step["slider_fraction"] = fraction
        step["title"] = f"{base_step['title']} - timeline sample {sample_index + 1}"
        result_images = capture_live_result(page, step)
        sample_frames.append(fit_video_frame(build_learning_card(step, source, result_images, card_conf)))

    frames: list[Path] = []
    for index in range(target_count):
        frame = sample_frames[int(index * len(sample_frames) / target_count)]
        frame_path = frames_dir / f"frame_{index:04d}.png"
        frame.save(frame_path)
        frames.append(frame_path)

    output_path = assets_dir / video_conf["file"]
    encode_webm(frames, output_path, int(video_conf.get("fps", 4)))
    validate_video(output_path, int(video_conf["max_seconds"]), int(video_conf["max_bytes"]))


def capture_module_case(case: dict, manifest: dict) -> None:
    root = repo_root()
    slug = case["slug"]
    source_path = root / case["source_path"]
    assets_dir = root / case["assets_dir"]
    assets_dir.mkdir(parents=True, exist_ok=True)
    if not source_path.exists():
        raise FileNotFoundError(f"{slug}: source module missing: {source_path}")

    for step in case["steps"]:
        step_source_path = root / step.get("source_path", case["source_path"])
        source = extract_source_excerpt(step_source_path, step)
        images = module_result_images(root, step, int(manifest["card"]["width"]))
        compose_learning_card(step, source, images, assets_dir / step["file"], manifest["card"])

    make_video_from_cards(case, manifest["video"], assets_dir)
    print(f"captured {slug}: {len(case['steps'])} module cards + {manifest['video']['file']}")


def capture_case(case: dict, manifest: dict, server: dict | None, browser, run_timeout: int, skip_run: bool) -> None:
    root = repo_root()
    slug = case["slug"]
    if case.get("kind") == "python_module":
        capture_module_case(case, manifest)
        return

    notebook_path = root / case["notebook"]
    executed_path = root / case["executed_notebook"]
    assets_dir = root / case["assets_dir"]
    assets_dir.mkdir(parents=True, exist_ok=True)

    if not notebook_path.exists():
        raise FileNotFoundError(f"{slug}: notebook missing: {notebook_path}")
    if not executed_path.exists():
        raise FileNotFoundError(f"{slug}: executed notebook missing: {executed_path}")

    errors = notebook_has_error_outputs(executed_path)
    if errors:
        raise RuntimeError(f"{slug}: executed notebook has error outputs: {errors}")

    source_nb = nbformat.read(notebook_path, as_version=4)
    executed_nb = nbformat.read(executed_path, as_version=4)
    needs_live = any(step.get("output_type") in LIVE_OUTPUT_TYPES for step in case["steps"])

    page = None
    if needs_live:
        if server is None:
            raise RuntimeError(f"{slug}: live JupyterLab server is required for viewer captures.")
        page = browser.new_page(viewport=manifest["viewport"])
        page.goto(lab_url(server, case), wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(10_000)
        expected_cells = len(source_nb.cells)
        actual_cells = page.locator(".jp-Notebook-cell").count()
        if actual_cells != expected_cells:
            raise RuntimeError(f"{slug}: expected {expected_cells} cells in JupyterLab, found {actual_cells}")
        click_jupyter_news_no(page)
        if not skip_run:
            run_all_cells(page, server, case, run_timeout)
        scan_page_for_errors(page, slug)

    for step in case["steps"]:
        cell_index = int(step["cell_index"])
        source = source_nb.cells[cell_index].source
        output_type = step.get("output_type")
        result_images: list[Image.Image] = []
        if output_type in LIVE_OUTPUT_TYPES:
            result_images = capture_live_result(page, step) if page is not None else []
        elif output_type in PLOT_OUTPUT_TYPES:
            image = image_from_executed_output(executed_nb, step)
            if image is None:
                image = text_image_from_executed_output(executed_nb, step, int(manifest["card"]["width"]))
            result_images = [add_image_label(image, "Executed cell plot/output")]
        elif output_type in TEXT_OUTPUT_TYPES:
            result_images = [text_image_from_executed_output(executed_nb, step, int(manifest["card"]["width"]))]
        else:
            result_images = [render_text_card("Cell output", ["This cell prepares data for downstream visualization."], int(manifest["card"]["width"]), FONT_TEXT)]

        compose_learning_card(step, source, result_images, assets_dir / step["file"], manifest["card"])

    if page is not None and case.get("video_step", {}).get("mode") == "live_timeline":
        make_video_from_live(page, case, source_nb, manifest["video"], assets_dir, manifest["card"])
        page.close()
    else:
        if page is not None:
            page.close()
        make_video_from_cards(case, manifest["video"], assets_dir)
    print(f"captured {slug}: {len(case['steps'])} learning cards + {manifest['video']['file']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="docs/blog/media_manifest.json")
    parser.add_argument("--slug", action="append", default=[])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--run-timeout", type=int, default=900)
    parser.add_argument("--skip-run", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    manifest = load_manifest(root / args.manifest)
    if int(manifest.get("version", 1)) < 3:
        raise SystemExit("media manifest must be version 3 learning-card schema")
    slugs = [] if args.all else args.slug
    if not args.all and not slugs:
        parser.error("pass --all or one or more --slug values")

    cases = selected_cases(manifest, slugs)
    needs_live = any(any(step.get("output_type") in LIVE_OUTPUT_TYPES for step in case["steps"]) for case in cases)
    server = find_live_jupyter_server() if needs_live else None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--use-gl=swiftshader", "--enable-webgl"])
        try:
            for case in cases:
                capture_case(case, manifest, server, browser, args.run_timeout, args.skip_run)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
