import threading
import time
import cv2


class CamaraStream:
    """Abstracción de cámara con dos modos según la fuente:

    - Cámara LOCAL (int, ej: 0): lectura directa sin hilo de fondo.
      No usa CAP_PROP_BUFFERSIZE. cap.set() se aplica antes del primer read().
      Evita el problema de congelamiento con el backend MSMF en Windows.

    - Cámara IP (str URL, ej: DroidCam): hilo de fondo que descarta frames
      acumulados en el buffer de red, eliminando el retraso de lag.
    """

    def __init__(self, fuente=0, timeout=10):
        self._es_local = isinstance(fuente, int)
        self.cap = cv2.VideoCapture(fuente)

        if self._es_local:
            # Cámara local: sin hilo de fondo, sin buffer forzado.
            # read() llama cap.read() directamente en el hilo del llamador.
            self._lock = threading.Lock()  # Protege acceso concurrente a cap
        else:
            # Cámara IP: hilo de fondo para descartar frames viejos acumulados.
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._ret = False
            self._frame = None
            self._lock = threading.Lock()
            self._activa = True
            self._primer_frame = threading.Event()
            self._thread = threading.Thread(target=self._leer, daemon=True)
            self._thread.start()
            self._primer_frame.wait(timeout=timeout)

    def _leer(self):
        """Solo se usa para cámaras IP."""
        while self._activa:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._ret = ret
                    self._frame = frame
                self._primer_frame.set()

    def read(self):
        if self._es_local:
            # Lectura directa: cap.read() bloquea hasta que llega el próximo frame.
            with self._lock:
                return self.cap.read()
        else:
            # Devuelve el último frame capturado por el hilo de fondo.
            with self._lock:
                if self._frame is None:
                    return False, None
                return self._ret, self._frame.copy()

    def set(self, prop, valor):
        """Aplica propiedad a la cámara (resolución, FPS, etc.)."""
        with self._lock:
            self.cap.set(prop, valor)

    def isOpened(self):
        if self._es_local:
            return self.cap.isOpened()
        return self._primer_frame.is_set()

    def release(self):
        if self._es_local:
            with self._lock:
                self.cap.release()
        else:
            self._activa = False
            self._thread.join(timeout=2)
            self.cap.release()
