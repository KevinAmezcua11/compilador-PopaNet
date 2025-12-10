# vm.py

"""
VM para manejar archivos .ioscfg generados por el compilador.

Este módulo funciona como una "máquina virtual" muy básica:
- Abre archivos .ioscfg generados por el compilador.
- Lee su contenido.
- Lo muestra dentro de una ventana en la GUI con un encabezado estilo consola.

En versiones futuras podría integrarse con librerías como Netmiko
para enviar la configuración directamente a un dispositivo Cisco real.
"""

def run_ioscfg(path):
    """
    Función que recibe la ruta de un archivo .ioscfg.
    Abre el archivo, lee todo su contenido y lo regresa como un string.
    La GUI utilizará esta función para mostrar el texto generado por el compilador.

    Parámetros:
        path (str): Ruta completa del archivo .ioscfg.
    """

    try:
        # Abre el archivo en modo lectura (r), usando codificación UTF-8.
        # El 'with' asegura que el archivo se cierre automáticamente al terminar.
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()  # Lee todo el contenido del archivo.

        # Cabecera simulada estilo "máquina virtual".
        # Esto solo es decoración para mostrar en la GUI.
        header = (
            "================= VM CISCO IOSCFG =================\n"
            f"Archivo: {path}\n"
            "===================================================\n\n"
        )

        # Regresa la cabecera y el contenido del archivo concatenados.
        return header + content

    except Exception as e:
        # Si ocurre cualquier error (archivo inexistente, permisos, etc.),
        # devolvemos un mensaje indicando que la VM no lo pudo leer.
        return f"[VM-ERROR] No se pudo leer el archivo: {e}"