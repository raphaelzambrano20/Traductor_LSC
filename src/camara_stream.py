import threading
import time
import cv2


class CamaraStream:
    """Lee frames en un hilo de fondo para eliminar el retraso acumulado en IP cameras."""

    def __init__(self, fuente=0, timeout=10):
        self.cap = cv2.VideoCapture(fuente)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._ret = False
        self._frame = None
        self._lock = threading.Lock()
        self._activa = True
        self._primer_frame = threading.Event()
        self._thread = threading.Thread(target=self._leer, daemon=True)
        self._thread.start()
        # Espera hasta recibir el primer frame antes de continuar
        self._primer_frame.wait(timeout=timeout)

    def _leer(self):
        while self._activa:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._ret = ret
                    self._frame = frame
                self._primer_frame.set()

    def read(self):
        with self._lock:
            if self._frame is None:
                return False, None
            return self._ret, self._frame.copy()

    def set(self, prop, valor):
        self.cap.set(prop, valor)

    def isOpened(self):
        return self._primer_frame.is_set()

    def release(self):
        self._activa = False
        self._thread.join(timeout=2)
        self.cap.release()
