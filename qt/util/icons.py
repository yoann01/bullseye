from PySide import QtGui, QtCore
from PySide.QtCore import Qt

class IconManager:
	def __init__(self):
		self.cache = {}
		
	def pixmapFromText(self, text, size, background_color='#456eac',border_color='#000', text_color='#fff'):
		
		height, width = size
		key = '%s - %sx%s - %s' % (text, height, width, background_color)
		
		if self.cache.has_key(key):
			return self.cache[key]
			
		dragImageSize = QtCore.QSize(height, width);
		dragImage = QtGui.QImage(dragImageSize, QtGui.QImage.Format_ARGB32_Premultiplied)
		dragPainter = QtGui.QPainter(dragImage)
		dragPainter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
		dragPainter.fillRect(dragImage.rect(), QtGui.QColor(background_color));
		dragPainter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver);
		#icon = QtGui.QPixmap('icons/circle_blue.png')
		#dragPainter.drawPixmap(0, 0, 48, 48, icon);
		font = dragPainter.font()
		font.setPointSize(28 - width)
		#font.setWeight(QtGui.QFont.Bold);
		dragPainter.setPen(QtGui.QColor(text_color))
		dragPainter.setFont(font)

		dragPainter.drawText(QtCore.QRect(width / 6, 0, width, height), text)
		dragPainter.end()
		
		pixmap = QtGui.QPixmap.fromImage(dragImage)
		self.cache[key] = pixmap
		
		return pixmap
		
MANAGER = IconManager()
pixmapFromText = MANAGER.pixmapFromText