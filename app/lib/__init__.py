"""
	Application Handler
	author: Trishkin Sergey

"""

import warnings
import json

from os       import path as osPath
from datetime import datetime
from sys      import path as sysPath
from sys      import path as sysPath

sysPath.append(osPath.dirname(__file__))
from redisGateway import RedisGateway


def getJsonContentFromFile(path):
	with open(path, 'r') as file:
		content = json.load(file)

	return content


class InnerApplicationError(Exception):
	pass


class InnerApplicationWarring(Warning):
	pass


class CoreError:
	"""
	Core Error event

	Attributes:
		title (string)- title of Error
		message (string) - explanation of the Error

	"""

	def __init__(self, title, message):
		self.title   = title
		self.message = message

	def __call__(self):
		raise InnerApplicationError(self.title, self.message)


class CoreWarning:
	"""
	Core Warning event

	Attributes:
		title (string)- title of warning
		message (string) - explanation of the warning

	"""

	def __init__(self, title, message):
		self.title   = title
		self.message = message

	def __call__(self):
		msg = "\n\tTitle:\t\t{0}\n\tDescription:\t{1}".format(self.title, self.message)

		warnings.warn(msg, InnerApplicationWarring)

		return msg


class CoreInfo:
	"""
	Core Info event

	Attributes:
		title (string)- title of Info
		message (string) - explanation of the Info

	"""

	def __init__(self, title, message):
		self.title   = title
		self.message = message

	def __call__(self):
		msg = """
		\nInformation:
			\n\tTitle: \t\t{0}
			\n\tDescription: \t{1}
		""".format(self.title, self.message)

		print(msg)

		return msg


class HandlerNodeTypes(object):

	def __init__(self):
		pass

	def getDescription(self, data):
		return {
			"tag": "td",
			"innerText": data,
			"property": {"class": "EventDescription"}
		}

	def getEventType(self, eventType):
		return {
			"tag": "td",
			"innerText": eventType,
			"property": {"class": "EventType"}
		}

	def getTitle(self, title, eventType):
		return {
			"tag": "td",
			"innerText": title,
			"property": {
				"class": "EventTitle",
				"title": eventType
			}
		}

	def getTime(self):
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		return {
			"tag": "td",
			"innerText": timestamp,
			"property": {
				"class": "EventTime"
			}
		}

	def getInfoRow(self, event, title, description):
		return {
			"tag": "tr",
			"property": {"class": event},

			"items": [
				self.getTitle(title, event),
				self.getDescription(description),
				self.getTime(),
				self.getEventType(event)
			]
		}


class CoreHandler(HandlerNodeTypes):
	footerTags = [
		"</html>",
		"</body>",
		"</table>",
		"</tbody>",
	]

	events = [{
		"type": "Error",
		"_class": CoreError,
	}, {
		"type": "Warning",
		"_class": CoreWarning
	}, {
		"type": "Info",
		"_class": CoreInfo
	}]

	logPath  = None

	def __init__(self, logParamsPath, logPath=False):
		self.handled = []
		self.baseDir = osPath.dirname(__file__)
		self.logPath = logPath

		if logParamsPath:
			self._initLog(logParamsPath)

	def _initLog(self, logParamsPath):
		if osPath.exists(logParamsPath):
			self.log      = HTMLJsonGateway()
			logParams     = self.log.getJsonContentFromFile(logParamsPath)
			self.logPath  = self.logPath if self.logPath else osPath.join(self.baseDir, *osPath.split(logParams["path"]))

			self._generateLogFile(logParams)

	def _generateLogFile(self, logParams):
		if not osPath.exists(self.logPath):
			content = self.log.createElement(logParams["page"])

			with open(self.logPath, 'a+') as file:
				file.write(content)

	def handle(self, title, message, eventType=0):
		"""
		handle Event

		Parameters:
			title (string) - core event title
			message (string) - explanation of the event
			eventType (int=0) - index of event in self.events

		"""

		eventItem = self.events[eventType]
		event     = eventItem["_class"](title, message)

		self.handled.append(event)

		if self.logPath:
			self._appendNodeOnLogTable(eventItem["type"], event.title, event.message)

		event()

	def _FooterModify(self, content, mode='clear'):
		for tag in self.footerTags:

			if mode == 'clear':
				content = content.replace(tag, "")

			else:
				content += tag

		return content

	def _appendNodeOnLogTable(self, event, title, description):
		el      = self.getInfoRow(event, title, description)
		content = self.log.createElement(el)

		with open(self.logPath, 'r+') as file:
			doc = self._FooterModify(file.read(), 'clear') + content

		with open(self.logPath, 'w') as file: file.write("%s%s" % (doc,  self._FooterModify("", "")))

	def __call__(self, title, message, eventType=0):
		self.handle(title, message, eventType)


class listConverter(object):

	def __init__(self):
		pass

	def listToStr(self, _list, separator="\n"):
		curstr = ""

		if isinstance(_list, str):
			curstr = _list

		else:
			for n in _list:
				curstr += n + separator if _list.index(n) != len(_list) else ""

		return curstr


class HTMLJsonGateway(listConverter):

	def __init__(self):
		pass

	def generatProperty(self, propertyJson):
		propsStr = ""

		for k, v in propertyJson.items():
			propsStr += ' {0}="{1}"'.format(k, v)

		return propsStr

	def getJsonContentFromFile(self, path):
		return getJsonContentFromFile(path)

	def createElement(self, params):
		tag    = params["tag"]
		props  = self.generatProperty(params["property"]) if "property"  in params.keys() else ""
		text   = self.listToStr(params["innerText"])      if "innerText" in params.keys() else ""
		items  = params["items"]                          if "items"     in params.keys() else ""
		parsed = "\n<{0}{1}>\n\t{2}".format(tag, props, text)

		if (items):
			for item in items:
				parsed += self.createElement(item)

		return parsed + "\n</{0}>".format(tag)