# API Contract (v0.1) — 2025X-City_Hackathon_Learnicer

## 1. Purpose

This document defines the backend API contract for the Hackathon project **2025X-City_Hackathon_Learnicer**.
The contract specifies request/response formats so that:

* Backend (A) can implement stable outputs.
* Frontend (B) can render solution steps and show OCR text for debugging.
* Visualization (C) can drive Canvas animations using `animation_instructions`.

**Contract version:** `v0.1`
**Stability rule:** Once `v0.1` is merged into `main`, do not rename existing fields. Add new optional fields only.

---

## 2. Endpoint Overview

### 2.1 Health Check

* **Method:** `GET`
* **Path:** `/health`
* **Response:** `{ "status": "ok" }`

### 2.2 Upload & Solve (MVP)

* **Method:** `POST`
* **Path:** `/upload`
* **Content-Type:** `multipart/form-data`
* **Form Field:** `file` (image file)

---

## 3. Request Specification

### 3.1 `/upload` Request

**Form fields**

* `file` (required): image file (`.png`, `.jpg`, `.jpeg`)

**Example (curl)**

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -F "file=@/path/to/problem.jpg"
```

---

## 4. Response Specification

### 4.1 Success Response (HTTP 200)

**Top-level JSON object fields**

| Field                    | Type     | Required | Description                                                          |
| ------------------------ | -------- | -------- | -------------------------------------------------------------------- |
| `problem_type`           | string   | Yes      | Problem category label for routing/visualization.                    |
| `ocr_text`               | string   | Yes      | Raw OCR extracted text for debugging and optional UI display.        |
| `solution_steps`         | string[] | Yes      | Ordered list of solution steps. Frontend renders as an ordered list. |
| `animation_instructions` | object   | Yes      | Animation instruction object consumed by Canvas engine.              |

#### 4.1.1 `problem_type` (string)

Recommended values for MVP:

* `physics_projectile` (projectile motion demo)
* `unknown` (fallback)

#### 4.1.2 `solution_steps` (string[])

* Must be in correct logical order.
* Each element is a human-readable step line.

#### 4.1.3 `animation_instructions` (object)

MVP requires at least one animation type: **projectile**.

**Common fields**

| Field   | Type   | Required | Description                                                             |
| ------- | ------ | -------- | ----------------------------------------------------------------------- |
| `type`  | string | Yes      | Animation type discriminator. MVP: `"projectile"`.                      |
| `scale` | number | No       | Pixels-per-unit mapping for Canvas. Default handled by frontend/engine. |

**Projectile fields** (`type = "projectile"`)

| Field           | Type   | Required | Description                                                                       |
| --------------- | ------ | -------- | --------------------------------------------------------------------------------- |
| `initial_speed` | number | Yes      | Initial speed magnitude (units: m/s).                                             |
| `angle`         | number | Yes      | Launch angle in degrees (0–90).                                                   |
| `gravity`       | number | Yes      | Gravity acceleration magnitude (units: m/s^2), default 9.8 if omitted by backend. |
| `duration`      | number | No       | Total animation time in seconds. If omitted, Canvas engine may estimate.          |
| `initial_x`     | number | No       | Initial position x (units: m). Default 0.                                         |
| `initial_y`     | number | No       | Initial position y (units: m). Default 0.                                         |

**Success example**

```json
{
  "problem_type": "physics_projectile",
  "ocr_text": "A ball is thrown with initial speed 20 m/s at 45 degrees...",
  "solution_steps": [
    "Step 1: Extract known parameters from the problem statement.",
    "Step 2: Decompose initial velocity into horizontal and vertical components.",
    "Step 3: Use kinematics equations to compute the trajectory and flight time."
  ],
  "animation_instructions": {
    "type": "projectile",
    "initial_speed": 20,
    "angle": 45,
    "gravity": 9.8,
    "duration": 3.0,
    "scale": 20,
    "initial_x": 0,
    "initial_y": 0
  }
}
```

---

### 4.2 Error Response (HTTP 4xx / 5xx)

To simplify frontend error handling, errors use a consistent JSON structure:

| Field     | Type   | Required | Description                                            |
| --------- | ------ | -------- | ------------------------------------------------------ |
| `error`   | string | Yes      | Short error category.                                  |
| `details` | string | No       | Optional debugging details (may be hidden in demo UI). |

**Recommended error categories**

* `missing_file` — form-data lacks `file`
* `empty_filename` — filename is empty
* `unsupported_file_type` — file extension not allowed
* `save_failed` — server failed to save file
* `ocr_failed` — OCR raised exception or failed critically
* `llm_failed` — LLM call failed (future)
* `internal_error` — fallback for uncaught errors

**Error example (HTTP 400)**

```json
{
  "error": "missing_file",
  "details": "missing file field 'file'"
}
```

**Error example (HTTP 500)**

```json
{
  "error": "ocr_failed",
  "details": "PaddleOCR initialization failed: ..."
}
```

---

## 5. Frontend/Visualization Consumption Rules

### 5.1 Frontend (B)

* Render `solution_steps` as an ordered list.
* Optionally show `ocr_text` in a collapsible/debug section.
* Pass `animation_instructions` directly to Canvas engine:

  * `engine.loadInstructions(animation_instructions)`
  * Then enable `play/pause/reset` controls.

### 5.2 Visualization (C)

* Use `animation_instructions.type` to route to the correct animation implementation.
* MVP only needs to support `type = "projectile"`.
* If optional fields are missing, apply safe defaults:

  * `gravity`: 9.8
  * `scale`: 20
  * `initial_x/initial_y`: 0
  * `duration`: estimate based on physics or set a fixed demo duration.

---

## 6. Backward Compatibility

* Do not rename existing fields in `v0.1`.
* Additions are allowed only as **optional** fields.
* If a breaking change is needed, bump contract version to `v0.2` and coordinate with B/C.

---

## 7. Notes

* LLM integration is placeholder in MVP. Backend can return mock `problem_type`, `solution_steps`, and `animation_instructions` until Claude API is connected.
* OCR text is included primarily for debugging and may be optional to display in demo UI.
* Units used in animation instructions follow common physics conventions (m, s), but visualization may scale them for display.

