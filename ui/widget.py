"""
PyQt6 桌面级悬浮小部件与全量分析网关面板
"""
import sys
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QColor, QFont, QKeyEvent


class FloatingTrackerWidget(QWidget):
    def __init__(self, port: int = 8045):
        super().__init__()
        self.port = port
        self.current_mode = "capsule"  # 'orb' | 'capsule' | 'full'
        self.drag_position = QPoint()
        self.is_resizing = False
        self.resize_edge_margin = 8

        # 统计持久缓存数据
        self.session_count = 0
        self.task_history = []

        self.init_ui()

    def init_ui(self):
        # 无边框 + 始终置顶 + 任务栏图标独立
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)

        # 容器背景卡片
        self.card = QWidget(self)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(12, 10, 12, 10)
        self.main_layout.addWidget(self.card)

        self.apply_theme_style()
        self.build_capsule_view()
        self.resize(380, 58)

    def apply_theme_style(self):
        # 纯黑夜高对比度样式 (标题纯白 text-white, 参数亮白 text-zinc-200, 型号白灰 text-zinc-300)
        self.card.setStyleSheet("""
            QWidget {
                background-color: #12151d;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                color: #e4e4e7;
            }
        """)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def build_capsule_view(self):
        self.clear_layout(self.card_layout)
        row = QHBoxLayout()
        row.setSpacing(8)

        # 状态指示呼吸灯
        indicator = QLabel()
        indicator.setFixedSize(8, 8)
        indicator.setStyleSheet("background-color: #10b981; border-radius: 4px;")
        row.addWidget(indicator)

        # 标题 (高亮纯白 text-white font-bold)
        self.lbl_title = QLabel("等待首个 IDE 请求...")
        self.lbl_title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px;")
        row.addWidget(self.lbl_title, 1)

        # 模式切换按钮
        btn_expand = QPushButton("展开")
        btn_expand.setStyleSheet("""
            QPushButton {
                background-color: #1f2430;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #272f40; }
        """)
        btn_expand.clicked.connect(self.switch_to_full)
        row.addWidget(btn_expand)

        self.card_layout.addLayout(row)

    def build_full_view(self):
        self.clear_layout(self.card_layout)

        # 顶部工具栏
        top_bar = QHBoxLayout()
        title_label = QLabel("网关监控分析中心")
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        btn_collapse = QPushButton("收起")
        btn_collapse.setStyleSheet("background-color: #1f2430; color: #94a3b8; border-radius: 4px; padding: 2px 8px;")
        btn_collapse.clicked.connect(self.switch_to_capsule)
        top_bar.addWidget(btn_collapse)

        self.card_layout.addLayout(top_bar)

        # 数据表格
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["#", "服务商", "模型", "总消耗", "TTFT", "命中率", "指令标题"])
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # 键盘方向键/WASD 响应属性
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 表格高对比暗黑样式
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #161922;
                border: 1px solid #27272a;
                border-radius: 8px;
                color: #e4e4e7;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1a1e28;
                color: #f4f4f5;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #27272a;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #202430;
            }
            QTableWidget::item:selected {
                background-color: #232938;
            }
        """)
        self.card_layout.addWidget(self.table)

        # 底部状态栏
        bottom_bar = QHBoxLayout()
        hint = QLabel(f"监听端口: 127.0.0.1:{self.port} | 支持 W/A/S/D 或 ↑↓←→ 平滑滚动")
        hint.setStyleSheet("color: #71717a; font-size: 11px;")
        bottom_bar.addWidget(hint)
        self.card_layout.addLayout(bottom_bar)

        # 刷新历史数据
        self.reload_table_data()

    def switch_to_full(self):
        self.current_mode = "full"
        self.build_full_view()
        self.resize(760, 420)

    def switch_to_capsule(self):
        self.current_mode = "capsule"
        self.build_capsule_view()
        self.resize(380, 58)

    def update_record(self, data: dict):
        self.session_count += 1
        data["num"] = self.session_count
        self.task_history.insert(0, data)

        # 更新胶囊标题
        if hasattr(self, 'lbl_title'):
            self.lbl_title.setText(f"#{data['num']} {data['title']}")

        if self.current_mode == "full" and hasattr(self, 'table'):
            self.reload_table_data()

    def reload_table_data(self):
        self.table.setRowCount(len(self.task_history))
        for row, item in enumerate(self.task_history):
            # 1. 编号 (浅亮灰)
            item_num = QTableWidgetItem(f"#{item.get('num')}")
            item_num.setForeground(QColor("#d4d4d8"))
            self.table.setItem(row, 0, item_num)

            # 2. 服务商
            self.table.setItem(row, 1, QTableWidgetItem("OpenAI"))

            # 3. 模型 (白偏灰 text-zinc-300)
            item_model = QTableWidgetItem(str(item.get("model")))
            item_model.setForeground(QColor("#d4d4d8"))
            self.table.setItem(row, 2, item_model)

            # 4. 总消耗 (金黄色)
            cost = item.get("cost_cny", 0.0)
            item_cost = QTableWidgetItem(f"¥{cost:.3f}")
            item_cost.setForeground(QColor("#fbbf24"))
            self.table.setItem(row, 3, item_cost)

            # 5. TTFT (浅白 text-zinc-200)
            ttft = item.get("ttft_ms", 0)
            item_ttft = QTableWidgetItem(f"{ttft}ms" if ttft else "-")
            item_ttft.setForeground(QColor("#e4e4e7"))
            self.table.setItem(row, 4, item_ttft)

            # 6. 缓存命中率 (翠绿)
            hit_rate = item.get("hit_rate", "0%")
            item_hit = QTableWidgetItem(hit_rate)
            item_hit.setForeground(QColor("#34d399"))
            self.table.setItem(row, 5, item_hit)

            # 7. 任务指令标题 (高亮纯白 text-white)
            item_title = QTableWidgetItem(str(item.get("title")))
            item_title.setForeground(QColor("#ffffff"))
            font = item_title.font()
            font.setBold(True)
            item_title.setFont(font)
            self.table.setItem(row, 6, item_title)

    # 键盘 WASD / 方向键滑动控制
    def keyPressEvent(self, event: QKeyEvent):
        if self.current_mode == "full" and hasattr(self, 'table'):
            key = event.key()
            v_bar = self.table.verticalScrollBar()
            h_bar = self.table.horizontalScrollBar()

            if key in (Qt.Key.Key_W, Qt.Key.Key_Up):
                v_bar.setValue(v_bar.value() - 36)
                event.accept()
                return
            elif key in (Qt.Key.Key_S, Qt.Key.Key_Down):
                v_bar.setValue(v_bar.value() + 36)
                event.accept()
                return
            elif key in (Qt.Key.Key_A, Qt.Key.Key_Left):
                h_bar.setValue(h_bar.value() - 50)
                event.accept()
                return
            elif key in (Qt.Key.Key_D, Qt.Key.Key_Right):
                h_bar.setValue(h_bar.value() + 50)
                event.accept()
                return
        super().keyPressEvent(event)

    # 鼠标拖动与平滑无边框拉伸
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
