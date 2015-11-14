import wx.xrc as xrc
import wx.aui as aui
from lib.engage_api import *
from widgets.live import *

if __name__ == '__main__':
    app = wx.App()

    res = xrc.XmlResource('../media/forms.xrc')

    dlg = res.LoadDialog(name='DialogLogin', parent=None)

    def onExit(evt=None):
        dlg.EndModal(wx.ID_CANCEL)
    def onLogin(evt=None):
        dlg.email = xrc.XRCCTRL(dlg, 'inputEmail').GetValue()
        dlg.password = xrc.XRCCTRL(dlg, 'inputPassword').GetValue()
        dlg.EndModal(wx.ID_OK)
    xrc.XRCCTRL(dlg, 'buttonExit').Bind(wx.EVT_BUTTON, onExit)
    xrc.XRCCTRL(dlg, 'buttonLogin').Bind(wx.EVT_BUTTON, onLogin)

    if dlg.ShowModal() == wx.ID_OK:
        link = EngageLink(username=dlg.email, password=dlg.password)
        print link
    # else:
    #     exit(0)

    frame = wx.Frame(None)

    auimgr = aui.AuiManager()
    auimgr.SetManagedWindow(frame)

    gauge = Gauge(0, 5, 0, parent=frame)

    auimgr.AddPane(gauge, aui.AuiPaneInfo().Left())

    auimgr.Update()

    def onIdle(evt):
        reading, age, date = link.getInstant()
        gauge.setValue(reading)
        evt.Skip()

    frame.Bind(wx.EVT_IDLE, onIdle)
    frame.Show()

    app.MainLoop()