import wx

class Gauge(wx.PyControl):
    def __init__(self, min, max, value, *args, **kwargs):
        wx.PyControl.__init__(self, *args, **kwargs)
        self.min = min
        self.max = max
        self.value = value
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_SIZE, self.onSize)
        # self.SetBackgroundColour('#000000')
        self.Refresh()

    def setValue(self, value):
        self.value = value
        self.Refresh()

    def onSize(self, evt):
        self.Refresh()
        evt.Skip()

    def onPaint(self, evt):
        rect = self.GetRect()
        portion = float(self.value - self.min) / float(self.max - self.min)
        rect = (rect[0], rect[3] * (1-portion), rect[2], rect[3] * portion)

        dc = wx.BufferedPaintDC(self)

        color = (255 * (portion), 255 * (1-portion), 0)
        color2 = (128 * (portion), 128 * (1-portion), 0)
        dc.Clear()
        dc.BeginDrawing()
        dc.GradientFillLinear(rect, color, color2, wx.NORTH)
        dc.EndDrawing()