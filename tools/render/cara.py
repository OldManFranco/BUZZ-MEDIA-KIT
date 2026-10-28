"""Medición de la cara de Andrew con MediaPipe: ojos, iris, barbilla, frente, giro de cabeza, parpadeo y tope de la cabeza.

Se usa para la regla 3/4 (encuadre), el QA de textos contra la cara y el Eye Contact.
Índices de la malla de MediaPipe (478 puntos):
  iris derecho 468 (centro) · iris izquierdo 473 (centro)
  ojo derecho: esquinas 33 (exterior) y 133 (interior), párpados 159 (arriba) y 145 (abajo)
  ojo izquierdo: esquinas 263 (exterior) y 362 (interior), párpados 386 (arriba) y 374 (abajo)
  frente 10 · barbilla 152 · punta de la nariz 1
"""
import math
import os

import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

MODELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

EYE_R = {"out": 33, "in": 133, "up": 159, "down": 145, "iris": 468}
EYE_L = {"out": 263, "in": 362, "up": 386, "down": 374, "iris": 473}
# contorno del ojo (para la máscara de corrección de Eye Contact)
EYE_R_RING = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
EYE_L_RING = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466]
# óvalo de la cara (para el QA de textos)
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148,
             176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]


class Medidor:
    def __init__(self, segmentar=True):
        opts = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=os.path.join(MODELS, "face_landmarker.task")),
            running_mode=vision.RunningMode.VIDEO, num_faces=1,
            output_facial_transformation_matrixes=True, output_face_blendshapes=True)
        self.lm = vision.FaceLandmarker.create_from_options(opts)
        self.seg = None
        if segmentar:
            sopts = vision.ImageSegmenterOptions(
                base_options=BaseOptions(model_asset_path=os.path.join(MODELS, "selfie_segmenter.tflite")),
                running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True)
            self.seg = vision.ImageSegmenter.create_from_options(sopts)

    def medir(self, rgb, t_ms):
        """rgb: imagen HxWx3 uint8. Devuelve dict con medidas en píxeles, o None si no hay cara."""
        h, w = rgb.shape[:2]
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        r = self.lm.detect_for_video(img, int(t_ms))
        if not r.face_landmarks:
            return None
        pts = np.array([[p.x * w, p.y * h] for p in r.face_landmarks[0]], dtype=np.float32)
        out = {"pts": pts}
        out["ojo_r"], out["ojo_l"] = pts[EYE_R["iris"]], pts[EYE_L["iris"]]
        out["ojos_y"] = float((pts[EYE_R["iris"]][1] + pts[EYE_L["iris"]][1]) / 2)
        out["ojos_x"] = float((pts[EYE_R["iris"]][0] + pts[EYE_L["iris"]][0]) / 2)
        out["frente_y"] = float(pts[10][1])
        out["barbilla_y"] = float(pts[152][1])
        out["alto_cara"] = out["barbilla_y"] - out["frente_y"]
        oval = pts[FACE_OVAL]
        out["cara_x0"], out["cara_x1"] = float(oval[:, 0].min()), float(oval[:, 0].max())
        out["centro_x"] = float((out["cara_x0"] + out["cara_x1"]) / 2)
        # giro de cabeza (grados) desde la matriz de transformación
        if r.facial_transformation_matrixes:
            m = np.array(r.facial_transformation_matrixes[0])[:3, :3]
            out["yaw"] = float(math.degrees(math.atan2(-m[2, 0], math.hypot(m[2, 1], m[2, 2]))))
            out["pitch"] = float(math.degrees(math.atan2(m[2, 1], m[2, 2])))
        # parpadeo y mirada desde los blendshapes
        if r.face_blendshapes:
            bs = {b.category_name: b.score for b in r.face_blendshapes[0]}
            out["bs"] = bs                                   # todos los blendshapes (expresión, para miniaturas)
            out["parpadeo"] = float((bs.get("eyeBlinkLeft", 0) + bs.get("eyeBlinkRight", 0)) / 2)
            out["mira_abajo"] = float((bs.get("eyeLookDownLeft", 0) + bs.get("eyeLookDownRight", 0)) / 2)
            out["mira_arriba"] = float((bs.get("eyeLookUpLeft", 0) + bs.get("eyeLookUpRight", 0)) / 2)
            out["mira_lado"] = float((bs.get("eyeLookOutLeft", 0) + bs.get("eyeLookInRight", 0)
                                      - bs.get("eyeLookInLeft", 0) - bs.get("eyeLookOutRight", 0)) / 2)
        # iris relativo al ojo (0 = esquina exterior, 1 = interior; 0 = párpado de arriba, 1 = abajo)
        for k, E in (("r", EYE_R), ("l", EYE_L)):
            a, b = pts[E["out"]], pts[E["in"]]
            u, d = pts[E["up"]], pts[E["down"]]
            iris = pts[E["iris"]]
            ax = b - a
            t = float(np.dot(iris - a, ax) / max(np.dot(ax, ax), 1e-6))
            ab = float(abs(d[1] - u[1]))
            out[f"iris_h_{k}"] = t
            out[f"iris_v_{k}"] = float((iris[1] - u[1]) / max(ab, 1e-6))
            out[f"apertura_{k}"] = ab / max(float(np.linalg.norm(ax)), 1e-6)
        # tope de la cabeza con la máscara de persona (el pelo no está en la malla)
        if self.seg is not None:
            sr = self.seg.segment_for_video(img, int(t_ms))
            mask = sr.confidence_masks[0].numpy_view()
            if mask.ndim == 3:
                mask = mask[..., 0]
            x0, x1 = int(max(0, out["cara_x0"])), int(min(w, out["cara_x1"]))
            cols = mask[:, x0:x1] > 0.5
            rows = np.where(cols.any(axis=1))[0]
            out["cabeza_y"] = float(rows[0]) if len(rows) else out["frente_y"] - 0.35 * out["alto_cara"]
        return out
