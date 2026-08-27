"""OMR extraction service — thin wrapper around the omrExtractor submodule.

Loads the calibration template once at module level and exposes a clean
interface for the processing router. All extractor exceptions are caught
and re-raised as OMRProcessingError so callers never need to know about
OpenCV or the submodule's internal structure.
"""

import sys
from pathlib import Path
from typing import Any

# ── Add omrExtractor/src to Python path ────────────────────────────
_OMR_SRC = Path(__file__).resolve().parent.parent.parent.parent / "omrExtractor" / "src"
if str(_OMR_SRC) not in sys.path:
    sys.path.insert(0, str(_OMR_SRC))

from align import align, find_markers  # noqa: E402
from bubble_reader import read_omr, load_template  # noqa: E402
from preprocess import load_image_from_path  # noqa: E402

_TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "omrExtractor"
    / "templates"
    / "calibration_points.json"
)

# Load once at import time — the template is static per calibration session.
_template: dict[str, Any] | None = None


def _get_template() -> dict[str, Any]:
    global _template
    if _template is None:
        _template = load_template(_TEMPLATE_PATH)
    return _template


class OMRProcessingError(Exception):
    """Raised when the OMR extractor fails for any reason."""


def get_template_question_count() -> int:
    """Return the number of questions the current template supports."""
    tpl = _get_template()
    return tpl["question_count"]


def extract_omr(image_path: Path, question_count: int) -> dict[str, str | None]:
    """Run the OMR extractor on a single image.

    Args:
        image_path: Absolute path to the scanned OMR sheet image/PDF.
        question_count: Number of questions to read (from the Assessment).

    Returns:
        dict mapping "Q{n}" → "A"/"B"/"C"/"D"/None.

    Raises:
        OMRProcessingError: If extraction fails for any reason.
    """
    tpl = _get_template()

    # Guard: assessment has more questions than the template supports.
    template_qc = tpl["question_count"]
    if question_count > template_qc:
        raise OMRProcessingError(
            f"Assessment has {question_count} questions but the OMR template "
            f"only supports {template_qc}. Recalibrate the template first."
        )

    if not image_path.exists():
        raise OMRProcessingError(f"OMR image file not found: {image_path.name}")

    # Guard: multi-page PDFs are not valid OMR inputs. One file = one sheet;
    # silently reading only page 1 would drop the other pages' data.
    if image_path.suffix.lower() == ".pdf":
        try:
            import fitz

            with fitz.open(image_path) as doc:
                page_count = doc.page_count
            if page_count > 1:
                raise OMRProcessingError(
                    f"{image_path.name}: multi-page PDF ({page_count} pages) is not "
                    f"supported. Upload each OMR sheet as a separate single-page "
                    f"image or PDF file."
                )
        except OMRProcessingError:
            raise
        except Exception as e:
            raise OMRProcessingError(
                f"Could not read PDF {image_path.name}: {type(e).__name__}: {e}"
            ) from e

    # Guard: verify page alignment BEFORE running bubble detection. The
    # extractor's read_omr() only warns on alignment failure and proceeds with
    # an unaligned image, which produces garbage scores. We run the same
    # marker check the extractor uses and fail the sheet instead.
    try:
        image = load_image_from_path(str(image_path))
    except Exception as e:
        raise OMRProcessingError(
            f"Could not load image {image_path.name}: {type(e).__name__}: {e}"
        ) from e

    try:
        markers = find_markers(image)
    except Exception as e:
        raise OMRProcessingError(
            f"OMR alignment check failed for {image_path.name}: "
            f"{type(e).__name__}: {e}"
        ) from e

    missing = [c for c in ("top_left", "top_right", "bottom_left", "bottom_right") if c not in markers]
    if missing:
        raise OMRProcessingError(
            f"OMR alignment failed for {image_path.name}: could not find corner "
            f"markers {missing}. The scan may be cropped, skewed, or not an OMR "
            f"sheet for the current template."
        )

    try:
        result = read_omr(image_path, tpl, question_count=question_count)
    except ValueError as e:
        # Alignment failures (missing corner markers, etc.)
        raise OMRProcessingError(f"OMR alignment failed: {e}") from e
    except KeyError as e:
        # Missing question key in template
        raise OMRProcessingError(f"OMR template missing expected key: {e}") from e
    except Exception as e:
        # Catch-all for OpenCV errors, corrupt images, etc.
        raise OMRProcessingError(f"OMR extraction failed: {type(e).__name__}: {e}") from e

    # Validate the result shape
    if not isinstance(result, dict):
        raise OMRProcessingError(
            f"Unexpected extractor output type: {type(result).__name__} (expected dict)"
        )

    return result
