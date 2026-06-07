# data/avatar_movimientos/

Dataset de secuencias temporales para el avatar 3D LSC.

## Formato de cada archivo

Cada seña tiene su propio archivo JSON: `<sena>.json`

```json
{
  "sena": "bien",
  "categoria": "emociones",
  "manos": "1",
  "duracion": "corta",
  "total_frames": 15,
  "calidad_pct": 93.3,
  "coordenadas": "normalizadas",
  "frames": [
    {
      "f": 0,
      "der": [[nx,ny,nz], ...],   // 21 landmarks mano derecha o null
      "izq": [[nx,ny,nz], ...]    // 21 landmarks mano izquierda o null
    },
    ...
  ]
}
```

## Sistema de coordenadas normalizadas

- **Origen**: nariz del firmante  
- **Escala**: 1 unidad = distancia nariz-pecho (en Y de imagen)  
- **X**: positivo = derecha del frame (= izquierda del firmante)  
- **Y**: positivo = arriba (Y imagen invertida)  
- **Z**: positivo = hacia la cámara (Z de MediaPipe negado)  

## Cómo capturar

```powershell
& "venv\Scripts\python.exe" "src\capturar_avatar.py"
```

## Señas capturadas

| Seña | Categoría | Manos | Duración | Calidad |
|------|-----------|-------|----------|---------|
| (ninguna aún) | | | | |
