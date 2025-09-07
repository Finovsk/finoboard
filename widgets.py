from __future__ import annotations
from PySide6 import QtCore, QtWidgets, QtGui
import os

class ElidedLabel(QtWidgets.QLabel):
    def __init__(self, text: str = "", parent=None,
                 mode: QtCore.Qt.TextElideMode = QtCore.Qt.TextElideMode.ElideRight):
        super().__init__(text, parent)
        self._full_text = text
        self._elide_mode = mode
        self.setMinimumWidth(40)

    def setText(self, text: str) -> None:
        self._full_text = text
        super().setText(text)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        metrics = self.fontMetrics()
        elided = metrics.elidedText(self._full_text, self._elide_mode, self.width())
        flags = int(self.alignment()) | QtCore.Qt.TextSingleLine
        painter.drawText(self.rect(), flags, elided)


class HotkeyDialog(QtWidgets.QDialog):
    def __init__(self, tr, current: str = "", parent=None):
        super().__init__(parent)
        self.tr = tr
        self.setModal(True)
        self.setWindowTitle(self.tr.t("hotkey_title"))

        layout = QtWidgets.QVBoxLayout(self)
        info = QtWidgets.QLabel(self.tr.t("hotkey_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.edit = QtWidgets.QKeySequenceEdit(self)
        if current:
            self.edit.setKeySequence(QtGui.QKeySequence(current))
        layout.addWidget(self.edit)

        row = QtWidgets.QHBoxLayout()
        self.btnClear = QtWidgets.QPushButton(self.tr.t("hotkey_clear"))
        self.btnCancel = QtWidgets.QPushButton(self.tr.t("cancel"))
        self.btnOK = QtWidgets.QPushButton(self.tr.t("ok"))
        row.addWidget(self.btnClear)
        row.addStretch(1)
        row.addWidget(self.btnCancel)
        row.addWidget(self.btnOK)
        layout.addLayout(row)

        self.btnOK.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)
        self.btnClear.clicked.connect(self._on_clear)

    def _on_clear(self):
        self.edit.clear()
        self.accept()

    def result_hotkey(self) -> str:
        seq = self.edit.keySequence().toString(QtGui.QKeySequence.PortableText)
        return (seq or "").lower()


class SoundItemWidget(QtWidgets.QWidget):
    playClicked = QtCore.Signal(str)
    removeClicked = QtCore.Signal()
    renameClicked = QtCore.Signal(str)
    hotkeyChanged = QtCore.Signal(str)

    def __init__(self, tr, path: str, display_name: str | None = None,
                 hotkey: str | None = None, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.path = path
        self.display_name = display_name or os.path.basename(path)
        self.hotkey = (hotkey or "").strip()
        self._build_ui()
        self._apply_hotkey_style()

    def _build_ui(self):
        self.setObjectName("SoundItem")
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Card externo (visual roxinho)
        self.card = QtWidgets.QFrame()
        self.card.setObjectName("RowCard")
        self.card.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.card.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.card)

        layout = QtWidgets.QHBoxLayout(self.card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        self.btnPlay = QtWidgets.QPushButton("▶")
        self.btnPlay.setObjectName("BtnPlayList")
        self.btnPlay.setFixedWidth(64)
        self.btnPlay.setCursor(QtCore.Qt.PointingHandCursor)
        self.btnPlay.clicked.connect(lambda: self.playClicked.emit(self.path))
        layout.addWidget(self.btnPlay, 0, QtCore.Qt.AlignVCenter)

        midBox = QtWidgets.QVBoxLayout(); midBox.setSpacing(4)
        self.lblName = ElidedLabel(self.display_name)
        self.lblName.setStyleSheet("background: transparent;")  # <- mantém fundo igual ao do card
        f = self.lblName.font(); f.setPointSizeF(f.pointSizeF() + 1); self.lblName.setFont(f)
        self.lblHotkey = QtWidgets.QLabel(); self.lblHotkey.setObjectName("Badge")
        self.lblHotkey.setStyleSheet("QLabel#Badge { background:#2c2840; color:#eae6ff; border-radius:6px; padding:2px 8px; }")
        hkrow = QtWidgets.QHBoxLayout(); hkrow.addWidget(self.lblHotkey, 0, QtCore.Qt.AlignLeft); hkrow.addStretch(1)
        midBox.addWidget(self.lblName); midBox.addLayout(hkrow)
        layout.addLayout(midBox, 1)

        self.btnHotkey = QtWidgets.QToolButton(); self._as_icon(self.btnHotkey, "⌨", self.tr.t("tip_hotkey"))
        self.btnRename = QtWidgets.QToolButton(); self._as_icon(self.btnRename, "✎", self.tr.t("tip_rename"))
        self.btnClear  = QtWidgets.QToolButton(); self._as_icon(self.btnClear,  "🧹", self.tr.t("tip_clear"))
        self.btnDelete = QtWidgets.QToolButton(); self._as_icon(self.btnDelete, "✖", self.tr.t("tip_delete"))

        actions = QtWidgets.QHBoxLayout(); actions.setSpacing(8)
        actions.addWidget(self.btnHotkey); actions.addWidget(self.btnRename)
        actions.addWidget(self.btnClear);  actions.addWidget(self.btnDelete)
        layout.addLayout(actions)

        # sombra suave roxa
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QtGui.QColor(139, 92, 246, 60))
        self.card.setGraphicsEffect(shadow)

        self.btnHotkey.clicked.connect(self._on_hotkey)
        self.btnRename.clicked.connect(self._on_rename)
        self.btnClear.clicked.connect(lambda: (self.set_hotkey(""), self.hotkeyChanged.emit("")))
        self.btnDelete.clicked.connect(lambda: self.removeClicked.emit())

        self._retranslate()

    def _as_icon(self, b: QtWidgets.QToolButton, text: str, tip: str):
        b.setCursor(QtCore.Qt.PointingHandCursor)
        b.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        b.setFixedSize(36, 36)
        b.setText(text)
        b.setToolTip(tip)

    def _retranslate(self):
        self.btnPlay.setToolTip(self.tr.t("btn_play"))
        self._refresh_labels()

    def _refresh_labels(self):
        self.lblName.setText(self.display_name)
        f = self.lblName.font()
        if self.hotkey:
            self.lblHotkey.setText(self.hotkey)
            f.setBold(True)
        else:
            self.lblHotkey.setText(self.tr.t("no_hotkey"))
            f.setBold(False)
        self.lblName.setFont(f)

    def _apply_hotkey_style(self): self._refresh_labels()
    def set_hotkey(self, hk: str):
        self.hotkey = (hk or "").strip()
        self._apply_hotkey_style()

    def _on_hotkey(self):
        dlg = HotkeyDialog(self.tr, self.hotkey, self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            new_hk = dlg.result_hotkey()
            self.set_hotkey(new_hk)
            self.hotkeyChanged.emit(new_hk)

    def _on_rename(self):
        text, ok = QtWidgets.QInputDialog.getText(
            self, self.tr.t("rename_title"),
            self.tr.t("rename_prompt"),
            QtWidgets.QLineEdit.Normal, self.display_name
        )
        if ok and text.strip():
            self.display_name = text.strip()
            self._refresh_labels()
            self.renameClicked.emit(self.display_name)


class SoundCardWidget(QtWidgets.QFrame):
    playClicked = QtCore.Signal(str)
    removeClicked = QtCore.Signal()
    renameClicked = QtCore.Signal(str)
    hotkeyChanged = QtCore.Signal(str)

    # tamanho fixo da grade
    CARD_W = 320
    CARD_H = 176

    def __init__(self, tr, path: str, display_name: str, hotkey: str | None, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.path = path
        self.display_name = display_name
        self.hotkey = (hotkey or "").strip()
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("Card")
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFixedSize(self.CARD_W, self.CARD_H)

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        nameRow = QtWidgets.QHBoxLayout()
        self.lblName = ElidedLabel(self.display_name)
        self.lblName.setStyleSheet("background: transparent;")  # <- fundo transparente
        f = self.lblName.font()
        f.setPointSizeF(f.pointSizeF() + 1)
        self.lblName.setFont(f)
        self.lblHotkey = QtWidgets.QLabel()
        self.lblHotkey.setObjectName("Badge")

        nameRow.addWidget(self.lblName, 1)
        nameRow.addWidget(self.lblHotkey, 0, QtCore.Qt.AlignRight)
        v.addLayout(nameRow)

        self.btnPlay = QtWidgets.QPushButton("▶")
        self.btnPlay.setObjectName("BigPlay")
        self.btnPlay.setCursor(QtCore.Qt.PointingHandCursor)
        self.btnPlay.setToolTip(self.tr.t("btn_play"))
        self.btnPlay.clicked.connect(lambda: self.playClicked.emit(self.path))
        v.addWidget(self.btnPlay)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(6)
        self.btnHotkey = QtWidgets.QToolButton(); self._as_icon(self.btnHotkey, "⌨", self.tr.t("tip_hotkey"))
        self.btnRename = QtWidgets.QToolButton(); self._as_icon(self.btnRename, "✎", self.tr.t("tip_rename"))
        self.btnClear  = QtWidgets.QToolButton(); self._as_icon(self.btnClear,  "🧹", self.tr.t("tip_clear"))
        self.btnDelete = QtWidgets.QToolButton(); self._as_icon(self.btnDelete, "✖", self.tr.t("tip_delete"))
        actions.addStretch(1)
        actions.addWidget(self.btnHotkey); actions.addWidget(self.btnRename)
        actions.addWidget(self.btnClear);  actions.addWidget(self.btnDelete)
        actions.addStretch(1)
        v.addLayout(actions)

        self.btnHotkey.clicked.connect(self._on_hotkey)
        self.btnRename.clicked.connect(self._on_rename)
        self.btnClear.clicked.connect(lambda: (self.set_hotkey(""), self.hotkeyChanged.emit("")))
        self.btnDelete.clicked.connect(lambda: self.removeClicked.emit())

        # sombra suave
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 2)
        shadow.setColor(QtGui.QColor(139, 92, 246, 50))
        self.setGraphicsEffect(shadow)

        self._refresh_labels()

    def _as_icon(self, b: QtWidgets.QToolButton, text: str, tip: str):
        b.setCursor(QtCore.Qt.PointingHandCursor)
        b.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly)
        b.setFixedSize(34, 34)
        b.setText(text)
        b.setToolTip(tip)

    def _refresh_labels(self):
        self.lblName.setText(self.display_name)
        f = self.lblName.font()
        if self.hotkey:
            self.lblHotkey.setText(self.hotkey)
            f.setBold(True)
        else:
            self.lblHotkey.setText(self.tr.t("no_hotkey"))
            f.setBold(False)
        self.lblName.setFont(f)

    def set_hotkey(self, hk: str):
        self.hotkey = (hk or "").strip()
        self._refresh_labels()

    def _on_hotkey(self):
        dlg = HotkeyDialog(self.tr, self.hotkey, self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            new_hk = dlg.result_hotkey()
            self.set_hotkey(new_hk)
            self.hotkeyChanged.emit(new_hk)

    def _on_rename(self):
        text, ok = QtWidgets.QInputDialog.getText(
            self, self.tr.t("rename_title"),
            self.tr.t("rename_prompt"),
            QtWidgets.QLineEdit.Normal, self.display_name
        )
        if ok and text.strip():
            self.display_name = text.strip()
            self._refresh_labels()
            self.renameClicked.emit(self.display_name)

class CardsPanel(QtWidgets.QScrollArea):
    """
    Grade responsiva:
      - Cards de tamanho fixo (SoundCardWidget.CARD_W/H)
      - Centralização horizontal (não vertical)
      - Acrescenta colunas conforme a largura disponível cresce
    """
    def __init__(self, tr, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container externo que permite centralizar horizontalmente
        self._outer = QtWidgets.QWidget()
        self._outerLay = QtWidgets.QVBoxLayout(self._outer)
        self._outerLay.setContentsMargins(0, 0, 0, 0)
        self._outerLay.setSpacing(0)

        # Wrap centralizado H
        self._centerWrap = QtWidgets.QWidget()
        self._centerLay = QtWidgets.QHBoxLayout(self._centerWrap)
        self._centerLay.setContentsMargins(8, 8, 8, 8)
        self._centerLay.setSpacing(0)
        self._centerLay.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        # Grid real dos cards
        self._gridContainer = QtWidgets.QWidget()
        self._grid = QtWidgets.QGridLayout(self._gridContainer)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(8)
        self._grid.setVerticalSpacing(8)

        self._centerLay.addWidget(self._gridContainer, 0, QtCore.Qt.AlignTop)
        self._outerLay.addWidget(self._centerWrap, 1, QtCore.Qt.AlignTop)
        self.setWidget(self._outer)

        self._cards: list[SoundCardWidget] = []

    def clear(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        self._cards.clear()

    def set_cards(self, cards: list[SoundCardWidget]):
        # não recria se for a mesma lista por referência
        if cards is not self._cards:
            self.clear()
            self._cards = list(cards)
        self._relayout()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)
        if self._cards:
            self._relayout()

    def _relayout(self):
        # remove do layout sem destruir os widgets
        while self._grid.count():
            self._grid.takeAt(0)

        if not self._cards:
            self._gridContainer.setFixedWidth(0)
            return

        cw = SoundCardWidget.CARD_W
        sp = self._grid.horizontalSpacing()
        avail = max(0, self.viewport().width() - 16)  # margem do centerWrap

        # quantas colunas cabem?
        cols = max(1, int((avail + sp) // (cw + sp)))

        # largura total ocupada pela grade (p/ centralizar)
        total_w = cols * cw + (cols - 1) * sp
        self._gridContainer.setFixedWidth(total_w)

        # posiciona os cards
        for i, card in enumerate(self._cards):
            r = i // cols
            c = i % cols
            self._grid.addWidget(card, r, c, QtCore.Qt.AlignTop)

        # garante que continue alinhado no topo, centralizado apenas no eixo X
        self._centerLay.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
