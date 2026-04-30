from voz import hablar_windows


if __name__ == "__main__":
    print("Probando voz de Windows...")
    hablar_windows("Prueba de voz del traductor LSC", esperar=True)
    print("Si escucho el mensaje, la voz esta funcionando.")
