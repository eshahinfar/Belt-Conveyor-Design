(function () {
  "use strict";

  function roundTo(value, decimals) {
    const factor = Math.pow(10, decimals);
    return Math.round((Number(value) + Number.EPSILON) * factor) / factor;
  }

  function parseSegments(value) {
    if (!value) {
      return null;
    }
    try {
      const parsed = JSON.parse(value);
      if (!Array.isArray(parsed)) {
        return null;
      }
      return parsed
        .map((segment) => ({
          length_mm: Number(segment.length_mm),
          diameter_mm: Number(segment.diameter_mm),
        }))
        .filter(
          (segment) =>
            Number.isFinite(segment.length_mm) &&
            Number.isFinite(segment.diameter_mm) &&
            segment.length_mm > 0 &&
            segment.diameter_mm > 0
        );
    } catch (error) {
      console.warn("Unable to parse shaft geometry JSON", error);
      return null;
    }
  }

  function getDefaultSegments() {
    return [
      { length_mm: 150, diameter_mm: 60 },
      { length_mm: 120, diameter_mm: 45 },
      { length_mm: 150, diameter_mm: 60 },
    ];
  }

  function createRow(segment, index, state) {
    const row = document.createElement("tr");
    row.dataset.index = String(index);
    row.innerHTML = `
      <th scope="row">${index + 1}</th>
      <td>
        <input
          type="number"
          min="1"
          step="1"
          value="${roundTo(segment.length_mm, 1)}"
          aria-label="Length of segment ${index + 1} in millimetres"
          data-field="length_mm"
        />
      </td>
      <td>
        <input
          type="number"
          min="1"
          step="0.5"
          value="${roundTo(segment.diameter_mm, 1)}"
          aria-label="Diameter of segment ${index + 1} in millimetres"
          data-field="diameter_mm"
        />
      </td>
      <td class="actions">
        <button type="button" class="link" data-remove>
          Remove
        </button>
      </td>
    `;

    row.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        const field = input.dataset.field;
        const numeric = Number(input.value);
        if (!Number.isFinite(numeric) || numeric <= 0) {
          return;
        }
        state.segments[index][field] = numeric;
        state.update();
      });
    });

    row.querySelector("[data-remove]").addEventListener("click", () => {
      if (state.segments.length <= 1) {
        return;
      }
      state.segments.splice(index, 1);
      state.update();
    });

    return row;
  }

  function renderPreview(svg, segments) {
    const totalLength = segments.reduce((sum, segment) => sum + segment.length_mm, 0);
    const maxDiameter = segments.reduce(
      (max, segment) => Math.max(max, segment.diameter_mm),
      0
    );

    const width = 620;
    const height = 200;
    const marginX = 30;
    const marginY = 20;
    const usableWidth = width - marginX * 2;
    const usableHeight = height - marginY * 2;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";

    const centerY = height / 2;
    const scaleX = totalLength > 0 ? usableWidth / totalLength : 1;
    const scaleY = maxDiameter > 0 ? usableHeight / maxDiameter : 1;

    const background = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    background.setAttribute("x", "0");
    background.setAttribute("y", "0");
    background.setAttribute("width", String(width));
    background.setAttribute("height", String(height));
    background.setAttribute("fill", "var(--shaft-preview-bg, rgba(15,23,42,0.65))");
    svg.appendChild(background);

    let cursorX = marginX;
    segments.forEach((segment) => {
      const segWidth = segment.length_mm * scaleX;
      const segHalfHeight = (segment.diameter_mm * scaleY) / 2;
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", String(cursorX));
      rect.setAttribute("y", String(centerY - segHalfHeight));
      rect.setAttribute("width", String(segWidth));
      rect.setAttribute("height", String(segHalfHeight * 2));
      rect.setAttribute("rx", "8");
      rect.setAttribute("fill", "rgba(56, 189, 248, 0.65)");
      rect.setAttribute("stroke", "rgba(148, 163, 184, 0.9)");
      rect.setAttribute("stroke-width", "1.5");
      svg.appendChild(rect);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", String(cursorX + segWidth / 2));
      label.setAttribute("y", String(centerY - segHalfHeight - 8));
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("fill", "#e2e8f0");
      label.setAttribute("font-size", "12");
      label.textContent = `${roundTo(segment.diameter_mm, 1)} mm`;
      svg.appendChild(label);

      cursorX += segWidth;
    });

    const centerLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
    centerLine.setAttribute("x1", String(marginX));
    centerLine.setAttribute("x2", String(width - marginX));
    centerLine.setAttribute("y1", String(centerY));
    centerLine.setAttribute("y2", String(centerY));
    centerLine.setAttribute("stroke", "rgba(226, 232, 240, 0.45)");
    centerLine.setAttribute("stroke-dasharray", "6 6");
    svg.appendChild(centerLine);
  }

  function updateSummary(editor, segments) {
    const minimum = segments.reduce(
      (current, segment) => Math.min(current, segment.diameter_mm),
      segments[0].diameter_mm
    );
    const total = segments.reduce((sum, segment) => sum + segment.length_mm, 0);
    editor.querySelector("[data-geometry-summary]").textContent =
      `Minimum diameter: ${roundTo(minimum, 1)} mm • Total length: ${roundTo(total, 1)} mm`;
  }

  function initialiseEditor(editor) {
    const fieldId = editor.getAttribute("data-field-id");
    const hiddenInput = fieldId ? document.getElementById(fieldId) : null;
    if (!hiddenInput) {
      return;
    }

    const parsed = parseSegments(hiddenInput.value);
    const segments = parsed && parsed.length ? parsed : getDefaultSegments();

    const summary = document.createElement("p");
    summary.className = "shaft-geometry-summary";
    summary.setAttribute("data-geometry-summary", "");
    const note = editor.querySelector(".shaft-geometry-note");
    editor.insertBefore(summary, note || null);

    const tableBody = editor.querySelector("[data-geometry-rows]");
    const addButton = editor.querySelector("[data-add-segment]");
    const preview = editor.querySelector("[data-geometry-preview]");

    const state = {
      segments: segments.slice(),
      update() {
        while (tableBody.firstChild) {
          tableBody.removeChild(tableBody.firstChild);
        }
        this.segments.forEach((segment, index) => {
          tableBody.appendChild(createRow(segment, index, state));
        });
        hiddenInput.value = JSON.stringify(this.segments);
        renderPreview(preview, this.segments);
        updateSummary(editor, this.segments);
      },
    };

    addButton.addEventListener("click", () => {
      const last = state.segments[state.segments.length - 1];
      state.segments.push({
        length_mm: last ? last.length_mm : 100,
        diameter_mm: last ? last.diameter_mm : 40,
      });
      state.update();
    });

    state.update();
  }

  document.addEventListener("DOMContentLoaded", () => {
    const editors = document.querySelectorAll("[data-geometry-editor]");
    editors.forEach((editor) => {
      initialiseEditor(editor);
    });
  });
})();
