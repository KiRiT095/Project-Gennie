"""Minimal two-dot face; expression comes from eye geometry only."""
from __future__ import annotations
import time
from PySide6.QtCore import Qt,QTimer,QRectF
from PySide6.QtGui import QColor,QPainter
from PySide6.QtWidgets import QWidget
class DotFaceWidget(QWidget):
    def __init__(self,size=92,parent=None):
        super().__init__(parent); self.setFixedSize(size,size); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.state="SLEEPING"; self.started=time.monotonic(); self.timer=QTimer(self); self.timer.setInterval(80); self.timer.timeout.connect(self.update); self.timer.start()
    def set_state(self,state):
        if state!=self.state: self.state=state; self.started=time.monotonic(); self.update()
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing,True); t=time.monotonic()-self.started; cx=self.width()/2; cy=self.height()/2; p.setPen(Qt.PenStyle.NoPen)
        if self.state in {"SLEEPING","BOOTING"}:
            p.setBrush(QColor("#b9bbc2")); p.drawEllipse(QRectF(cx-22,cy-2,12,3)); p.drawEllipse(QRectF(cx+10,cy-2,12,3)); p.end(); return
        blink=(t%4.7)<0.12
        if self.state=="THINKING": y=-4; radius=5; offsets=(-5,5)
        elif self.state=="LISTENING": y=0; radius=8; offsets=(-2,2)
        elif self.state=="SPEAKING": y=-1; radius=7+(2 if int(t*8)%2==0 else 0); offsets=(-3,3)
        elif self.state=="EMERGING": y=0; radius=min(8,3+t*5); offsets=(-4,4)
        elif self.state=="RETURNING": y=0; radius=max(1,7-t*5); offsets=(-4,4)
        else: y=0; radius=6; offsets=(-3,3)
        p.setBrush(QColor("#f2f2f2" if self.state!="ERROR" else "#ff7777"))
        for dx in offsets: p.drawEllipse(QRectF(cx+dx*3-3,cy+y-(2 if blink else radius)/2,6,2 if blink else radius))
        p.end()
