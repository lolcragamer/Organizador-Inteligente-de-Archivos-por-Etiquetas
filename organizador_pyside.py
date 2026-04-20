import os
import shutil
import json
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QGroupBox, QSplitter,
    QAbstractItemView, QInputDialog, QListWidget, QListWidgetItem,
    QMenu
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QAction, QDrag

DATABASE_FILE = "etiquetas_archivos.json"
SUGERENCIAS_FILE = "sugerencias.json"

# Etiquetas sugeridas por defecto
DEFAULT_SUGGESTIONS = [
    "contabilidad", "ciber3", "ciber4", "practicas",
    "laboratorios", "material", "sin clasificar", "facturas",
    "proyectos", "fotos", "videos", "documentos"
]

class TablaArchivosEtiquetados(QTableWidget):
    """Subclase de QTableWidget para soportar arrastrar filas (drag)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)  # No recibe drops, solo envía
        self.setDragDropMode(QAbstractItemView.DragOnly)

    def startDrag(self, supportedActions):
        """Capturar las filas seleccionadas y crear un QDrag con sus rutas"""
        rows = set()
        for item in self.selectedItems():
            rows.add(item.row())
        if not rows:
            return

        # Obtener las rutas de los archivos de las filas seleccionadas
        rutas = []
        for row in rows:
            item = self.item(row, 0)
            if item:
                rutas.append(item.text())

        if not rutas:
            return

        # Crear datos MIME con las rutas separadas por newline
        mime_data = QMimeData()
        mime_data.setText("\n".join(rutas))
        mime_data.setData("application/x-fileruta", "\n".join(rutas).encode())

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)

class ListaSeleccionArchivos(QTableWidget):
    """Subclase de QTableWidget para recibir drops (archivos arrastrados)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.ventana_principal = parent

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            texto = event.mimeData().text()
            rutas = texto.split("\n")
            if self.ventana_principal and hasattr(self.ventana_principal, 'archivos_seleccionados'):
                for r in rutas:
                    if r and os.path.exists(r) and r not in self.ventana_principal.archivos_seleccionados:
                        self.ventana_principal.archivos_seleccionados.append(r)
                self.ventana_principal.actualizar_lista_seleccion()
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

class OrganizadorAvanzado(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organizador Inteligente por Etiquetas")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet("""
            QMainWindow { background-color: #000000; }
            QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; color: white; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { background-color: #6fa8dc; border: 1px solid #aaa; border-radius: 4px; padding: 5px; color: black; }
            QPushButton:hover { background-color: #8fc8ff; }
            QPushButton#organizar { background-color: #4CAF50; color: white; font-weight: bold; }
            QPushButton#organizar:hover { background-color: #45a049; }
            QTableWidget { alternate-background-color: #073763; color: white; }
            QHeaderView::section { background-color: #6fa8dc; padding: 4px; color: black; }
            QListWidget { color: white; background-color: #1a1a1a; }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #444; }
            QListWidget::item:selected { background-color: #2a6da8; color: white; }
            QLabel { color: white; }
            QLineEdit { background-color: #2a2a2a; color: white; border: 1px solid #555; }
        """)

        # Datos
        self.archivos_seleccionados = []
        self.carpeta_raiz = None
        self.etiquetas = self.cargar_bd()
        self.sugerencias = self.cargar_sugerencias()

        # UI
        self.setup_ui()
        self.actualizar_tabla()

    # -------------------- BASE DE DATOS --------------------
    def cargar_bd(self):
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def guardar_bd(self):
        with open(DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.etiquetas, f, indent=4, ensure_ascii=False)

    def cargar_sugerencias(self):
        if os.path.exists(SUGERENCIAS_FILE):
            with open(SUGERENCIAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_SUGGESTIONS.copy()

    def guardar_sugerencias(self):
        with open(SUGERENCIAS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.sugerencias, f, indent=4, ensure_ascii=False)

    # -------------------- INTERFAZ --------------------
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter_principal = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter_principal)

        # --- PANEL IZQUIERDO (Selección y asignación) ---
        panel_izq = QWidget()
        layout_izq = QVBoxLayout(panel_izq)

        grupo_seleccion = QGroupBox("📂 1. Seleccionar archivos")
        layout_sel = QVBoxLayout(grupo_seleccion)
        btn_agregar = QPushButton("➕ Agregar archivos")
        btn_agregar.clicked.connect(self.agregar_archivos)
        layout_sel.addWidget(btn_agregar)

        # Usar nuestra subclase para la lista de selección (acepta drops)
        self.lista_seleccion = ListaSeleccionArchivos(self)
        self.lista_seleccion.setColumnCount(1)
        self.lista_seleccion.setHorizontalHeaderLabels(["Ruta del archivo"])
        self.lista_seleccion.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.lista_seleccion.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lista_seleccion.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout_sel.addWidget(self.lista_seleccion)

        btn_limpiar = QPushButton("🗑️ Limpiar selección")
        btn_limpiar.clicked.connect(self.limpiar_seleccion)
        layout_sel.addWidget(btn_limpiar)

        layout_izq.addWidget(grupo_seleccion)

        grupo_etiqueta = QGroupBox("🏷️ 2. Asignar etiquetas (separadas por comas)")
        layout_etq = QVBoxLayout(grupo_etiqueta)
        self.input_etiqueta = QLineEdit()
        self.input_etiqueta.setPlaceholderText("Ejemplo: contabilidad,practica  →  contabilidad/practica/")
        layout_etq.addWidget(self.input_etiqueta)

        btn_asignar = QPushButton("📌 Asignar a archivos seleccionados")
        btn_asignar.clicked.connect(self.asignar_etiqueta)
        layout_etq.addWidget(btn_asignar)

        layout_izq.addWidget(grupo_etiqueta)

        grupo_organizar = QGroupBox("📁 3. Carpeta de destino y organizar")
        layout_org = QVBoxLayout(grupo_organizar)
        btn_raiz = QPushButton("📂 Seleccionar carpeta raíz")
        btn_raiz.clicked.connect(self.seleccionar_carpeta_raiz)
        layout_org.addWidget(btn_raiz)

        self.label_raiz = QLabel("Ninguna carpeta seleccionada")
        self.label_raiz.setWordWrap(True)
        self.label_raiz.setStyleSheet("color: gray;")
        layout_org.addWidget(self.label_raiz)

        btn_organizar = QPushButton("🚀 ORGANIZAR ARCHIVOS")
        btn_organizar.setObjectName("organizar")
        btn_organizar.clicked.connect(self.organizar)
        layout_org.addWidget(btn_organizar)

        layout_izq.addWidget(grupo_organizar)
        layout_izq.addStretch()

        # --- PANEL CENTRAL (Sugerencias de etiquetas) ---
        panel_centro = QWidget()
        layout_centro = QVBoxLayout(panel_centro)

        grupo_sugerencias = QGroupBox("💡 Etiquetas sugeridas")
        layout_sug = QVBoxLayout(grupo_sugerencias)

        self.lista_sugerencias = QListWidget()
        self.lista_sugerencias.setSelectionMode(QListWidget.SingleSelection)
        self.lista_sugerencias.itemDoubleClicked.connect(self.agregar_etiqueta_sugerida_al_input)
        self.lista_sugerencias.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lista_sugerencias.customContextMenuRequested.connect(self.menu_sugerencias)
        layout_sug.addWidget(self.lista_sugerencias)

        btn_agregar_sug = QPushButton("➕ Agregar nueva etiqueta sugerida")
        btn_agregar_sug.clicked.connect(self.agregar_nueva_sugerencia)
        layout_sug.addWidget(btn_agregar_sug)

        layout_centro.addWidget(grupo_sugerencias)

        # --- PANEL DERECHO (Tabla de archivos etiquetados con drag) ---
        panel_der = QWidget()
        layout_der = QVBoxLayout(panel_der)

        grupo_tabla = QGroupBox("📋 Archivos etiquetados")
        layout_tabla = QVBoxLayout(grupo_tabla)

        # Usar subclase con drag habilitado
        self.tabla_archivos = TablaArchivosEtiquetados(self)
        self.tabla_archivos.setColumnCount(3)
        self.tabla_archivos.setHorizontalHeaderLabels(["Archivo", "Etiquetas (jerarquía)", "Acciones"])
        self.tabla_archivos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_archivos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_archivos.setColumnWidth(2, 120)
        self.tabla_archivos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_archivos.setAlternatingRowColors(True)
        self.tabla_archivos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_archivos.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout_tabla.addWidget(self.tabla_archivos)

        btn_refrescar = QPushButton("🔄 Refrescar lista")
        btn_refrescar.clicked.connect(self.actualizar_tabla)
        layout_tabla.addWidget(btn_refrescar)

        btn_reetiquetar = QPushButton("🏷️ Re-etiquetar seleccionados")
        btn_reetiquetar.clicked.connect(self.reetiquetar_seleccionados)
        layout_tabla.addWidget(btn_reetiquetar)

        btn_mover = QPushButton("⬅ Mover seleccionados a 'Agregar archivos'")
        btn_mover.clicked.connect(self.mover_seleccionados_a_izquierda)
        layout_tabla.addWidget(btn_mover)

        layout_der.addWidget(grupo_tabla)

        splitter_principal.addWidget(panel_izq)
        splitter_principal.addWidget(panel_centro)
        splitter_principal.addWidget(panel_der)
        splitter_principal.setSizes([300, 200, 500])

        self.cargar_lista_sugerencias()

    def cargar_lista_sugerencias(self):
        self.lista_sugerencias.clear()
        for sug in self.sugerencias:
            item = QListWidgetItem(sug)
            item.setToolTip("Haz doble clic para añadir esta etiqueta al campo de texto")
            self.lista_sugerencias.addItem(item)

    def agregar_etiqueta_sugerida_al_input(self, item):
        etiqueta = item.text()
        texto_actual = self.input_etiqueta.text().strip()
        if texto_actual:
            self.input_etiqueta.setText(f"{texto_actual}, {etiqueta}")
        else:
            self.input_etiqueta.setText(etiqueta)

    def menu_sugerencias(self, pos):
        menu = QMenu()
        eliminar_action = QAction("Eliminar etiqueta sugerida", self)
        eliminar_action.triggered.connect(self.eliminar_sugerencia_seleccionada)
        menu.addAction(eliminar_action)
        menu.exec(self.lista_sugerencias.mapToGlobal(pos))

    def eliminar_sugerencia_seleccionada(self):
        item = self.lista_sugerencias.currentItem()
        if item:
            etiqueta = item.text()
            resp = QMessageBox.question(self, "Confirmar", f"¿Eliminar '{etiqueta}' de las sugerencias?",
                                        QMessageBox.Yes | QMessageBox.No)
            if resp == QMessageBox.Yes:
                self.sugerencias.remove(etiqueta)
                self.guardar_sugerencias()
                self.cargar_lista_sugerencias()

    def agregar_nueva_sugerencia(self):
        texto, ok = QInputDialog.getText(self, "Nueva etiqueta sugerida", "Nombre de la etiqueta:")
        if ok and texto.strip():
            nueva = texto.strip()
            if nueva not in self.sugerencias:
                self.sugerencias.append(nueva)
                self.guardar_sugerencias()
                self.cargar_lista_sugerencias()
            else:
                QMessageBox.information(self, "Ya existe", f"'{nueva}' ya está en la lista de sugerencias.")

    # -------------------- MANEJO DE ARCHIVOS SELECCIONADOS --------------------
    def agregar_archivos(self):
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos")
        for r in rutas:
            if r not in self.archivos_seleccionados:
                self.archivos_seleccionados.append(r)
        self.actualizar_lista_seleccion()

    def actualizar_lista_seleccion(self):
        self.lista_seleccion.setRowCount(len(self.archivos_seleccionados))
        for i, ruta in enumerate(self.archivos_seleccionados):
            item = QTableWidgetItem(ruta)
            self.lista_seleccion.setItem(i, 0, item)

    def limpiar_seleccion(self):
        self.archivos_seleccionados.clear()
        self.lista_seleccion.setRowCount(0)

    # -------------------- ASIGNAR ETIQUETAS --------------------
    def asignar_etiqueta(self):
        if not self.archivos_seleccionados:
            QMessageBox.warning(self, "Sin archivos", "Selecciona o agrega archivos primero.")
            return
        texto_etiquetas = self.input_etiqueta.text().strip()
        if not texto_etiquetas:
            QMessageBox.warning(self, "Sin etiquetas", "Escribe al menos una etiqueta.")
            return

        etiquetas = [e.strip() for e in texto_etiquetas.split(",") if e.strip()]
        if not etiquetas:
            return

        for archivo in self.archivos_seleccionados:
            self.etiquetas[archivo] = etiquetas
        self.guardar_bd()
        self.actualizar_tabla()
        QMessageBox.information(self, "Éxito", f"Etiquetas '{' → '.join(etiquetas)}' asignadas a {len(self.archivos_seleccionados)} archivo(s).")
        self.limpiar_seleccion()
        self.input_etiqueta.clear()

    # -------------------- TABLA DE ARCHIVOS ETIQUETADOS --------------------
    def actualizar_tabla(self):
        self.tabla_archivos.setRowCount(len(self.etiquetas))
        for i, (ruta, etiquetas) in enumerate(self.etiquetas.items()):
            if not os.path.exists(ruta):
                continue

            item_ruta = QTableWidgetItem(ruta)
            item_ruta.setToolTip(ruta)
            self.tabla_archivos.setItem(i, 0, item_ruta)

            texto_etq = " → ".join(etiquetas)
            item_etq = QTableWidgetItem(texto_etq)
            item_etq.setToolTip("Jerarquía de carpetas: " + texto_etq)
            self.tabla_archivos.setItem(i, 1, item_etq)

            widget_botones = QWidget()
            layout_botones = QHBoxLayout(widget_botones)
            layout_botones.setContentsMargins(5, 2, 5, 2)
            btn_editar = QPushButton("✏️")
            btn_editar.setMaximumWidth(30)
            btn_editar.setToolTip("Editar etiquetas")
            btn_editar.clicked.connect(lambda checked, r=ruta: self.editar_etiquetas(r))
            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setMaximumWidth(30)
            btn_eliminar.setToolTip("Eliminar de la lista")
            btn_eliminar.clicked.connect(lambda checked, r=ruta: self.eliminar_archivo(r))
            layout_botones.addWidget(btn_editar)
            layout_botones.addWidget(btn_eliminar)
            self.tabla_archivos.setCellWidget(i, 2, widget_botones)

        self.tabla_archivos.resizeRowsToContents()

    def editar_etiquetas(self, ruta):
        etiquetas_actuales = self.etiquetas.get(ruta, [])
        texto_actual = ",".join(etiquetas_actuales)
        nuevo_texto, ok = QInputDialog.getText(self, "Editar etiquetas", 
                                               "Nuevas etiquetas (separadas por comas):",
                                               text=texto_actual)
        if ok and nuevo_texto.strip():
            nuevas = [e.strip() for e in nuevo_texto.split(",") if e.strip()]
            if nuevas:
                self.etiquetas[ruta] = nuevas
                self.guardar_bd()
                self.actualizar_tabla()
                QMessageBox.information(self, "Actualizado", "Etiquetas modificadas.")
            else:
                QMessageBox.warning(self, "Error", "Debes escribir al menos una etiqueta.")

    def eliminar_archivo(self, ruta):
        resp = QMessageBox.question(self, "Confirmar", f"¿Eliminar '{ruta}' de la base de datos?\n(El archivo físico no se borrará)",
                                    QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            del self.etiquetas[ruta]
            self.guardar_bd()
            self.actualizar_tabla()

    def reetiquetar_seleccionados(self):
        selected_rows = set()
        for item in self.tabla_archivos.selectedItems():
            selected_rows.add(item.row())
        if not selected_rows:
            QMessageBox.warning(self, "Sin selección", "Selecciona al menos un archivo en la tabla.")
            return

        rutas = []
        for row in selected_rows:
            item_ruta = self.tabla_archivos.item(row, 0)
            if item_ruta:
                rutas.append(item_ruta.text())

        texto_etiquetas, ok = QInputDialog.getText(self, "Re-etiquetar", 
                                                   "Nuevas etiquetas (separadas por comas):")
        if not ok or not texto_etiquetas.strip():
            return

        nuevas = [e.strip() for e in texto_etiquetas.split(",") if e.strip()]
        if not nuevas:
            QMessageBox.warning(self, "Error", "Debes escribir al menos una etiqueta.")
            return

        for ruta in rutas:
            self.etiquetas[ruta] = nuevas
        self.guardar_bd()
        self.actualizar_tabla()
        QMessageBox.information(self, "Actualizado", f"Se re-etiquetaron {len(rutas)} archivo(s) con: {' → '.join(nuevas)}")

    def mover_seleccionados_a_izquierda(self):
        selected_rows = set()
        for item in self.tabla_archivos.selectedItems():
            selected_rows.add(item.row())
        if not selected_rows:
            QMessageBox.warning(self, "Sin selección", "Selecciona al menos un archivo en la tabla para mover.")
            return
        for row in selected_rows:
            ruta = self.tabla_archivos.item(row, 0).text()
            if ruta not in self.archivos_seleccionados:
                self.archivos_seleccionados.append(ruta)
        self.actualizar_lista_seleccion()
        QMessageBox.information(self, "Movidos", f"{len(selected_rows)} archivo(s) añadidos a la lista de selección izquierda.")

    # -------------------- SELECCIÓN DE CARPETA RAÍZ --------------------
    def seleccionar_carpeta_raiz(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta raíz donde se crearán las subcarpetas")
        if carpeta:
            self.carpeta_raiz = carpeta
            self.label_raiz.setText(f"📁 Carpeta raíz: {carpeta}")
            self.label_raiz.setStyleSheet("color: white;")

    # -------------------- ORGANIZACIÓN --------------------
    def organizar(self):
        if not self.carpeta_raiz:
            QMessageBox.warning(self, "Sin raíz", "Primero selecciona una carpeta raíz.")
            return
        if not self.etiquetas:
            QMessageBox.information(self, "Sin datos", "No hay archivos etiquetados.")
            return

        contador = 0
        errores = []
        nuevas_etiquetas = {}

        for archivo, jerarquia in self.etiquetas.items():
            if not os.path.exists(archivo):
                errores.append(f"No existe: {archivo}")
                continue

            ruta_actual = self.carpeta_raiz
            for nombre_carpeta in jerarquia:
                carpeta_existente = self.encontrar_carpeta_case_insensitive(ruta_actual, nombre_carpeta)
                if carpeta_existente:
                    ruta_actual = carpeta_existente
                else:
                    nueva_ruta = os.path.join(ruta_actual, nombre_carpeta)
                    os.makedirs(nueva_ruta, exist_ok=True)
                    ruta_actual = nueva_ruta

            destino = os.path.join(ruta_actual, os.path.basename(archivo))
            base, ext = os.path.splitext(destino)
            cont = 1
            while os.path.exists(destino):
                destino = f"{base}_{cont}{ext}"
                cont += 1

            try:
                shutil.move(archivo, destino)
                contador += 1
            except Exception as e:
                errores.append(f"{archivo}: {str(e)}")
                nuevas_etiquetas[archivo] = jerarquia

        for archivo in list(self.etiquetas.keys()):
            if os.path.exists(archivo):
                nuevas_etiquetas[archivo] = self.etiquetas[archivo]
        self.etiquetas = nuevas_etiquetas
        self.guardar_bd()
        self.actualizar_tabla()

        msg = f"✅ Se organizaron {contador} archivo(s) correctamente."
        if errores:
            msg += f"\n\n⚠️ Errores ({len(errores)}):\n" + "\n".join(errores[:5])
        QMessageBox.information(self, "Organización completada", msg)

    def encontrar_carpeta_case_insensitive(self, ruta_padre, nombre_carpeta):
        if not os.path.exists(ruta_padre):
            return None
        try:
            for item in os.listdir(ruta_padre):
                ruta_item = os.path.join(ruta_padre, item)
                if os.path.isdir(ruta_item) and item.lower() == nombre_carpeta.lower():
                    return ruta_item
        except PermissionError:
            pass
        return None

# -------------------- PUNTO DE ENTRADA --------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = OrganizadorAvanzado()
    ventana.show()
    sys.exit(app.exec())