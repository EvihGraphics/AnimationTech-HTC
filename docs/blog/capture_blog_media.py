"""Capture learning-oriented blog media from notebook cells.

The v5 blog media schema separates two artifacts:

* result media used in README prose (result-only PNG, GIF, MP4, WebM)
* code learning cards kept as reproducible evidence

Plot/log/table results are extracted from executed notebook outputs.
Viewer/timeline results are captured from a live JupyterLab session when
available. A derive-from-cards mode can rebuild v5 assets from legacy cards so
schema migrations do not require a full live recapture.
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

from jupyter_client import BlockingKernelClient
import nbformat
from PIL import Image, ImageDraw, ImageFont, ImageOps
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BAD_TEXT = (
    "Traceback",
    "IndexError",
    "ModuleNotFoundError",
    "output_type: error",
    "Error displaying widget",
    "model not found",
)
LIVE_OUTPUT_TYPES = {"viewer", "timeline_viewer", "widget_controls", "animation_viewer"}
ALLOWED_CAPTURE_KINDS = {
    "canvas",
    "plot",
    "table",
    "formula",
    "widget_controls",
    "artifact_summary",
    "code_evidence",
}
REAL_MEDIA_PROVENANCE = {
    "live_canvas",
    "executed_plot_image",
    "executed_text_card",
    "executed_table_card",
    "executed_formula_card",
    "live_widget_controls",
    "artifact_summary",
    "code_evidence",
}
DERIVED_CARD_PROVENANCE = "derived_card_crop"
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


def card_file(step: dict) -> str:
    return step.get("card_file") or step.get("file")


def result_file(step: dict) -> str:
    value = step.get("result_file")
    if not value:
        raise RuntimeError(f"{step_label(step)}: result_file is required for result media.")
    if value == card_file(step):
        raise RuntimeError(f"{step_label(step)}: result_file must not point at the learning card.")
    return value


def capture_kind(step: dict) -> str:
    kind = step.get("capture_kind")
    if kind is None:
        output_type = step.get("output_type")
        if output_type in {"viewer", "timeline_viewer", "animation_viewer"}:
            kind = "canvas"
        elif output_type == "widget_controls":
            kind = "widget_controls"
        elif output_type == "plot":
            kind = "plot"
        elif output_type in {"table", "matrix"}:
            kind = "table"
        elif output_type in {"latex", "formula"}:
            kind = "formula"
        elif output_type == "artifact_summary":
            kind = "artifact_summary"
        elif output_type in {"source_excerpt", "command_log", "code_log", "diagram"}:
            kind = "code_evidence"
        else:
            kind = "code_evidence"
    if kind not in ALLOWED_CAPTURE_KINDS:
        raise RuntimeError(f"{step_label(step)}: unsupported capture_kind {kind!r}.")
    return kind


def visual_subject(step: dict) -> str:
    return step.get("visual_subject") or step.get("title") or step_label(step)


def media_provenance(step: dict, default: str) -> str:
    return step.get("media_provenance") or default


def concrete_provenance(step: dict, default: str) -> str:
    manifest_value = step.get("media_provenance")
    aliases = {
        "executed_plot_output": "executed_plot_image",
        "executed_structured_output": "executed_table_card",
        "executed_formula_output": "executed_formula_card",
        "generated_artifact_summary": "artifact_summary",
        "generated_code_evidence": "code_evidence",
    }
    return aliases.get(manifest_value, manifest_value or default)


def publish_media_required(step: dict) -> set[str]:
    required = step.get("publish_media_required", [])
    if isinstance(required, str):
        return {required}
    if isinstance(required, list):
        return {str(value) for value in required}
    if isinstance(required, bool):
        return {"key_visual"} if required else set()
    return set()


def is_key_publish_media(step: dict) -> bool:
    return bool(publish_media_required(step).intersection({"key_visual", "key_animation"}))


def step_needs_motion_media(step: dict) -> bool:
    if step.get("output_type") == "timeline_viewer":
        return True
    for control in step.get("controls", []):
        if control.get("kind") == "slider" and control.get("role") == "parameter":
            return True
    return False


def save_result_media(result_images: list[Image.Image], target_path: Path, width: int) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fitted = [fit_image(image, width) for image in result_images if image is not None]
    if not fitted:
        fitted = [render_text_card("Output", ["No visual output was captured."], width, FONT_TEXT)]
    gap = 16
    margin = 18
    canvas_width = max(image.width for image in fitted) + margin * 2
    total_height = margin * 2 + sum(image.height for image in fitted) + gap * (len(fitted) - 1)
    canvas = Image.new("RGB", (canvas_width, total_height), (255, 255, 255))
    y = margin
    for image in fitted:
        canvas.paste(image, (margin, y))
        y += image.height + gap
    canvas.save(target_path)
    validate_png(target_path, min_width=320, min_height=150, min_bytes=4000)


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
    kind = capture_kind(step)
    if output_type == "command_log":
        if kind != "code_evidence":
            raise RuntimeError(f"{step_label(step)}: command_log requires capture_kind=code_evidence.")
        log_path = root / step.get("log_path", "")
        return [render_text_card("Command log", text_lines_from_file(log_path), width, FONT_CODE)]
    if output_type == "artifact_summary":
        if kind != "artifact_summary":
            raise RuntimeError(f"{step_label(step)}: artifact_summary requires capture_kind=artifact_summary.")
        artifact_path = root / step.get("artifact_path", "")
        return [render_text_card("Artifact summary", summarize_artifact(artifact_path), width, FONT_CODE)]
    if output_type == "diagram":
        if kind != "code_evidence":
            raise RuntimeError(f"{step_label(step)}: diagram requires capture_kind=code_evidence.")
        return [render_text_card("Module flow", step.get("diagram_lines", []), width, FONT_TEXT)]
    if kind != "code_evidence":
        raise RuntimeError(f"{step_label(step)}: module evidence requires capture_kind=code_evidence.")
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


def api_kernel_id(server: dict, notebook_path: str) -> str | None:
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
            return kernel.get("id")
    return None


def kernel_connection_file(server: dict, notebook_path: str) -> Path:
    kernel_id = api_kernel_id(server, notebook_path)
    if not kernel_id:
        raise RuntimeError(f"Cannot find live kernel for {notebook_path}.")
    path = repo_root() / ".jupyter-runtime" / f"kernel-{kernel_id}.json"
    if not path.exists():
        raise RuntimeError(f"Cannot find kernel connection file: {path}")
    return path


def execute_kernel_code(connection_file: Path, code: str, timeout_seconds: int = 60) -> None:
    client = BlockingKernelClient()
    client.load_connection_file(str(connection_file))
    client.start_channels()
    try:
        message_id = client.execute(code, store_history=False)
        deadline = time.time() + timeout_seconds
        errors: list[str] = []
        while time.time() < deadline:
            try:
                message = client.get_iopub_msg(timeout=1)
            except Exception:
                continue
            if message.get("parent_header", {}).get("msg_id") != message_id:
                continue
            msg_type = message.get("msg_type")
            content = message.get("content", {})
            if msg_type == "error":
                errors.append("\n".join(content.get("traceback") or [content.get("ename", "error")]))
            if msg_type == "status" and content.get("execution_state") == "idle":
                if errors:
                    raise RuntimeError("Kernel render command failed:\n" + "\n".join(errors))
                return
        raise TimeoutError("Kernel render command timed out.")
    finally:
        client.stop_channels()


def run_all_cells(page, server: dict, case: dict, timeout_seconds: int) -> None:
    page.locator(".jp-Notebook-cell").nth(1).click(timeout=10_000)
    page.wait_for_timeout(300)
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


def set_slider_by_index(output, index: int, fraction: float) -> bool:
    sliders = output.locator("input[type='range']")
    if index >= sliders.count():
        return False
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
    return True


def set_checkbox_by_index(output, index: int, checked: bool) -> bool:
    boxes = output.locator("input[type='checkbox']")
    if index >= boxes.count():
        return False
    boxes.nth(index).evaluate(
        """(node, checked) => {
            node.checked = Boolean(checked);
            node.dispatchEvent(new Event('input', {bubbles: true}));
            node.dispatchEvent(new Event('change', {bubbles: true}));
        }""",
        bool(checked),
    )
    return True


def control_fraction(step: dict, control: dict) -> float:
    if control.get("role") == "timeline" and "slider_fraction" in step:
        return float(step["slider_fraction"])
    return float(control.get("fraction", step.get("slider_fraction", 0.5)))


def set_sliders(output, step: dict) -> None:
    controls = step.get("controls")
    if isinstance(controls, list):
        for control in controls:
            if control.get("kind") == "slider":
                if not set_slider_by_index(output, int(control.get("index", 0)), control_fraction(step, control)):
                    raise RuntimeError(f"{step_label(step)}: slider control index {control.get('index', 0)} was not found.")
        return
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
    for index in indices:
        if not set_checkbox_by_index(output, index, True):
            raise RuntimeError(f"Checkbox control index {index} was not found.")


def set_controls(output, step: dict) -> None:
    if output.count() == 0:
        return
    controls = step.get("controls")
    if isinstance(controls, list):
        for control in controls:
            if control.get("kind") == "slider":
                if not set_slider_by_index(output, int(control.get("index", 0)), control_fraction(step, control)):
                    raise RuntimeError(f"{step_label(step)}: slider control index {control.get('index', 0)} was not found.")
            elif control.get("kind") == "checkbox":
                if not set_checkbox_by_index(output, int(control.get("index", 0)), bool(control.get("checked", True))):
                    raise RuntimeError(f"{step_label(step)}: checkbox control index {control.get('index', 0)} was not found.")
        return
    set_checkboxes(output, step.get("checkbox_indices", []))
    set_sliders(output, step)


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


def raw_element_image(locator) -> Image.Image | None:
    if locator.count() == 0:
        return None
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        path = Path(handle.name)
    try:
        locator.screenshot(path=str(path), timeout=12_000)
        image = Image.open(path).convert("RGB")
        if image.width < 20 or image.height < 20:
            return None
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


def compose_labeled_montage(items: list[tuple[str, Image.Image]], width: int = 1280) -> Image.Image:
    if not items:
        raise RuntimeError("Cannot compose an empty live-canvas montage.")
    margin = 18
    gap = 16
    label_height = 34
    column_width = max(180, int((width - margin * 2 - gap * (len(items) - 1)) / len(items)))
    fitted: list[tuple[str, Image.Image]] = []
    for label, image in items:
        fitted.append((label, ImageOps.contain(image.convert("RGB"), (column_width, 720), Image.Resampling.LANCZOS)))
    content_height = max(image.height for _, image in fitted)
    height = margin * 2 + label_height + content_height
    output = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(output)
    x = margin
    for label, image in fitted:
        draw.text((x, margin), label, font=FONT_SMALL, fill=(30, 41, 59))
        output.paste(image, (x, margin + label_height))
        x += column_width + gap
    return output


def column_sidebar_fraction(image: Image.Image, x: int) -> float:
    pixels = image.convert("RGB").load()
    sidebar = 0
    for y in range(image.height):
        r, g, b = pixels[x, y]
        gray = abs(r - g) <= 4 and abs(g - b) <= 4 and 25 <= r <= 170
        dark_edge = r <= 18 and g <= 22 and b <= 30
        if gray or dark_edge:
            sidebar += 1
    return sidebar / max(1, image.height)


def crop_canvas_render_area(image: Image.Image) -> Image.Image:
    source = image.convert("RGB")
    right = source.width
    while right > int(source.width * 0.5) and column_sidebar_fraction(source, right - 1) > 0.96:
        right -= 1
    while right > int(source.width * 0.5) and column_sidebar_fraction(source, right - 1) > 0.90:
        right -= 1
    if right < source.width - 20:
        return source.crop((0, 0, right, source.height))
    return source


def locator_text(locator) -> str:
    try:
        return locator.inner_text(timeout=1500)
    except Exception:
        return ""


def image_stats(image: Image.Image) -> dict:
    sample = ImageOps.contain(image.convert("RGB"), (160, 160), Image.Resampling.BILINEAR)
    pixels = list(sample.getdata())
    count = max(1, len(pixels))
    channel_means = [sum(pixel[index] for pixel in pixels) / count for index in range(3)]
    grayish = sum(1 for r, g, b in pixels if abs(r - g) < 4 and abs(g - b) < 4 and 80 <= r <= 245) / count
    near_white = sum(1 for r, g, b in pixels if r > 248 and g > 248 and b > 248) / count
    near_uniform = len({(r // 8, g // 8, b // 8) for r, g, b in pixels}) <= 6
    variance = sum(sum((pixel[index] - channel_means[index]) ** 2 for index in range(3)) for pixel in pixels) / count
    return {
        "grayish": grayish,
        "near_white": near_white,
        "near_uniform": near_uniform,
        "variance": variance,
    }


def validate_captured_subject(image: Image.Image, kind: str, subject: str, text: str = "") -> None:
    if image.width < 80 or image.height < 60:
        raise RuntimeError(f"{subject}: captured {kind} is too small: {image.width}x{image.height}.")
    bad_text = [token for token in BAD_TEXT if token in text]
    chrome_text = ["Run All Cells", "Code", "Markdown", "Python 3", "Trusted", "No Kernel"]
    bad_text.extend(token for token in chrome_text if token in text)
    if bad_text:
        raise RuntimeError(f"{subject}: captured {kind} includes notebook chrome/error text: {', '.join(sorted(set(bad_text)))}.")
    if kind == "canvas":
        stats = image_stats(image)
        if stats["near_white"] > 0.985:
            raise RuntimeError(f"{subject}: live canvas capture is blank/white.")
        if stats["near_uniform"] or stats["variance"] < 18:
            raise RuntimeError(f"{subject}: live canvas capture is nearly uniform.")
        if stats["grayish"] > 0.94 and stats["variance"] < 140:
            raise RuntimeError(f"{subject}: live canvas capture looks like a gray placeholder.")


def screenshot_concrete(locator, kind: str, subject: str, label: str | None = None) -> Image.Image:
    image = raw_element_image(locator)
    if image is None:
        raise RuntimeError(f"{subject}: failed to screenshot {kind}.")
    validate_captured_subject(image, kind, subject, locator_text(locator))
    return add_image_label(image, label) if label else image


def selector_locator(page, output, selector: str):
    selector = selector.strip()
    if selector in {"page canvas:last", "page canvas"}:
        return page.locator("canvas").last if selector.endswith(":last") else page.locator("canvas").first
    if selector in {"output canvas:last", "output canvas"}:
        return output.locator("canvas").last if selector.endswith(":last") else output.locator("canvas").first
    if selector == "output widget controls":
        return widget_controls_locator(output)
    if selector.startswith("output "):
        selector = selector[len("output "):].strip()
    scoped = output.locator(selector) if output.count() > 0 else page.locator(selector)
    if scoped.count() > 0:
        return scoped.first
    return page.locator(selector).first


def widget_controls_locator(output):
    explicit = output.locator(".widget-box, .jupyter-widgets, .widget-subarea, .lm-Widget").first
    if explicit.count() > 0:
        return explicit
    controls = output.locator("input[type='range'], input[type='checkbox'], select, button")
    if controls.count() == 0:
        return controls
    controls.first.evaluate(
        """(node) => {
            const target = node.closest('.widget-box, .jupyter-widgets, .widget-subarea, form, div') || node;
            target.setAttribute('data-blog-media-widget-controls', 'true');
        }"""
    )
    return output.locator("[data-blog-media-widget-controls='true']").first


def merge_variant_step(step: dict, variant: dict) -> dict:
    merged = dict(step)
    merged.pop("capture_variants", None)
    if "controls" in variant:
        merged["controls"] = variant["controls"]
    if "slider_fraction" in step:
        merged["slider_fraction"] = step["slider_fraction"]
    for key in ("cell_index", "capture_selector", "capture_kind", "visual_subject"):
        if key in variant:
            merged[key] = variant[key]
    for key in ("camera", "live_prepare_cell", "live_render"):
        if key in variant:
            merged[key] = variant[key]
    return merged


def timeline_fraction(step: dict) -> float:
    for control in step.get("controls", []):
        if control.get("kind") == "slider" and control.get("role") == "timeline":
            return float(step.get("slider_fraction", control.get("fraction", 0.5)))
    return float(step.get("slider_fraction", 0.5))


def execute_live_render(context: dict | None, step: dict) -> None:
    render_template = step.get("live_render")
    if not render_template:
        return
    if context is None:
        raise RuntimeError(f"{step_label(step)}: live_render requires a live kernel context.")
    prepare_cell = step.get("live_prepare_cell")
    if prepare_cell is not None and context.get("prepared_cell") != int(prepare_cell):
        source_nb = context["source_nb"]
        source = source_nb.cells[int(prepare_cell)].source
        execute_kernel_code(context["connection_file"], source, int(context.get("kernel_timeout", 90)))
        context["prepared_cell"] = int(prepare_cell)
    fraction = timeline_fraction(step)
    frame_expr = f"int(round((frame_count - 1) * {fraction:.8f}))"
    camera = step.get("camera")
    camera_lines: list[str] = []
    if isinstance(camera, dict):
        if camera.get("target") == "animation_root":
            offset = camera.get("offset", [0.0, 0.0, 0.0])
            camera_lines.append(f"_blog_frame = {frame_expr}")
            camera_lines.append(
                "viewer.camera_pos = (animation.pos[_blog_frame, 0] + "
                f"np.array({offset}, dtype=np.float32)).tolist()"
            )
            frame_expr = "_blog_frame"
        elif isinstance(camera.get("pos"), list):
            camera_lines.append(f"viewer.camera_pos = {camera['pos']}")
        if "pitch" in camera:
            camera_lines.append(f"viewer.camera_pitch = {float(camera['pitch'])}")
        if "yaw" in camera:
            camera_lines.append(f"viewer.camera_yaw = {float(camera['yaw'])}")
    code = "\n".join(camera_lines + [render_template.format(frame=frame_expr, fraction=f"{fraction:.8f}")])
    execute_kernel_code(context["connection_file"], code, int(context.get("kernel_timeout", 90)))


def capture_live_canvas_image(page, step: dict, context: dict | None = None) -> Image.Image:
    if page is None:
        raise RuntimeError(f"{step_label(step)}: live capture requires a browser page.")
    execute_live_render(context, step)
    cell, output = cell_output_locator(page, int(step["cell_index"]))
    cell.scroll_into_view_if_needed(timeout=10_000)
    page.wait_for_timeout(500)
    if output.count() > 0 and not step.get("live_render"):
        set_controls(output, step)
    page.wait_for_timeout(1200)

    kind = capture_kind(step)
    subject = visual_subject(step)
    selector = step.get("capture_selector")
    if kind == "canvas":
        target = selector_locator(page, output, selector) if selector else output.locator("canvas").last
        if target.count() == 0:
            raise RuntimeError(f"{subject}: no concrete canvas found; live capture will not fall back to cell/output screenshots.")
        target.scroll_into_view_if_needed(timeout=10_000)
        page.wait_for_timeout(500)
        image = screenshot_concrete(target, "canvas", subject)
        return crop_canvas_render_area(image) if step.get("crop_canvas_render_area") else image
    if kind == "widget_controls":
        if output.count() == 0:
            raise RuntimeError(f"{subject}: no output area available for widget controls.")
        target = selector_locator(page, output, selector) if selector else widget_controls_locator(output)
        if target.count() == 0:
            raise RuntimeError(f"{subject}: no concrete widget controls found; live capture will not fall back to output screenshots.")
        target.scroll_into_view_if_needed(timeout=10_000)
        page.wait_for_timeout(300)
        return screenshot_concrete(target, "widget_controls", subject)
    raise RuntimeError(f"{subject}: live capture_kind={kind!r} is not supported.")


def capture_live_result(page, step: dict, context: dict | None = None) -> list[Image.Image]:
    variants = step.get("capture_variants")
    if isinstance(variants, list) and variants:
        captured: list[tuple[str, Image.Image]] = []
        for index, variant in enumerate(variants):
            variant_step = merge_variant_step(step, variant)
            label = variant.get("label") or f"Variant {index + 1}"
            captured.append((label, capture_live_canvas_image(page, variant_step, context)))
        return [compose_labeled_montage(captured)]
    return [capture_live_canvas_image(page, step, context)]


def png_size(path: Path) -> tuple[int, int] | None:
    header = path.read_bytes()[:24]
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    return struct.unpack(">II", header[16:24])


def validate_png(path: Path, min_width: int = 800, min_height: int = 450, min_bytes: int = 10_000) -> None:
    size = png_size(path)
    if size is None:
        raise RuntimeError(f"{path} is not a readable PNG")
    width, height = size
    if width < min_width or height < min_height:
        raise RuntimeError(f"{path} is too small for blog media: {width}x{height}")
    if path.stat().st_size < min_bytes:
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


def encode_mp4(frames: list[Path], output_path: Path, fps: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode MP4 previews.")
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
            "libx264",
            "-profile:v",
            "baseline",
            "-level",
            "3.1",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def encode_gif(frames: list[Path], output_path: Path, fps: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode GIF previews.")
    pattern = str(frames[0].parent / "frame_%04d.png")
    palette = output_path.with_suffix(".palette.png")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            pattern,
            "-vf",
            "fps=6,scale=960:-1:flags=lanczos,palettegen",
            str(palette),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            pattern,
            "-i",
            str(palette),
            "-lavfi",
            "fps=6,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    palette.unlink(missing_ok=True)


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


def ffprobe_video_codec(video_path: Path) -> str | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name",
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
    value = result.stdout.strip()
    return value or None


def validate_video(video_path: Path, max_seconds: int, max_bytes: int) -> None:
    size = video_path.stat().st_size
    if size <= 0:
        raise RuntimeError(f"{video_path} is empty.")
    if size > max_bytes:
        raise RuntimeError(f"{video_path} is too large: {size} bytes.")
    duration = ffprobe_duration(video_path)
    if duration is not None and duration > max_seconds + 0.75:
        raise RuntimeError(f"{video_path} is too long: {duration:.2f}s.")


def validate_codec(video_path: Path, expected: str) -> None:
    codec = ffprobe_video_codec(video_path)
    if codec is not None and codec != expected:
        raise RuntimeError(f"{video_path} codec is {codec}, expected {expected}.")


def validate_gif(path: Path, max_bytes: int) -> None:
    if path.stat().st_size <= 0:
        raise RuntimeError(f"{path} is empty.")
    if path.stat().st_size > max_bytes:
        raise RuntimeError(f"{path} is too large: {path.stat().st_size} bytes.")


def make_video_from_cards(case: dict, video_conf: dict, assets_dir: Path) -> None:
    frames_dir = Path(tempfile.mkdtemp(prefix=f"blog_media_{case['slug']}_frames_"))
    target_count = max(12, min(48, int(video_conf["max_seconds"]) * int(video_conf.get("fps", 4))))
    steps = case["steps"]
    frames: list[Path] = []
    for index in range(target_count):
        step = steps[int(index * len(steps) / target_count)]
        source = assets_dir / card_file(step)
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


def write_frames(images: list[Image.Image], prefix: str) -> list[Path]:
    frames_dir = Path(tempfile.mkdtemp(prefix=prefix))
    frames: list[Path] = []
    for index, image in enumerate(images):
        frame_path = frames_dir / f"frame_{index:04d}.png"
        fit_video_frame(image).save(frame_path)
        frames.append(frame_path)
    return frames


def frame_difference(left: Image.Image, right: Image.Image) -> float:
    a = ImageOps.contain(left.convert("RGB"), (160, 90), Image.Resampling.BILINEAR)
    b = ImageOps.contain(right.convert("RGB"), (160, 90), Image.Resampling.BILINEAR)
    if a.size != b.size:
        b = b.resize(a.size, Image.Resampling.BILINEAR)
    left_pixels = list(a.getdata())
    right_pixels = list(b.getdata())
    total = 0
    for first, second in zip(left_pixels, right_pixels):
        total += sum(abs(first[index] - second[index]) for index in range(3))
    return total / max(1, len(left_pixels) * 3)


def validate_real_motion_frames(step: dict, frames: list[Image.Image], provenance: str) -> None:
    if provenance == DERIVED_CARD_PROVENANCE:
        if is_key_publish_media(step):
            raise RuntimeError(f"{step_label(step)}: derived card crops cannot satisfy publish-required key media.")
        return
    if provenance not in REAL_MEDIA_PROVENANCE:
        raise RuntimeError(f"{step_label(step)}: motion media provenance {provenance!r} is not an approved real source.")
    if len(frames) < 3:
        raise RuntimeError(f"{step_label(step)}: motion media requires a real frame sequence, got {len(frames)} frame(s).")
    max_delta = max(frame_difference(frames[index - 1], frames[index]) for index in range(1, len(frames)))
    if max_delta < 1.5:
        raise RuntimeError(f"{step_label(step)}: motion frame sequence appears static.")


def animated_frames_from_still(image: Image.Image, frame_count: int = 18) -> list[Image.Image]:
    source = fit_video_frame(image)
    frames: list[Image.Image] = []
    for index in range(frame_count):
        # A tiny crop drift makes legacy still captures visibly playable in README
        # previews until a live timeline recapture is available.
        phase = index / max(1, frame_count - 1)
        zoom = 1.0 + 0.025 * phase
        crop_w = int(source.width / zoom)
        crop_h = int(source.height / zoom)
        x = int((source.width - crop_w) * phase)
        y = int((source.height - crop_h) * 0.5)
        frame = source.crop((x, y, x + crop_w, y + crop_h)).resize((1280, 720), Image.Resampling.LANCZOS)
        frames.append(frame)
    return frames


def encode_step_motion(
    step: dict,
    frames: list[Image.Image],
    assets_dir: Path,
    animation_conf: dict,
    provenance: str = "live_canvas",
) -> None:
    if not step_needs_motion_media(step):
        return
    validate_real_motion_frames(step, frames, provenance)
    fps = int(animation_conf.get("fps", 6))
    max_seconds = int(animation_conf.get("max_seconds", 6))
    max_bytes = int(animation_conf.get("max_bytes", 10 * 1024 * 1024))
    frame_paths = write_frames(frames, f"blog_media_{step.get('id', 'step')}_motion_")
    if step.get("preview_gif"):
        gif_path = assets_dir / step["preview_gif"]
        encode_gif(frame_paths, gif_path, fps)
        validate_gif(gif_path, max_bytes)
    if step.get("video_mp4"):
        mp4_path = assets_dir / step["video_mp4"]
        encode_mp4(frame_paths, mp4_path, fps)
        validate_video(mp4_path, max_seconds, max_bytes)
        validate_codec(mp4_path, "h264")
    if step.get("video_webm"):
        webm_path = assets_dir / step["video_webm"]
        encode_webm(frame_paths, webm_path, fps)
        validate_video(webm_path, max_seconds, max_bytes)
        validate_codec(webm_path, "vp9")


def choose_live_video_step(case: dict) -> dict | None:
    for output_type in ("timeline_viewer", "viewer", "animation_viewer", "widget_controls"):
        for step in case["steps"]:
            if step.get("output_type") == output_type:
                return step
    return None


def make_video_from_live(page, case: dict, source_nb, video_conf: dict, assets_dir: Path, card_conf: dict, context: dict | None = None) -> None:
    base_step = choose_live_video_step(case)
    if base_step is None:
        raise RuntimeError(f"{case['slug']}: live_timeline video requires a concrete live video step.")

    frames_dir = Path(tempfile.mkdtemp(prefix=f"blog_media_{case['slug']}_live_frames_"))
    target_count = max(12, min(48, int(video_conf["max_seconds"]) * int(video_conf.get("fps", 4))))
    sample_count = min(12, target_count)
    sample_frames: list[Image.Image] = []

    for sample_index in range(sample_count):
        fraction = sample_index / max(1, sample_count - 1)
        step = dict(base_step)
        step["slider_fraction"] = fraction
        step["title"] = f"{base_step['title']} - timeline sample {sample_index + 1}"
        result_images = capture_live_result(page, step, context)
        if not result_images:
            raise RuntimeError(f"{case['slug']}: live video sample {sample_index + 1} produced no concrete media.")
        sample_frames.append(fit_video_frame(result_images[0]))

    validate_real_motion_frames(base_step, sample_frames, concrete_provenance(base_step, "live_canvas"))

    frames: list[Path] = []
    for index in range(target_count):
        frame = sample_frames[int(index * len(sample_frames) / target_count)]
        frame_path = frames_dir / f"frame_{index:04d}.png"
        frame.save(frame_path)
        frames.append(frame_path)

    output_path = assets_dir / video_conf["file"]
    encode_webm(frames, output_path, int(video_conf.get("fps", 4)))
    validate_video(output_path, int(video_conf["max_seconds"]), int(video_conf["max_bytes"]))


def capture_live_motion_frames(page, step: dict, animation_conf: dict, context: dict | None = None) -> list[Image.Image]:
    frame_count = max(3, min(24, int(animation_conf.get("max_seconds", 6)) * int(animation_conf.get("fps", 6))))
    sample_count = min(12, frame_count)
    frames: list[Image.Image] = []
    for index in range(sample_count):
        sample = dict(step)
        sample["slider_fraction"] = index / max(1, sample_count - 1)
        images = capture_live_result(page, sample, context)
        if not images:
            raise RuntimeError(f"{step_label(step)}: live motion sample {index + 1} produced no concrete media.")
        frames.append(images[0])
    return frames


def executed_result_images(executed_nb, step: dict, width: int) -> tuple[list[Image.Image], str]:
    kind = capture_kind(step)
    if kind == "plot":
        image = image_from_executed_output(executed_nb, step)
        if image is None:
            raise RuntimeError(f"{step_label(step)}: capture_kind=plot requires an executed image/png output.")
        return [add_image_label(image, f"{visual_subject(step)} / executed plot image")], "executed_plot_image"
    if kind == "table":
        return [text_image_from_executed_output(executed_nb, step, width)], "executed_table_card"
    if kind == "formula":
        return [text_image_from_executed_output(executed_nb, step, width)], "executed_formula_card"
    if kind == "artifact_summary":
        return [text_image_from_executed_output(executed_nb, step, width)], "artifact_summary"
    if kind == "code_evidence":
        return [text_image_from_executed_output(executed_nb, step, width)], "code_evidence"
    raise RuntimeError(f"{step_label(step)}: capture_kind={kind!r} requires live capture.")


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
        provenance = concrete_provenance(step, "artifact_summary" if capture_kind(step) == "artifact_summary" else "code_evidence")
        if provenance not in {"artifact_summary", "code_evidence"}:
            raise RuntimeError(f"{step_label(step)}: module media provenance {provenance!r} is not valid for concrete evidence.")
        save_result_media(images, assets_dir / result_file(step), int(manifest["card"]["width"]))
        compose_learning_card(step, source, images, assets_dir / card_file(step), manifest["card"])

    make_video_from_cards(case, manifest["video"], assets_dir)
    print(f"captured {slug}: {len(case['steps'])} module cards + {manifest['video']['file']}")


def row_nonwhite_fraction(image: Image.Image, y: int) -> float:
    pixels = image.load()
    nonwhite = 0
    for x in range(image.width):
        r, g, b = pixels[x, y]
        if r < 252 or g < 252 or b < 252:
            nonwhite += 1
    return nonwhite / max(1, image.width)


def contiguous_segments(rows: list[int], max_gap: int = 3) -> list[tuple[int, int]]:
    if not rows:
        return []
    segments: list[tuple[int, int]] = []
    start = prev = rows[0]
    for row in rows[1:]:
        if row - prev <= max_gap:
            prev = row
            continue
        segments.append((start, prev))
        start = prev = row
    segments.append((start, prev))
    return segments


def explanation_top(image: Image.Image) -> int | None:
    pixels = image.load()
    start_y = int(image.height * 0.45)
    for y in range(start_y, image.height):
        warm = 0
        for x in range(20, image.width - 20):
            r, g, b = pixels[x, y]
            if r > 245 and g > 235 and 185 < b < 245 and r - b >= 18:
                warm += 1
        if warm > image.width * 0.55:
            return max(0, y - 8)
    return None


def result_region_from_card(card: Image.Image) -> Image.Image:
    """Best-effort crop from a legacy learning card to just controls/output."""
    image = card.convert("RGB")
    rows = [y for y in range(image.height) if row_nonwhite_fraction(image, y) > 0.18]
    segments = contiguous_segments(rows)
    code_like = [
        segment
        for segment in segments
        if segment[0] > 55 and segment[0] < 180 and segment[1] - segment[0] > 80
    ]
    code_end = max((segment[1] for segment in code_like), default=int(image.height * 0.25))
    later = [segment for segment in segments if segment[0] > code_end + 8]
    top = later[0][0] if later else min(image.height - 1, code_end + 16)
    bottom = explanation_top(image) or image.height - 24
    if bottom <= top + 180:
        bottom = image.height - 24
    crop = image.crop((0, max(0, top - 4), image.width, min(image.height, bottom)))
    return crop


def derive_case_from_cards(case: dict, manifest: dict) -> None:
    root = repo_root()
    assets_dir = root / case["assets_dir"]
    animation_conf = manifest.get("animation", manifest.get("video", {}))
    for step in case["steps"]:
        if is_key_publish_media(step):
            raise RuntimeError(f"{case['slug']} {step_label(step)}: derive-from-cards is fallback/provenance={DERIVED_CARD_PROVENANCE} and cannot satisfy publish-required key media.")
        card_path = assets_dir / card_file(step)
        if not card_path.exists():
            raise FileNotFoundError(f"{case['slug']}: missing legacy card for derive mode: {card_path}")
        with Image.open(card_path) as image:
            source = image.convert("RGB")
            result = result_region_from_card(source)
            result_path = assets_dir / result_file(step)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result.save(result_path)
            validate_png(result_path, min_width=320, min_height=180, min_bytes=4000)
            if step_needs_motion_media(step):
                encode_step_motion(step, animated_frames_from_still(result), assets_dir, animation_conf, DERIVED_CARD_PROVENANCE)
    make_video_from_cards(case, manifest["video"], assets_dir)
    print(f"derived {case['slug']}: result media from legacy cards")


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
    needs_live = any(capture_kind(step) in {"canvas", "widget_controls"} for step in case["steps"])

    page = None
    live_context = None
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
        live_context = {
            "connection_file": kernel_connection_file(server, case["notebook"]),
            "source_nb": source_nb,
            "prepared_cell": None,
            "kernel_timeout": 120,
        }

    for step in case["steps"]:
        cell_index = int(step["cell_index"])
        source = source_nb.cells[cell_index].source
        kind = capture_kind(step)
        width = int(manifest["card"]["width"])
        if kind in {"canvas", "widget_controls"}:
            result_images = capture_live_result(page, step, live_context)
            provenance = concrete_provenance(step, "live_canvas" if kind == "canvas" else "live_widget_controls")
        else:
            result_images, provenance = executed_result_images(executed_nb, step, width)
        if provenance not in REAL_MEDIA_PROVENANCE:
            raise RuntimeError(f"{step_label(step)}: result media provenance {provenance!r} is not an approved real source.")

        save_result_media(result_images, assets_dir / result_file(step), width)
        compose_learning_card(step, source, result_images, assets_dir / card_file(step), manifest["card"])
        if step_needs_motion_media(step):
            if kind != "canvas":
                raise RuntimeError(f"{step_label(step)}: motion media requires capture_kind=canvas and a real frame sequence.")
            motion_frames = capture_live_motion_frames(page, step, manifest.get("animation", manifest["video"]), live_context)
            encode_step_motion(step, motion_frames, assets_dir, manifest.get("animation", manifest["video"]), provenance)

    if page is not None and case.get("video_step", {}).get("mode") == "live_timeline":
        make_video_from_live(page, case, source_nb, manifest["video"], assets_dir, manifest["card"], live_context)
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
    parser.add_argument("--derive-from-cards", action="store_true", help="Build v5 result/GIF/video media from existing card PNGs.")
    args = parser.parse_args()

    root = repo_root()
    manifest = load_manifest(root / args.manifest)
    if int(manifest.get("version", 1)) < 3:
        raise SystemExit("media manifest must be version 3 or newer")
    slugs = [] if args.all else args.slug
    if not args.all and not slugs:
        parser.error("pass --all or one or more --slug values")

    cases = selected_cases(manifest, slugs)
    if args.derive_from_cards:
        for case in cases:
            derive_case_from_cards(case, manifest)
        return 0

    needs_live = any(any(capture_kind(step) in {"canvas", "widget_controls"} for step in case["steps"]) for case in cases if case.get("kind") != "python_module")
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
