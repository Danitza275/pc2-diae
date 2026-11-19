"""Clasificación de imágenes con un modelo ViT (google/vit-base-patch16-224).

La Inference API de Hugging Face ahora cobra (402), así que el modelo ONNX
del mismo ViT se descarga una vez con huggingface_hub y se ejecuta en local
con onnxruntime (CPU, sin GPU y sin torch ni transformers).

Si la inferencia local falla (por ejemplo, sin el modelo descargado), se
intenta la Inference API de Hugging Face con HF_TOKEN como respaldo.
"""
import io
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from PIL import Image

REPO = 'Xenova/vit-base-patch16-224'          # mismo ViT exportado a ONNX
ARCHIVO = 'onnx/model.onnx'
TOP = 5

_cache = {'sesion': None, 'etiquetas': {}, 'pre': {}}


def _cargar_modelo():
    """Descarga (la primera vez) y prepara la sesión de ONNX Runtime."""
    if _cache['sesion'] is None:
        ruta = hf_hub_download(REPO, ARCHIVO)
        config = json.loads(Path(hf_hub_download(REPO, 'config.json')).read_text())
        pre = json.loads(Path(hf_hub_download(REPO, 'preprocessor_config.json')).read_text())
        _cache['etiquetas'] = config.get('id2label', {})
        _cache['pre'] = pre
        _cache['sesion'] = ort.InferenceSession(ruta, providers=['CPUExecutionProvider'])
    return _cache


def _preparar_imagen(datos, pre):
    """Convierte los bytes de la imagen en el tensor que espera el modelo."""
    tam = pre.get('size', {}) or {}
    alto = int(tam.get('height') or tam.get('shortest_edge') or 224)
    ancho = int(tam.get('width') or tam.get('shortest_edge') or 224)
    media = np.array(pre.get('image_mean', [0.485, 0.456, 0.406]), dtype=np.float32)
    desvio = np.array(pre.get('image_std', [0.229, 0.224, 0.225]), dtype=np.float32)

    imagen = Image.open(io.BytesIO(datos)).convert('RGB')
    imagen = imagen.resize((ancho, alto), Image.BILINEAR)   # igual que ViTFeatureExtractor
    tensor = np.asarray(imagen, dtype=np.float32) / 255.0
    tensor = (tensor - media) / desvio
    return tensor.transpose(2, 0, 1)[np.newaxis, ...]   # NCHW


def clasificar_local(datos):
    """Devuelve los TOP resultados [{label, score}, ...] usando ONNX en local."""
    modelo = _cargar_modelo()
    sesion = modelo['sesion']

    entrada = sesion.get_inputs()[0]
    tensor = _preparar_imagen(datos, modelo['pre'])
    canal = entrada.shape[1] if len(entrada.shape) > 1 else 3
    if isinstance(canal, int) and canal != 3:           # si espera NHWC
        tensor = tensor.transpose(0, 2, 3, 1)

    logits = sesion.run(None, {entrada.name: tensor})[0][0]

    exp = np.exp(logits - np.max(logits))
    probabilidades = exp / exp.sum()
    mejores = np.argsort(probabilidades)[::-1][:TOP]

    return [{
        'label': str(modelo['etiquetas'].get(str(i), i)),
        'score': round(float(probabilidades[i]), 4),
    } for i in mejores]


def clasificar_hf(datos, token):
    """Respaldo: Inference API de Hugging Face (requiere créditos en la cuenta)."""
    from huggingface_hub import InferenceClient
    cliente = InferenceClient(model='google/vit-base-patch16-224', token=token)
    return [{
        'label': r['label'] if isinstance(r, dict) else r.label,
        'score': round(float(r['score'] if isinstance(r, dict) else r.score), 4),
    } for r in cliente.image_classification(datos)[:TOP]]


def clasificar_imagen(datos, token=''):
    """Clasifica con el modelo local; si falla, intenta la Inference API."""
    try:
        etiquetas = clasificar_local(datos)
        return etiquetas, 'vit-base-patch16-224 (in local con ONNX Runtime)'
    except Exception as error_local:
        if token:
            etiquetas = clasificar_hf(datos, token)
            return etiquetas, 'google/vit-base-patch16-224 (Inference API)'
        raise RuntimeError(
            'No se pudo cargar el modelo local y tampoco hay HF_TOKEN: '
            + str(error_local).splitlines()[0])
