# excel_export.py
import csv
from tkinter import filedialog, messagebox

def export_to_csv(vlsm_data):
    """
    Exporta la lista de resultados VLSM a CSV.
    vlsm_data: lista de diccionarios (como devuelve vlsm_calc.calculate_vlsm)
    """
    if not vlsm_data:
        messagebox.showerror("Error", "No hay datos para exportar.")
        return

    path = filedialog.asksaveasfilename(defaultextension=".csv",
                                        filetypes=[("CSV", "*.csv"), ("All", "*.*")])

    if not path:
        return

    headers = [
        'nombre_red', 'ip_base', 'hosts_solicitados', 'hosts_encontrados',
        'direccionamiento_de_red', 'nueva_mascara', 'mascara_decimal',
        'primera_ip_utilizable', 'ultima_ip_utilizable', 'direccion_de_broadcast'
    ]

    try:
        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for row in vlsm_data:
                out = {k: row.get(k, "") for k in headers}
                writer.writerow(out)

        messagebox.showinfo("Exportado", f"CSV guardado en: {path}")

    except Exception as e:
        messagebox.showerror("Error exportando CSV", str(e))
