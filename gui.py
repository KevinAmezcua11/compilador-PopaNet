# gui.py - Versión final (sin .vlsmobj). Añade pestaña Cisco IOS.
import tkinter as tk
from tkinter import ttk, font, scrolledtext, messagebox, filedialog

# Componentes del compilador
from lexer import VLSMLexer
from parser import VLSMParser
from semantic import VLSMSemanticAnalyzer
from vlsm_calc import calculate_vlsm
from excel_export import export_to_csv
from utils import TextLineNumbers

from intermediate_code import IntermediateCodeGenerator

# Generador Cisco
from cisco_generator import generate_cisco_config

# VM para leer archivos .ioscfg si deseas ejecutar fuera del router (opcional)
# vm.run_ioscfg simplemente imprime el archivo; incluyendo aquí por si quieres añadir ejecuciones.
try:
    from vm import run_ioscfg
except Exception:
    run_ioscfg = None  # si no existe, no rompemos el GUI

class VLSMApp:
    def __init__(self, root):
        self.root = root
        root.title("Compilador VLSM - Cisco IOS Exporter")

        # UI styling
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure("TNotebook", background="#f5f6fa", tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[10, 5])
        style.configure("TFrame", background="#f5f6fa")
        style.configure("TLabel", background="#f6f6fa", font=("Segoe UI", 10))
        style.configure("Treeview", font=("Consolas", 10), rowheight=24)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("TLabelframe", background="#f5f6fa", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", font=("Segoe UI", 11, "bold"))

        # Fonts
        self.monospace = font.Font(family="Consolas", size=11)

        # Notebook / tabs
        self.notebook = ttk.Notebook(root)
        self.frame_input = ttk.Frame(self.notebook)
        self.frame_tables = ttk.Frame(self.notebook)
        self.frame_tree = ttk.Frame(self.notebook)
        self.frame_intermediate = ttk.Frame(self.notebook)
        self.frame_cisco = ttk.Frame(self.notebook)

        self.notebook.add(self.frame_input, text="Entrada / Salida")
        self.notebook.add(self.frame_tables, text="Tablas")
        self.notebook.add(self.frame_tree, text="Árbol")
        self.notebook.add(self.frame_intermediate, text="Código Intermedio")
        self.notebook.add(self.frame_cisco, text="Cisco IOS")

        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Build each area
        self._build_io(self.frame_input)
        self._build_tables(self.frame_tables)
        self._build_tree_area(self.frame_tree)
        self._build_intermediate_area(self.frame_intermediate)
        self._build_cisco_area(self.frame_cisco)

        # Data containers
        self.vlsm_data = None
        self.tokens = []
        self.derivation_tree = []
        self.generated_cisco = None

    # -----------------------------
    # UI builders
    # -----------------------------
    def _build_io(self, parent):
        input_frame = ttk.LabelFrame(parent, text="Entrada")
        input_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        tf = ttk.Frame(input_frame)
        tf.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        self.linenumbers = TextLineNumbers(tf, width=36, bg="#e9eef2")
        self.linenumbers.pack(side="left", fill="y", padx=(0, 2))

        self.input_text = scrolledtext.ScrolledText(
            tf, wrap=tk.WORD, width=72, height=10, font=self.monospace, background="#fafdff"
        )
        self.input_text.pack(side="left", fill=tk.BOTH, expand=1)
        self.input_text.bind("<KeyRelease>", lambda e: [self.linenumbers.redraw(), self.highlight_reserved_words()])
        self.linenumbers.attach(self.input_text)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Analizar", command=self.analyze, width=16).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Exportar a CSV", command=self.export_to_excel, width=18).pack(side=tk.LEFT, padx=8)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        output_label_frame = ttk.Labelframe(output_frame, text="Salida y Resultados")
        output_label_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        self.output_text = scrolledtext.ScrolledText(
            output_label_frame,
            wrap=tk.WORD,
            width=72,
            height=16,
            state=tk.NORMAL,
            font=("Consolas", 12),
            background="#fafdff",
            foreground="#222"
        )
        self.output_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)

    def _build_tables(self, parent):
        self.sub_notebook = ttk.Notebook(parent)
        self.tab_tokens = ttk.Frame(self.sub_notebook)
        self.tab_reserved = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.tab_tokens, text="Tabla de tokens")
        self.sub_notebook.add(self.tab_reserved, text="Tabla de palabras reservadas")
        self.sub_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cols_tok = ("Tipo", "Valor", "Línea", "Posición")
        self.tv_tokens = ttk.Treeview(self.tab_tokens, columns=cols_tok, show='headings', height=12)
        for c in cols_tok:
            self.tv_tokens.heading(c, text=c)
            self.tv_tokens.column(c, anchor="center", width=140)
        self.tv_tokens.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cols_res = ("Palabra", "Cantidad")
        self.tv_reserved = ttk.Treeview(self.tab_reserved, columns=cols_res, show='headings', height=12)
        for c in cols_res:
            self.tv_reserved.heading(c, text=c)
            self.tv_reserved.column(c, anchor="center", width=160)
        self.tv_reserved.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_tree_area(self, parent):
        self.tree_notebook = ttk.Notebook(parent)
        self.tree_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree_tabs = []

    def _build_intermediate_area(self, parent):
        frame = ttk.LabelFrame(parent, text="Código Intermedio Generado")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_intermediate = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, width=88, height=30,
            font=("Consolas", 11), background="#f7fbff", foreground="#222"
        )
        self.text_intermediate.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_intermediate.config(state=tk.DISABLED)

    def _build_cisco_area(self, parent):
        frame = ttk.LabelFrame(parent, text="Configuración Cisco IOS Generada")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Config listing
        self.text_cisco = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, width=88, height=28,
            font=("Consolas", 11), background="#fcfff5", foreground="#111"
        )
        self.text_cisco.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10,6))
        self.text_cisco.config(state=tk.DISABLED)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(0,10))
        ttk.Button(btn_frame, text="Guardar archivo Cisco (.ioscfg)", command=self.save_cisco).pack(side=tk.LEFT, padx=6)
        if run_ioscfg:
            ttk.Button(btn_frame, text="Ver archivo (ejecutar local)", command=self.run_selected_ios_file).pack(side=tk.LEFT, padx=6)

    # -----------------------------
    # Saving / running Cisco config
    # -----------------------------
    def save_cisco(self):
        if not self.generated_cisco:
            messagebox.showerror("Error", "No hay configuración Cisco generada. Realiza un análisis primero.")
            return

        path = filedialog.asksaveasfilename(
            title="Guardar archivo Cisco",
            defaultextension=".ioscfg",
            filetypes=[("Cisco Config", "*.ioscfg"), ("Text", "*.txt"), ("All", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.generated_cisco)
            messagebox.showinfo("Guardado", f"Archivo Cisco guardado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error guardando archivo Cisco", str(e))

    def run_selected_ios_file(self):
        """
        Abre un diálogo para seleccionar un archivo .ioscfg y lo 'ejecuta' con run_ioscfg (si está disponible).
        El run_ioscfg por defecto solo imprime el contenido; en el futuro puede integrarse con SSH.
        """
        file_path = filedialog.askopenfilename(title="Seleccionar archivo .ioscfg",
                                               filetypes=[("Cisco Config", "*.ioscfg"), ("Text", "*.txt"), ("All", "*.*")])
        if not file_path:
            return

        try:
            if run_ioscfg is None:
                messagebox.showerror("No disponible", "La función run_ioscfg no está disponible en vm.py")
                return
            # run_ioscfg imprime a stdout; capturamos y mostramos en una ventana modal
            output = run_ioscfg(file_path)
            # Si run_ioscfg devuelve texto, mostrarlo; si imprime, puede no devolver nada.
            if output is None:
                # Abrir el archivo y mostrar su contenido
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                output = content

            # Mostrar en ventana
            win = tk.Toplevel(self.root)
            win.title(f"Salida run_ioscfg - {file_path}")
            txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 11))
            txt.pack(fill=tk.BOTH, expand=True)
            txt.insert(tk.END, output)
            txt.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error ejecutando archivo", str(e))

    # -----------------------------
    # Analysis pipeline
    # -----------------------------
    def analyze(self):
        # Reset UI
        self._cleanup_analysis()
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.vlsm_data = None
        self.tokens = []

        code = self.input_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Advertencia", "Por favor introduce un código para analizar.")
            return

        # Lexical
        lexer = VLSMLexer()
        tokens, lex_errors = lexer.tokenize(code)
        self.tokens = tokens

        # Show tokens
        self.output_text.insert(tk.END, "=== ANÁLISIS LÉXICO ===\n")
        for token in tokens:
            token_type, value, line, col = token
            self.output_text.insert(tk.END, f"Token: {token_type} Valor: {value} (L{line},C{col})\n")
        self.populate_tables()

        error_text = ""
        if lex_errors:
            error_text += "=== ERRORES LÉXICOS ===\n"
            for err in lex_errors:
                error_text += f"{err}\n"
            error_text += "\n"

        # Syntax
        parser = VLSMParser(tokens)
        blocks = parser.parse()
        syntax_errors = parser.errors

        # Build tree view
        parser2 = VLSMParser(tokens)
        tree_blocks = parser2.parse_with_tree()
        self.derivation_tree = tree_blocks
        self.draw_tree(tree_blocks)

        if syntax_errors:
            error_text += "=== ERRORES SINTÁCTICOS ===\n"
            for err in syntax_errors:
                error_text += f"{err}\n"
            error_text += "\n"

        # Semantic
        semantic_errors = []
        if not lex_errors and not syntax_errors:
            self.output_text.insert(tk.END, "\n=== ANÁLISIS SINTÁCTICO ===\n")
            for i, block in enumerate(blocks, start=1):
                resumen = (
                    f"Red #{i}:\n"
                    f" \tIP: {block['ip_address']}\n"
                    f" \tMáscara: {block['subnet_mask']}\n"
                    f" \tHosts requeridos: {block['num_hosts']}\n"
                    f" \tNombre: {block.get('name', 'Sin nombre')}\n"
                )
                self.output_text.insert(tk.END, resumen)

            analyzer = VLSMSemanticAnalyzer(blocks)
            if not analyzer.analyze():
                semantic_errors = analyzer.errors

            if semantic_errors:
                error_text += "=== ERRORES SEMÁNTICOS ===\n"
                for err in semantic_errors:
                    error_text += f"{err}\n"
                error_text += "\n"

        # If errors show them
        if error_text:
            self.show_error_popup(error_text)
            self.vlsm_data = None
            self.output_text.config(state=tk.DISABLED)
            return

        # No errors -> calculate VLSM and display results
        if blocks and not lex_errors and not syntax_errors and not semantic_errors:
            self.output_text.insert(tk.END, "\n=== CÁLCULO VLSM ===\n")
            all_results = []
            for block in blocks:
                results = calculate_vlsm(block['ip_address'], block['subnet_mask'], block['num_hosts'], block.get('name'))
                all_results.extend(results)

            self.vlsm_data = all_results

            for res in all_results:
                salida = (
                    f"Hosts solicitados: {res['hosts_solicitados']}\n"
                    f"Hosts encontrados: {res['hosts_encontrados']}\n"
                    f"Dirección de red: {res['direccionamiento_de_red']}\n"
                    f"Nueva máscara: {res['nueva_mascara']}\n"
                    f"Máscara decimal: {res['mascara_decimal']}\n"
                    f"Primera IP utilizable: {res['primera_ip_utilizable']}\n"
                    f"Última IP utilizable: {res['ultima_ip_utilizable']}\n"
                    f"Dirección de broadcast: {res['direccion_de_broadcast']}\n"
                    "--------------------------------------\n"
                )
                self.output_text.insert(tk.END, salida)

        self.output_text.config(state=tk.DISABLED)

        # === Código Intermedio ===
        try:
            generator = IntermediateCodeGenerator(blocks)
            intermediate_result = generator.generate()

            self.text_intermediate.config(state=tk.NORMAL)
            self.text_intermediate.delete("1.0", tk.END)
            self.text_intermediate.insert(tk.END, "=== CÓDIGO INTERMEDIO ===\n")

            if isinstance(intermediate_result, list):
                for instr in intermediate_result:
                    self.text_intermediate.insert(tk.END, str(instr) + "\n")
            else:
                self.text_intermediate.insert(tk.END, str(intermediate_result))

            self.text_intermediate.config(state=tk.DISABLED)
        except Exception as e:
            self.text_intermediate.config(state=tk.NORMAL)
            self.text_intermediate.delete("1.0", tk.END)
            self.text_intermediate.insert(tk.END, f"Error generando código intermedio:\n{e}")
            self.text_intermediate.config(state=tk.DISABLED)

        # === GENERAR CONFIGURACIÓN CISCO ===
        try:
            if self.vlsm_data:
                # default interface prefix can be changed
                self.generated_cisco = generate_cisco_config(self.vlsm_data, interface_prefix="GigabitEthernet0/")
                self.text_cisco.config(state=tk.NORMAL)
                self.text_cisco.delete("1.0", tk.END)
                self.text_cisco.insert(tk.END, self.generated_cisco)
                self.text_cisco.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error generando Cisco config", str(e))

    # -----------------------------
    # Tables / helpers
    # -----------------------------
    def _cleanup_analysis(self):
        for i in self.tv_tokens.get_children():
            self.tv_tokens.delete(i)
        for i in self.tv_reserved.get_children():
            self.tv_reserved.delete(i)
        for tab in getattr(self, 'tree_tabs', []):
            self.tree_notebook.forget(tab)
        self.tree_tabs = []
        self.vlsm_data = None
        self.generated_cisco = None

        if hasattr(self, "text_intermediate"):
            self.text_intermediate.config(state=tk.NORMAL)
            self.text_intermediate.delete("1.0", tk.END)
            self.text_intermediate.config(state=tk.DISABLED)

        if hasattr(self, "text_cisco"):
            self.text_cisco.config(state=tk.NORMAL)
            self.text_cisco.delete("1.0", tk.END)
            self.text_cisco.config(state=tk.DISABLED)

    def export_to_excel(self):
        if self.vlsm_data:
            export_to_csv(self.vlsm_data)
        else:
            messagebox.showerror("Error", "No hay datos válidos para exportar. Realiza un análisis exitoso primero.")

    def populate_tables(self):
        # tokens
        for i in self.tv_tokens.get_children():
            self.tv_tokens.delete(i)
        for i in self.tv_reserved.get_children():
            self.tv_reserved.delete(i)

        if self.tokens:
            for token in self.tokens:
                token_type, value, line, col = token
                self.tv_tokens.insert('', tk.END, values=(token_type, value, line, col))

        # reserved counts
        reserved_words = ['IP', 'MASK', 'HOSTS', 'NAME']
        text = self.input_text.get("1.0", tk.END).upper()
        counts = {word: text.count(word) for word in reserved_words if text.count(word) > 0}
        for word, count in counts.items():
            self.tv_reserved.insert('', tk.END, values=(word, count))

    # -----------------------------
    # Highlighting & lines
    # -----------------------------
    def highlight_reserved_words(self):
        reserved_words = ['IP', 'MASK', 'HOSTS', 'NAME']
        for word in reserved_words:
            self.input_text.tag_remove(word, "1.0", tk.END)
        for word in reserved_words:
            start_index = '1.0'
            while True:
                start_index = self.input_text.search(word, start_index, tk.END, nocase=True)
                if not start_index:
                    break
                end_index = f"{start_index}+{len(word)}c"
                self.input_text.tag_add(word, start_index, end_index)
                self.input_text.tag_config(word, foreground="#0074D9", font=("Consolas", 11, "bold"))
                start_index = end_index

    # -----------------------------
    # Draw tree
    # -----------------------------
    def draw_tree(self, tree):
        # remove old tabs
        for tab in getattr(self, 'tree_tabs', []):
            self.tree_notebook.forget(tab)
        self.tree_tabs = []

        if not tree:
            return

        V_SPACING = 60
        H_SPACING = 90
        FONT = ("Segoe UI", 11, "bold")
        LEAF_FONT = ("Segoe UI", 10, "normal")
        NODE_BG = "#e3eafc"
        NODE_BORDER = "#5b9bd5"
        ROOT_BG = "#d1f2eb"
        ROOT_BORDER = "#148f77"
        LEAF_BG = "#fff9e3"
        LEAF_BORDER = "#f4d03f"

        def get_subtree_width(node):
            label, children = node if isinstance(node, tuple) and isinstance(node[1], list) else (node[0], None)
            if children and len(children) > 0:
                widths = [get_subtree_width(child) for child in children]
                return max(sum(widths), H_SPACING * len(children))
            else:
                return H_SPACING

        def get_tree_height(node, depth=1):
            label, children = node if isinstance(node, tuple) and isinstance(node[1], list) else (node[0], None)
            if children and len(children) > 0:
                return max(get_tree_height(child, depth+1) for child in children)
            else:
                return depth

        for idx, block in enumerate(tree, 1):
            tab = ttk.Frame(self.tree_notebook)
            self.tree_tabs.append(tab)
            self.tree_notebook.add(tab, text=f"Árbol {idx}")

            tree_width = get_subtree_width(block)
            tree_height = get_tree_height(block)
            canvas_width = max(500, tree_width + 100)
            canvas_height = max(250, tree_height * V_SPACING + 80)

            x_scroll = tk.Scrollbar(tab, orient="horizontal")
            y_scroll = tk.Scrollbar(tab, orient="vertical")
            canvas = tk.Canvas(tab, bg="#fafdff",
                                width=canvas_width, height=canvas_height,
                                xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set,
                                highlightthickness=0)
            x_scroll.config(command=canvas.xview)
            y_scroll.config(command=canvas.yview)
            canvas.grid(row=0, column=0, sticky="nsew")
            y_scroll.grid(row=0, column=1, sticky="ns")
            x_scroll.grid(row=1, column=0, sticky="ew")
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

            def draw_node(node, x, y, is_root=False):
                label, children = (
                    node if isinstance(node, tuple) and isinstance(node[1], list)
                    else (node[0], None)
                )

                NODE_RADIUS_Y = 24
                LINE_COLOR = "#4a6fa5"
                LINE_WIDTH = 3
                RED_LEN = 15

                if children and len(children) > 0:
                    parent_red_start_y = y + NODE_RADIUS_Y
                    parent_red_end_y = parent_red_start_y + RED_LEN

                    SMALL_LINE = 15

                    canvas.create_line(x, parent_red_start_y, x, parent_red_end_y, width=2, fill="#4a6fa5", capstyle=tk.ROUND)

                    child_y = y + V_SPACING
                    child_edge_top_y = child_y - NODE_RADIUS_Y

                    widths = [get_subtree_width(child) for child in children]
                    total_width = sum(widths)
                    effective_width = max(total_width, H_SPACING * len(children))
                    start_x = x - effective_width // 2
                    child_centers = []
                    current_x = start_x

                    for i, child in enumerate(children):
                        w = widths[i]
                        effective_w = max(w, H_SPACING)
                        child_x = current_x + effective_w // 2
                        child_centers.append(child_x)
                        current_x += effective_w

                    canvas.create_line(x, parent_red_end_y, x, child_edge_top_y, width=LINE_WIDTH, fill=LINE_COLOR, capstyle=tk.ROUND)

                    if len(child_centers) > 0:
                        canvas.create_line(child_centers[0], child_edge_top_y, child_centers[-1], child_edge_top_y, width=LINE_WIDTH, fill=LINE_COLOR, capstyle=tk.ROUND)

                    for child_x in child_centers:
                        canvas.create_line(child_x, child_edge_top_y, child_x, child_edge_top_y + SMALL_LINE, width=2, fill="#4a6fa5", capstyle=tk.ROUND)

                    for i, child in enumerate(children):
                        draw_node(child, child_centers[i], child_y, is_root=False)

                if is_root:
                    bg, border = ROOT_BG, ROOT_BORDER
                elif children and len(children) > 0:
                    bg, border = NODE_BG, NODE_BORDER
                else:
                    bg, border = LEAF_BG, LEAF_BORDER

                if children:
                    text = f"<{label}>"
                    font = FONT
                    if label == "HOSTS_LIST":
                        y_draw = y + 15
                    else:
                        y_draw = y
                else:
                    # leaf label structure: ('NUMBER', '5') or ('IDENTIFIER', 'Escuela')
                    text = str(node[1]) if isinstance(node, tuple) else str(node)
                    font = LEAF_FONT
                    y_draw = y + 15

                bbox = canvas.create_text(x, y_draw, text=text, font=font, fill="#222", anchor="c")
                bb = canvas.bbox(bbox)
                canvas.delete(bbox)

                pad_x, pad_y = 18, 14
                x0, y0 = bb[0] - pad_x, bb[1] - pad_y
                x1, y1 = bb[2] + pad_x, bb[3] + pad_y

                min_width = 80
                current_width = x1 - x0
                if current_width < min_width:
                    diff = (min_width - current_width) / 2
                    x0 -= diff
                    x1 += diff

                canvas.create_oval(x0, y0, x1, y1, fill=bg, outline=border, width=2)
                canvas.create_text(x, y_draw, text=text, font=font, fill="#222", anchor="c")

            root_x = canvas_width // 2
            root_y = 40
            draw_node(block, root_x, root_y, is_root=True)
            canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

# Run as script for quick testing
if __name__ == "__main__":
    root = tk.Tk()
    # maximize window
    try:
        root.state('zoomed')
    except Exception:
        root.geometry("1200x800")
    app = VLSMApp(root)
    root.mainloop()
