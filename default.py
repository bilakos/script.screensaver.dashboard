import sys
import xbmcaddon
import xbmcgui
import xbmc
import time
import httplib 
import re
import threading

Addon = xbmcaddon.Addon('script.screensaver.dashboard')

__settings__ = xbmcaddon.Addon(id='script.screensaver.dashboard')
__scriptname__ = Addon.getAddonInfo('name')
__path__ = Addon.getAddonInfo('path')


class ExitMonitor(xbmc.Monitor):
	ScreenSaverActive = True
	def __init__(self, exit_callback):
		self.exit_callback = exit_callback

	def onScreensaverDeactivated(self):
		self.exit_callback()
	
class Screensaver(xbmcgui.WindowXMLDialog):
        
    def onInit(self):
        self.Monitor = ExitMonitor(self.exit)
	if(self.Monitor.ScreenSaverActive):
		self.getStocks()
		self.getRssNews()

    def exit(self):
        self.Monitor.ScreenSaverActive = False
        self.close()
        

    def getStocks(self):
	conn = httplib.HTTPConnection("query.yahooapis.com")
	try:
		quotesymbol = __settings__.getSetting('quotesymbol')
		conn.request("GET", "/v1/public/yql?q=select%20*%20from%20yahoo.finance.quotes%20where%20symbol%20in%20(%22" + quotesymbol + "%22)&env=store://datatables.org/alltableswithkeys")
		r1 = conn.getresponse()	
		data1 = r1.read()
		conn.close()
	except ValueError:
		print 'Could not retrieve stock quotes'
	try:
		import xml.etree.ElementTree as ET
		root = ET.fromstring(str(data1))
		LastTradePriceOnly = root[0][0][41].text # LastTradePriceOnly
		ChangeinPercent = root[0][0][57].text # ChangeinPercent
		ChangeinPercentColor = '0xFF00FF00'
		if '-' in str(ChangeinPercent):
			ChangeinPercentColor = '0xFFFF0000'
		self.CtrlLastTradePriceOnly=xbmcgui.ControlLabel(85, 590, 100, 100, LastTradePriceOnly,'font28_title')
		self.addControl(self.CtrlLastTradePriceOnly)
		self.CtrlChangeinPercent=xbmcgui.ControlLabel(85, 630, 100, 100, ChangeinPercent,'font14',ChangeinPercentColor)
		self.addControl(self.CtrlChangeinPercent)
		if 'true' in __settings__.getSetting('ownquotelabel'):
			self.getControl(99).setLabel(__settings__.getSetting('quotelabel'))
		else:
			self.getControl(99).setLabel(root[0][0][67].text)
	except ValueError:
		print 'Could not parse stock quotes'
		
    def getRssNews(self):
    	rssuri = __settings__.getSetting('rssuri')
    	try:
  		regex = re.compile("^(.*?)/(.*)")
		r = regex.search(rssuri)
		conn = httplib.HTTPConnection(str(r.group(1)))
		conn.request("GET", "/" + str(r.group(2)))
		r1 = conn.getresponse()	
		data1 = r1.read()
    	except ValueError:
    		print 'Could not parse URI or Server not available. Please use the following format: www.n-tv.de/rss'
	
	try:
		import xml.etree.ElementTree as ET
		NewsXML = ET.fromstring(str(data1))
		t = threading.Thread(target=self.PostRssNews,args=(NewsXML,))
		t.daemon = True
		t.start()
	except ValueError:
		print 'Could not write News to Screensaver'

    def PostRssNews(self,NewsXML):
	x = 0
	items = NewsXML.findall("channel/item")
	try:
		rsslogo = ElementWrapper(NewsXML.find("channel/image")).gettext('url')
	except ValueError:
		print 'Could not get RSS News image'
		rsslogo = 'rsslogo.jpg'
	self.getControl(98).setImage(rsslogo)
	while(x < 5 | self.Monitor.ScreenSaverActive):
		item = ElementWrapper(items[x])
		# Extract Image URL
		try:
			regex = re.compile("img src=\"(.*?)\"")
			r = regex.search(item.gettext('{http://purl.org/rss/1.0/modules/content/}encoded'))
			img = r.group(1)
			self.getControl(100).setImage(img)
		except ValueError:
    			print 'Could not parse NewsImage of RSS News'
		self.getControl(101).setLabel(item.gettext('title'))
		self.getControl(102).setText(item.gettext('description'))
		x = x + 1
		xbmc.sleep(int(__settings__.getSetting('feedloop')))
	if(self.Monitor.ScreenSaverActive):
		self.getRssNews()

class ElementWrapper:
    def __init__(self, element,):
        self._element = element
    def gettext(self, tag):
        if tag.startswith("__"):
            raise AttributeError(tag)
        return self._element.findtext(tag)

if __name__ == '__main__':
    screensaver_gui = Screensaver('script-%s-main.xml' % __scriptname__, __path__, 'default',)
    screensaver_gui.doModal()
    del screensaver_gui
    sys.modules.clear()