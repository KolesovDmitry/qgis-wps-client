# -*- coding: latin1 -*-  
"""
 /***************************************************************************
qgswpstools.py QGIS Web Processing Service Plugin  -------------------------------------------------------------------
 Date                 : 09 November 2009
 Copyright            : (C) 2009 by Dr. Horst Duester
 email                : horst dot duester at kappasys dot ch

 Authors              : Dr. Horst Duester, Soeren Gebbert

  ***************************************************************************
  *                                                                         *
  *   This program is free software; you can redistribute it and/or modify  *
  *   it under the terms of the GNU General Public License as published by  *
  *   the Free Software Foundation; either version 2 of the License, or     *
  *   (at your option) any later version.                                   *
  *                                                                         *
  ***************************************************************************/
"""
# Import the PyQt and the QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from PyQt4 import QtXml
from PyQt4.QtSql import * 
from PyQt4.QtWebKit import QWebView
from qgis.core import *
import os, sys, string, tempfile,  base64

# initialize Qt resources from file resources.py
import resources_rc


# All supported import raster formats
RASTER_MIMETYPES = [{"MIMETYPE":"IMAGE/TIFF", "GDALID":"GTiff"},
                           {"MIMETYPE":"IMAGE/PNG", "GDALID":"PNG"}, \
                           {"MIMETYPE":"IMAGE/GIF", "GDALID":"GIF"}, \
                           {"MIMETYPE":"IMAGE/JPEG", "GDALID":"JPEG"}, \
                           {"MIMETYPE":"IMAGE/GEOTIFF", "GDALID":"GTiff"}, \
                           {"MIMETYPE":"APPLICATION/X-ERDAS-HFA", "GDALID":"HFA"}, \
                           {"MIMETYPE":"APPLICATION/NETCDF", "GDALID":"netCDF"}, \
                           {"MIMETYPE":"APPLICATION/X-NETCDF", "GDALID":"netCDF"}, \
                           {"MIMETYPE":"APPLICATION/GEOTIFF", "GDALID":"GTiff"}, \
                           {"MIMETYPE":"APPLICATION/X-GEOTIFF", "GDALID":"GTiff"}, 
                           {"MIMETYPE":"APPLICATION/X-ESRI-ASCII-GRID", "GDALID":"AAIGrid"}]
# All supported input vector formats [mime type, schema]
VECTOR_MIMETYPES = [{"MIMETYPE":"TEXT/XML", "SCHEMA":"GML", "GDALID":"GML"}, \
                           {"MIMETYPE":"TEXT/XML", "SCHEMA":"GML3", "GDALID":"GML"}, \
                           {"MIMETYPE":"TEXT/XML", "SCHEMA":"KML", "GDALID":"KML"}, \
                           {"MIMETYPE":"APPLICATION/DGN", "SCHEMA":"", "GDALID":"DGN"}, \
                           {"MIMETYPE":"APPLICATION/X-ZIPPED-SHP", "SCHEMA":"", "GDALID":"ESRI_Shapefile"}, \
                           {"MIMETYPE":"APPLICATION/X-OGC-BNA", "SCHEMA":"", "GDALID":"BNA"}]

DEBUG = False


# Our help class for the plugin
class QgsWpsTools(QObject):

  def __init__(self, iface=None,  dlg=None):
    QObject.__init__(self)
    self.iface = iface
    self.doc = QtXml.QDomDocument()
    self.dlg = dlg

  ##############################################################################

  # Gets Server and Connection Info from Stored Server Connections in QGIS Settings
  # Param: String ConnectionName
  # Return: Array Server Information (http,www....,/cgi-bin/...,Post||Get,Service Version)
  def getServer(self,name):
    settings = QSettings()
    mySettings = "/WPS/"+name
    result = {}
    result["scheme"] = settings.value(mySettings+"/scheme").toString()
    result["server"] = settings.value(mySettings+"/server").toString()
    result["port"] =  settings.value(mySettings+"/port")
    result["path"] = settings.value(mySettings+"/path").toString()
    result["method"] = settings.value(mySettings+"/method").toString()
    result["version"] = settings.value(mySettings+"/version").toString()
    return result    

  # Gets Server and Connection Info from Stored Server Connections
  # Param: String ConnectionName
  # Return: Array Server Information (http,www....,/cgi-bin/...,Post||Get,Service Version)
  def getBookmarkXmlUrl(self, name):
    settings = QSettings()
    mySettings = "/WPS-Bookmarks/"+name
    scheme = settings.value(mySettings+"/scheme").toString()
    server = settings.value(mySettings+"/server").toString()
    path = settings.value(mySettings+"/path").toString()
    port =  settings.value(mySettings+"/port")
    identifier = settings.value(mySettings+"/identifier").toString()
    version = settings.value(mySettings+"/version").toString()    

    url = QUrl()        
    myRequest = "?Request=DescribeProcess&identifier="+identifier+"&Service=WPS&Version=1.0.0"
    url.setUrl(scheme+"://"+server+path+myRequest)
    
    try:
        url.setPort(port)
    except:
        pass
        
    return url 

  # Gets Server and Connection Info from Stored Server Connections
  # Param: String ConnectionName
  # Return: Array Server Information (http,www....,/cgi-bin/...,Post||Get,Service Version)
  def getBookmarkXML(self, name):
    settings = QSettings()
    mySettings = "/WPS-Bookmarks/"+name
    scheme = settings.value(mySettings+"/scheme").toString()
    server = settings.value(mySettings+"/server").toString()
    path = settings.value(mySettings+"/path").toString()
    port =  settings.value(mySettings+"/port")
    identifier = settings.value(mySettings+"/identifier").toString()
    version = settings.value(mySettings+"/version").toString()    
    requestFinished = False
    self.theHttp = QgsNetworkAccessManager.instance()     

    try:
      self.theHttp.finished.disconnect()       
    except:
      pass

    url = QUrl()        
    myRequest = "?Request=DescribeProcess&identifier="+identifier+"&Service=WPS&Version="+version
    url.setUrl(scheme+"://"+server+path+myRequest)
    url.setPort(port)
    theReply = self.theHttp.get(QNetworkRequest(url))                        
    self.theHttp.finished.connect(self.serviceRequestFinished)      
      
      
  ##############################################################################

  # Gets Server and Connection Info from Stored Server Connections
  # Param: String ConnectionName
  # Return: Array Server Information (http,www....,/cgi-bin/...,Post||Get,Service Version)
  def getServiceXML(self, name, request, identifier=''):
    result = self.getServer(name)
    path = result["path"]
    server = result["server"]
    method = result["method"]
    version = result["version"]
    scheme = result["scheme"]
    requestFinished = False
    self.theHttp = QgsNetworkAccessManager.instance()     

    try:
      self.theHttp.finished.disconnect()       
    except:
      pass

    if identifier <> '':
      url = QUrl()        
      myRequest = "?Request="+request+"&identifier="+identifier+"&Service=WPS&Version="+version
      url.setUrl(scheme+"://"+server+path+myRequest)
      theReply = self.theHttp.get(QNetworkRequest(url))                        
      self.theHttp.finished.connect(self.serviceRequestFinished)      
    else:
      url = QUrl()        
      myRequest = "?Request="+request+"&Service=WPS&Version="+version
      url.setUrl(scheme+"://"+server+path+myRequest)
      theReply = self.theHttp.get(QNetworkRequest(url))      
      self.theHttp.finished.connect(self.capabilitiesRequestFinished)


  def capabilitiesRequestFinished(self,  reply):
       self.emit(SIGNAL("capabilitiesRequestIsFinished(QNetworkReply)"), reply) 

  def serviceRequestFinished(self,  reply):
       self.emit(SIGNAL("serviceRequestIsFinished(QNetworkReply)"), reply) 

  ##############################################################################

  def parseCapabilitiesXML(self,  xmlString):    
    self.doc.setContent(xmlString,  True)  
    if self.getServiceVersion(self.doc) != "1.0.0":
      QMessageBox.information(None, QApplication.translate("QgsWps","Only WPS Version 1.0.0 is supported"), xmlString)
#      QMessageBox.information(None, QApplication.translate("QgsWps","Error"), QApplication.translate("QgsWps","Only WPS Version 1.0.0 is supprted"))
      return 0

    version    = self.doc.elementsByTagNameNS("http://www.opengis.net/wps/1.0.0","Process")
    title      = self.doc.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Title")    
    identifier = self.doc.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Identifier")
    abstract   = self.doc.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Abstract")

    itemListAll = []

    for i in range(identifier.size()):
      v_element = version.at(i).toElement()
      i_element = identifier.at(i).toElement()
      t_element = title.at(i+1).toElement()
      a_element = abstract.at(i+1).toElement()                       

      itemList = []
      itemList.append(i_element.text()) 
      itemList.append(t_element.text()) 
      if "*"+a_element.text()+"*"== "**":
         itemList.append("*")
      else:
         itemList.append(a_element.text()) 

      itemListAll.append(itemList)

    return itemListAll


  ##############################################################################

  def getServiceVersion(self,  doc):
    root = doc.documentElement()  
    version = root.attribute("version")
    return version

  ##############################################################################

  def getFileReference(self):
    pass

  ##############################################################################

  def getDefaultMimeType(self,  inElement):
    myElement = inElement.elementsByTagName("Default").at(0).toElement()
    return self._getMimeTypeSchemaEncoding(myElement)

  ##############################################################################

  def getSupportedMimeTypes(self,  inElement):
    mimeTypes = []
    myElements = inElement.elementsByTagName("Supported").at(0).toElement()
    myFormats = myElements.elementsByTagName('Format')
    for i in range(myFormats.size()):
      myElement = myFormats.at(i).toElement()
      mimeTypes.append(self._getMimeTypeSchemaEncoding(myElement))
    return mimeTypes

  ##############################################################################

  def _getMimeTypeSchemaEncoding(self,  Element):
    mimeType = ""
    schema = ""
    encoding = ""
    try:
        mimeType = str(Element.elementsByTagName("MimeType").at(0).toElement().text().simplified().toLower())
        schema = str(Element.elementsByTagName("Schema").at(0).toElement().text().simplified().toLower())
        encoding = str(Element.elementsByTagName("Encoding").at(0).toElement().text().simplified().toLower())
    except:
        pass

    return {"MimeType":mimeType,"Schema":schema,"Encoding":encoding}

  ##############################################################################

  def getIdentifierTitleAbstractFromElement(self, element):

      inputIdentifier = element.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Identifier").at(0).toElement().text().simplified()
      title      = element.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Title").at(0).toElement().text().simplified()
      abstract   = element.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Abstract").at(0).toElement().text().simplified()

      return inputIdentifier, title, abstract

  ##############################################################################

  def createTmpBase64(self,  layer):
    try:
        filename = tempfile.mktemp(prefix="base64")         
        rLayer = self.getVLayer(layer)
        infile = open(rLayer.source())
        outfile = open(filename, 'w')
        base64.encode(infile,outfile)
        outfile.close()
        outfile =  open(filename, 'r')
        base64String = outfile.read()
        os.remove(filename)
    except:
        QMessageBox.error(None, QApplication.translate("QgsWps","Error"), QApplication.translate("QgsWps","Unable to create temporal file: ") + filename + QApplication.translate("QgsWps"," for base64 encoding") ) 
    return base64String

  ##############################################################################

  def decodeBase64(self, infileName,  mimeType="image/tiff"):

#   This is till untested
#   TODO: test it
    try:
        # User project dir
        #filename = QFileDialog.getSaveFileName(None, "Chose filename for output file", "/home/soeren");
        filename = tempfile.mktemp(prefix="base64") 
        infile = open(infileName)
        outfile = open(filename, 'w')
        base64.decode(infile,outfile)
        infile.close()
        outfile.close()
    except:
        raise

    return filename

  ##############################################################################

  def createTmpGML(self, layer, processSelection="False"):
    myQTempFile = QTemporaryFile()
    myQTempFile.open()
    tmpFile = unicode(myQTempFile.fileName()+".gml",'latin1')
    myQTempFile.close()

    vLayer = self.getVLayer(layer)    

    if vLayer.dataProvider().name() == "postgres":
      encoding = self.getDBEncoding(vLayer.dataProvider())
    else:
      encoding = vLayer.dataProvider().encoding()

    processSelected = False
    if processSelection and vLayer.selectedFeatureCount() > 0:
      processSelected = True

    dso = QStringList("FORMAT=GML3")
    lco = QStringList()
    error = QgsVectorFileWriter.writeAsVectorFormat(vLayer, tmpFile, encoding, vLayer.dataProvider().crs(), "GML",  processSelected,  "",  dso,  lco)
    if error != QgsVectorFileWriter.NoError:
        QMessageBox.information(None, 'Error',  'Process stopped with errors')
    else:
        myFile = QFile(tmpFile)
        if (not myFile.open(QIODevice.ReadOnly | QIODevice.Text)):
          QMessageBox.information(None, '', QApplication.translate("QgsWps","File open problem"))
          pass    
    
        myGML = QTextStream(myFile)
        myGML.setCodec(encoding)    
        gmlString = ""
    # Overread the first Line of GML Result    
        dummy = myGML.readLine()
        gmlString += myGML.readAll()
        myFile.close()
        myFilePath = QFileInfo(myFile).dir().path()
        myFileInfo = myFilePath+'/'+QFileInfo(myFile).completeBaseName()
        QFile(myFileInfo+'.xsd').remove()
        QFile(myFileInfo+'.gml').remove()
#        QMessageBox.information(None, '', gmlString.simplified())        
    return gmlString.simplified()

  ##############################################################################

  def getVLayer(self,name):
  #   Die sichtbaren Layer der Legende zur weiteren Bearbeitung holen
        # get the map canvas
    mc=self.iface.mapCanvas()

     # how many layers are there?
    nLayers=mc.layerCount()

    for l in range(nLayers):
      layer = mc.layer(l)
      if layer.name() == name:
        return layer  

  ##############################################################################

  def getProviderName(self, name):
    mc=self.iface.mapCanvas()

     # how many layers are there?
    nLayers=mc.layerCount()

    for l in range(nLayers):
      layer = mc.layer(l)
      if layer.name() == name:    
       layerProvider = layer.dataProvider()
       providerName = layerProvider.name()    

    return providerName

  ##############################################################################

  def getTableName(self, name):
    #  Die sichtbaren Layer der Legende zur weiteren Bearbeitung holen
    # get the map canvas
    mc=self.iface.mapCanvas()

     # how many layers are there?
    nLayers=mc.layerCount()

    for l in range(nLayers):
      layer = mc.layer(l)
      if layer.name() == name:
        dataSource = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
        theTableName = dataSource.quotedTablename()
        theTableName.replace('"','')
        return theTableName 

  ##############################################################################

  def getLayerSourceList(self):
    # get the map canvas
    mc=self.iface.mapCanvas()

    # how many layers are there?
    nLayers=mc.layerCount()

    # loopage:
    layerSourceList = []

    for l in range(nLayers):
       layer = mc.layer(l)
       layerSource = unicode(layer.publicSource(),'latin1').lower()
       layerSourceList.append(layerSource)

    return layerSourceList

  ##############################################################################

  def allowedValues(self, aValues):
     valList = []

     # Manage a value list defined by a range
     value_element = aValues.at(0).toElement()
     v_range_element = value_element.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Range")

     if v_range_element.size() > 0:
       min_val = value_element.elementsByTagNameNS("http://www.opengis.net/ows/1.1","MinimumValue").at(0).toElement().text()
       max_val = value_element.elementsByTagNameNS("http://www.opengis.net/ows/1.1","MaximumValue").at(0).toElement().text()
#       QMessageBox.information(None, '', min_val+' - '+max_val)
       for n in range(int(min_val),int(max_val)+1):
           myVal = QString()
           myVal.append(str(n))
           valList.append(myVal)

     # Manage a value list defined by single values
     v_element = value_element.elementsByTagNameNS("http://www.opengis.net/ows/1.1","Value")
     if v_element.size() > 0:
       for n in range(v_element.size()):
         mv_element = v_element.at(n).toElement() 
         valList.append(unicode(mv_element.text(),'latin1').strip())

#     print str(valList)
     return valList        

   ##############################################################################

  # Creates a QgsVectorFileWriter for GML
  # Return: QgsVectorFileWriter
  def createGMLFileWriter(self, myTempFile, fields, geometryType, crs,  encoding):
    writer = QgsVectorFileWriter(myTempFile, encoding, fields, geometryType, crs, "GML")
    if writer.hasError() != QgsVectorFileWriter.NoError:
      message = self.writerErrorMessage(writer.hasError())
      QMessageBox.warning(None, '', message)
      return 0
    return writer

  ##############################################################################

  # Get the List of Fields
  # Return: QGsFieldMap
  def getFieldList(self, vlayer):
    fProvider = vlayer.dataProvider()
    feat = QgsFeature()
    allAttrs = fProvider.attributeIndexes()


    # start data retrieval: all attributes for each feature
    fProvider.select(allAttrs, QgsRectangle(), False)

    # retrieve every feature with its attributes
    myFields = fProvider.fields()

    return myFields

  ##############################################################################

  # Get the Features of a vector Layer
  # Return: QgsFieldMap
  def getFeatureList(self, vlayer):
    provider = vlayer.dataProvider()

    feat = QgsFeature()
    allAttrs = provider.allAttributesList()
    provider.select(allAttrs)

    # retrieve every feature with its attributes
    myFields = provider.fields()

    return myFields

  ##############################################################################

  def uniqueLayerName(self, name):

    mapLayers = QgsMapLayerRegistry.instance().mapLayers()
    i=1
    layerNameList = []    
    for (k, layer) in mapLayers.iteritems():
      layerNameList.append(layer.name())

    layerNameList.sort()

    for layerName in layerNameList:
      if layerName == name+unicode(str(i),'latin1'):    
        i += 1

    newName = name+unicode(str(i),'latin1')
    return newName

  ##############################################################################

  def getLayerNameList(self, dataType=0, all=False):
    myLayerList = []    

    if all:
      mapLayers = QgsMapLayerRegistry.instance().mapLayers()      
      for (k, layer) in mapLayers.iteritems():
        myLayerList.append(layer.name())
    else:
      mc=self.iface.mapCanvas()
      nLayers=mc.layerCount()

      for l in range(nLayers):
        # Nur die Layer des gew�nschten Datentypes ausw�hlen 0=Vectorlayer 1=Rasterlayer
        if mc.layer(l).type() == dataType:
          myLayerList.append(mc.layer(l).name())

    return myLayerList

  ##############################################################################

  def getDBEncoding(self, layerProvider):
    dbConnection = QgsDataSourceURI(layerProvider.dataSourceUri())
    db = QSqlDatabase.addDatabase("QPSQL","WPSClient")    
    db.setHostName(dbConnection.host())
    db.setDatabaseName(dbConnection.database())
    db.setUserName(dbConnection.username())
    db.setPassword(dbConnection.password())
    db.setPort(int(dbConnection.port()))
    db.open()

    query =  "select pg_encoding_to_char(encoding) as encoding "
    query += "from pg_catalog.pg_database "
    query += "where datname = '"+dbConnection.database()+"' "

    result = QSqlQuery(query,db)
    result.first()
    encoding = result.value(0).toString()
    db.close()

    return encoding

  ##############################################################################

  def popUpMessageBox(self, title, detailedText):
    """A message box used for debugging"""
    mbox = WPSMessageBox()
    mbox.setText(title)
    mbox.setDetailedText(detailedText)
    mbox.exec_()
    pass

  ##############################################################################

  def xmlExecuteRequestInputStart(self, identifier):
    string = ""
    string += "<wps:Input>\n"
    string += "<ows:Identifier>"+identifier+"</ows:Identifier>\n"
    string += "<ows:Title>"+identifier+"</ows:Title>\n"
    string += "<wps:Data>\n"
    return string

  ##############################################################################

  def xmlExecuteRequestInputEnd(self):
    string = ""
    string += "</wps:Data>\n"
    string += "</wps:Input>\n"
    return string

  ############################################################################

  def isMimeTypeRaster(self, mimeType):
    """Check for raster input"""
    for rasterType in RASTER_MIMETYPES:
        if mimeType.upper() == rasterType["MIMETYPE"]:
          return rasterType["GDALID"]
    return None

  ############################################################################

  def isMimeTypeVector(self, mimeType):
    """Check for vector input. Zipped shapefiles must be extracted"""
    for vectorType in VECTOR_MIMETYPES:
        if mimeType.upper() == vectorType["MIMETYPE"]:
          return vectorType["GDALID"]
    return None

  ############################################################################

  def isMimeTypeText(self, mimeType):
    """Check for text file input"""
    if mimeType.upper() == "TEXT/PLAIN":
       return "TXT"
    else:
       return None


 ##############################################################################

  def isMimeTypeFile(self, mimeType):
    """Check for file output"""
    for fileType in FILE_MIMETYPES:
        if mimeType.upper() == fileType["MIMETYPE"]:
          return "ZIP"
    return None

##############################################################################

  def addComplexInputComboBox(self, title, name, mimeType, namesList, minOccurs,  dlgProcessScrollAreaWidget,  dlgProcessScrollAreaWidgetLayout):
      """Adds a combobox to select a raster or vector map as input to the process tab"""

      groupbox = QGroupBox(dlgProcessScrollAreaWidget)
      #groupbox.setTitle(name)
      groupbox.setMinimumHeight(25)
      layout = QHBoxLayout()

      # This input is optional
      if minOccurs == 0:
        namesList.append("<None>")

      comboBox = QComboBox(groupbox)
      comboBox.addItems(namesList)
      comboBox.setObjectName(name)
      comboBox.setMinimumWidth(179)
      comboBox.setMaximumWidth(179)
      comboBox.setMinimumHeight(25)

      myLabel = QLabel(dlgProcessScrollAreaWidget)
      myLabel.setObjectName("qLabel"+name)

      if minOccurs > 0:
        string = "[" + name + "] <br>" + title
        myLabel.setText("<font color='Red'>" + string + "</font>" + " <br>(" + mimeType + ")")
      else:
        string = "[" + name + "]\n" + title + " <br>(" + mimeType + ")"
        myLabel.setText(string)

      myLabel.setWordWrap(True)
      myLabel.setMinimumWidth(400)
      myLabel.setMinimumHeight(25)

      layout.addWidget(myLabel)
      layout.addStretch(1)
      layout.addWidget(comboBox)

      groupbox.setLayout(layout)

      dlgProcessScrollAreaWidgetLayout.addWidget(groupbox)

      return comboBox              


  ##############################################################################

  def addComplexOutputComboBox(self, widget, name, title, mimeType,  processIdentifier):
      """Adds a combobox to select a raster or vector map as input to the process tab"""

      groupbox = QGroupBox(widget)
      groupbox.setMinimumHeight(25)
      layout = QHBoxLayout()

      namesList = []
      # Generate a unique name for the layer
      namesList.append(self.uniqueLayerName(processIdentifier + "_" + name + "_"))
      namesList.append("<None>")

      comboBox = QComboBox(groupbox)
      comboBox.setEditable(True)
      comboBox.addItems(namesList)
      comboBox.setObjectName(name)
      comboBox.setMinimumWidth(250)
      comboBox.setMaximumWidth(250)
      comboBox.setMinimumHeight(25)
      comboBox.setEditable(False)

      myLabel = QLabel(widget)
      myLabel.setObjectName("qLabel"+name)

      string = "[" + name + "] <br>" + title
      myLabel.setText("<font color='Green'>" + string + "</font>" + " <br>(" + mimeType + ")")

      myLabel.setWordWrap(True)
      myLabel.setMinimumWidth(400)
      myLabel.setMinimumHeight(25)

      layout.addWidget(myLabel)
      layout.addStretch(1)
      layout.addWidget(comboBox)

      groupbox.setLayout(layout)

      return groupbox, comboBox              

  ##############################################################################

  def addComplexInputListWidget(self, title, name, mimeType, namesList, minOccurs, dlgProcessScrollAreaWidget,  dlgProcessScrollAreaWidgetLayout):
      """Adds a widget for multiple raster or vector selections as inputs to the process tab"""
      groupbox = QGroupBox(dlgProcessScrollAreaWidget)
      #groupbox.setTitle(name)
      groupbox.setMinimumHeight(25)
      layout = QHBoxLayout()

      # This input is optional
      if minOccurs == 0:
        namesList.append("<None>")

      listWidget = QListWidget(groupbox)
      listWidget.addItems(namesList)
      listWidget.setObjectName(name)
      listWidget.setMinimumWidth(179)
      listWidget.setMaximumWidth(179)
      listWidget.setMinimumHeight(120)
      listWidget.setMaximumHeight(120)
      listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

      myLabel = QLabel(self.dlgProcessScrollAreaWidget)
      myLabel.setObjectName("qLabel"+name)

      if minOccurs > 0:
        string = "[" + name + "] <br>" + title
        myLabel.setText("<font color='Red'>" + string + "</font>" + " <br>(" + mimeType + ")")
      else:
        string = "[" + name + "]\n" + title + " <br>(" + mimeType + ")"
        myLabel.setText(string)

      myLabel.setWordWrap(True)
      myLabel.setMinimumWidth(400)
      myLabel.setMinimumHeight(25)

      layout.addWidget(myLabel)
      layout.addStretch(1)
      layout.addWidget(listWidget)

      groupbox.setLayout(layout)

      dlgProcessScrollAreaWidgetLayout.addWidget(groupbox)

      return listWidget

  ##############################################################################

  def addComplexInputTextBox(self, title, name, minOccurs,  dlgProcessScrollAreaWidget, dlgProcessScrollAreaWidgetLayout):
      """Adds a widget to insert text as complex inputs to the process tab"""
      groupbox = QGroupBox(dlgProcessScrollAreaWidget)
      #groupbox.setTitle(name)
      groupbox.setMinimumHeight(50)
      layout = QHBoxLayout()

      textBox = QTextEdit(groupbox)
      textBox.setObjectName(name)
      textBox.setMinimumWidth(200)
      textBox.setMaximumWidth(200)
      textBox.setMinimumHeight(50)

      myLabel = QLabel(dlgProcessScrollAreaWidget)
      myLabel.setObjectName("qLabel"+name)

      if minOccurs > 0:
        string = "[" + name + "] <br>" + title
        myLabel.setText("<font color='Red'>" + string + "</font>")
      else:
        string = "[" + name + "]\n" + title
        myLabel.setText(string)

      myLabel.setWordWrap(True)
      myLabel.setMinimumWidth(400)
      myLabel.setMinimumHeight(25)

      layout.addWidget(myLabel)
      layout.addStretch(1)
      layout.addWidget(textBox)

      groupbox.setLayout(layout)

      dlgProcessScrollAreaWidgetLayout.addWidget(groupbox)

      return textBox

  ##############################################################################

  def addLiteralComboBox(self, title, name, namesList, minOccurs,  dlgProcessScrollAreaWidget,  dlgProcessScrollAreaWidgetLayout):

      groupbox = QGroupBox(dlgProcessScrollAreaWidget)
      #groupbox.setTitle(name)
      groupbox.setMinimumHeight(25)
      layout = QHBoxLayout()

      comboBox = QComboBox(dlgProcessScrollAreaWidget)
      comboBox.addItems(namesList)
      comboBox.setObjectName(name)
      comboBox.setMinimumWidth(179)
      comboBox.setMaximumWidth(179)
      comboBox.setMinimumHeight(25)

      myLabel = QLabel(dlgProcessScrollAreaWidget)
      myLabel.setObjectName("qLabel"+name)

      if minOccurs > 0:
        string = "[" + name + "] <br>" + title
        myLabel.setText("<font color='Red'>" + string + "</font>")
      else:
        string = "[" + name + "]\n" + title
        myLabel.setText(string)

      myLabel.setWordWrap(True)
      myLabel.setMinimumWidth(400)
      myLabel.setMinimumHeight(25)

      layout.addWidget(myLabel)
      layout.addStretch(1)
      layout.addWidget(comboBox)

      groupbox.setLayout(layout)

      dlgProcessScrollAreaWidgetLayout.addWidget(groupbox)

      return comboBox

  ##############################################################################

  def addLiteralLineEdit(self, title, name, minOccurs, dlgProcessScrollAreaWidget,  dlgProcessScrollAreaWidgetLayout,  defaultValue=""):

      groupbox = QGroupBox(dlgProcessScrollAreaWidget)
      #groupbox.setTitle(name)
      groupbox.setMinimumHeight(25)
      layout = QHBoxLayout()

      myLineEdit = QLineEdit(groupbox)
      myLineEdit.setObjectName(name)
      myLineEdit.setMinimumWidth(179)
      myLineEdit.setMaximumWidth(179)
      myLineEdit.setMinimumHeight(25)
      myLineEdit.setText(defaultValue)

      myLabel = QLabel(groupbox)
      myLabel.setObjectName("qLabel"+name)

      if minOccurs > 0:
        string = "[" + name + "] <br>" + title
        myLabel.setText("<font color='Red'>" + string + "</font>")
      else:
        string = "[" + name + "]\n" + title
        myLabel.setText(string)

      myLabel.setWordWrap(True)
      myLabel.setMinimumWidth(400)
      myLabel.setMinimumHeight(25)

      layout.addWidget(myLabel)
      layout.addStretch(1)
      layout.addWidget(myLineEdit)

      groupbox.setLayout(layout)

      dlgProcessScrollAreaWidgetLayout.addWidget(groupbox)

      return myLineEdit


  ##############################################################################

  def addCheckBox(self,  title,  name,  dlgProcessScrollAreaWidget,  dlgProcessScrollAreaWidgetLayout):

      groupbox = QGroupBox(dlgProcessScrollAreaWidget)
      #groupbox.setTitle(name)
      groupbox.setMinimumHeight(25)
      layout = QHBoxLayout()

      myCheckBox = QCheckBox(groupbox)
      myCheckBox.setObjectName("chkBox"+name)
      myCheckBox.setChecked(False)

      myLabel = QLabel(groupbox)
      myLabel.setObjectName("qLabel"+name)  
      myLabel.setText("(" + name + ")" + "\n" + title)
      myLabel.setMinimumWidth(400)
      myLabel.setMinimumHeight(25)
      myLabel.setWordWrap(True)

      layout.addWidget(myLabel)
      layout.addStretch(1)
      layout.addWidget(myCheckBox)

      groupbox.setLayout(layout)

      dlgProcessScrollAreaWidgetLayout.addWidget(groupbox)


  def addDocumentationTab(self, dlgProcessTab,  abstract):
    # Check for URL
    if str(abstract).find("http://") == 0:
      textBox = QWebView(dlgProcessTab)
      textBox.load(QUrl(abstract))
      textBox.show()
    else:
      textBox = QTextBrowser(dlgProcessTab)
      textBox.setText(QString(abstract))

    dlgProcessTab.addTab(textBox, "Documentation")



################################################################################
################################################################################
################################################################################

class WPSMessageBox(QMessageBox):
    """A resizable message box to show debug info"""
    def __init__(self):
        QMessageBox.__init__(self)
        self.setSizeGripEnabled(True)

    def event(self, e):
        result = QMessageBox.event(self, e)

        self.setMinimumHeight(600)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(800)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        textEdit = self.findChild(QTextEdit)
        if textEdit != None :
            textEdit.setMinimumHeight(300)
            textEdit.setMaximumHeight(16777215)
            textEdit.setMinimumWidth(300)
            textEdit.setMaximumWidth(16777215)
            textEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        return result

