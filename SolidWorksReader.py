# Copyright (c) 2017 Thomas Karl Pietrowski

# TODOs:
# * Adding selection to separately import parts from an assembly

# Buildins
import math

# Uranium/Cura
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("CuraSolidWorksIntegrationPlugin")
from UM.Message import Message
from UM.Logger import Logger
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion

# Our plugin
from .CommonComReader import CommonCOMReader
from .SolidWorksConstants import SolidWorksEnums

class SolidWorksReader(CommonCOMReader):
    def __init__(self):
        self._extension_part = ".SLDPRT"
        self._extension_assembly = ".SLDASM"
        self._supported_extensions = [self._extension_part.lower(),
                                      self._extension_assembly.lower(),
                                      ]

        super(SolidWorksReader, self).__init__("SldWorks.Application", "SolidWorks")
        
        self._convertAssemblyIntoOnce = True # False is not implemented now!
        
        self._revision = None
        self._revision_major = None
        self._revision_minor = None
        self._revision_patch = None

    def setAppVisible(self, state, **options):
        options["app_instance"].Visible = state
    
    def getAppVisible(self, state, **options):
        return options["app_instance"].Visible
    
    def startApp(self, visible=False):
        app_instance = CommonCOMReader.startApp(self, visible=visible)
        
        # Getting revision after starting
        Logger.log("d", "SolidWorks RevisionNumber: " + app_instance.RevisionNumber)
        self._revision = [int(x) for x in app_instance.RevisionNumber.split(".")]
        self._revision_major = self._revision[0]
        self._revision_minor = self._revision[1]
        self._revision_patch = self._revision[2]
        
        # Re-generate a list of preferred file formats
        self.updateFormatsFirstChoise()
        
        return app_instance
    
    def updateFormatsFirstChoise(self):
        self._fileFormatsFirstChoise = ["stl"]
        if self._revision_major >= 25 and "3mf" in self._readerForFileformat.keys():
            self._fileFormatsFirstChoise.insert(0, "3mf")

        return self._fileFormatsFirstChoise
    
    def checkApp(self, **options):
        functionsToBeChecked = ("OpenDoc", "CloseDoc")
        for function in functionsToBeChecked:
            try:
                getattr(options["app_instance"], function)
            except:
                Logger.logException("e", "Error which occured when checking for a valid app instance")
                return False
        return True

    def closeApp(self, **options):
        if "app_instance" in options.keys():
            del(options["app_instance"])

    def walkComponentsInAssembly(self, root = None):
        if root == None:
            root = self.rootComponent
        
        children = root.GetChildren
        
        if children:
            children = [self.walkComponentsInAssembly(child) for child in children]
            return (root, children)
        else:
            return root
        
        """
        models = options["sw_model"].GetComponents(True)
        
        for model in models:
            #Logger.log("d", model.GetModelDoc2())
            #Logger.log("d", repr(model.GetTitle))
            Logger.log("d", repr(model.GetPathName))
            #Logger.log("d", repr(model.GetType))
            if model.GetPathName in ComponentsCount.keys():
                ComponentsCount[model.GetPathName] = ComponentsCount[model.GetPathName] + 1
            else:
                ComponentsCount[model.GetPathName] = 1

        for key in ComponentsCount.keys():
            Logger.log("d", "Found %s %s-times in the assembly!" %(key, ComponentsCount[key]))
        """

    def openForeignFile(self, **options):
        if options["foreignFormat"].upper() == self._extension_part:
            filetype = SolidWorksEnums.FileTypes.SWpart
        elif options["foreignFormat"].upper() == self._extension_assembly:
            filetype = SolidWorksEnums.FileTypes.SWassembly
        else:
            raise NotImplementedError("Unknown extension. Something went terribly wrong!")

        #options["sw_model"] = options["app_instance"].OpenDoc(options["foreignFile"], filetype)
        documentSpecification = options["app_instance"].GetOpenDocSpec(options["foreignFile"])
        
        ## NOTE: SPEC: FileName
        #documentSpecification.FileName
        
        ## NOTE: SPEC: DocumentType
        ## TODO: Really needed here?!
        documentSpecification.DocumentType = filetype
        
        ## TODO: Test the impact of LightWeight = True
        #documentSpecification.LightWeight = True
        documentSpecification.Silent = True
        
        ## TODO: Double check, whether file was really opened read-only..
        documentSpecification.ReadOnly = True
        
        options["sw_model"] = options["app_instance"].OpenDoc7(documentSpecification)
        
        if documentSpecification.Warning:
            Logger.log("w", "Warnings happened while opening your SolidWorks file!")
        if documentSpecification.Error:
            Logger.log("e", "Errors happened while opening your SolidWorks file!")
            error_message = Message(i18n_catalog.i18nc("@info:status", "Errors appeared while opening your SolidWorks file! \
            Please check, whether it is possible to open your file in SolidWorks itself without any problems as well!" %(self._app_friendlyName)))
            error_message.show()
        
        # Might be useful in the future, but no need for this ATM
        #self.configuration = self.model.getActiveConfiguration
        #self.rootComponent = self.configuration.GetRootComponent

        ## EXPERIMENTAL: Browse single parts in assembly
        #if filetype == SolidWorksEnums.FileTypes.SWassembly:
        #    Logger.log("d", 'walkComponentsInAssembly: ' + repr(self.walkComponentsInAssembly()))
        
        return options

    def exportFileAs(self, **options):
        if options["tempType"] == "stl":
            if options["foreignFormat"].upper() == self._extension_assembly:
                # Backing up current setting of swSTLComponentsIntoOneFile
                swSTLComponentsIntoOneFileBackup = options["app_instance"].GetUserPreferenceToggle(SolidWorksEnums.UserPreferences.swSTLComponentsIntoOneFile)
                options["app_instance"].SetUserPreferenceToggle(SolidWorksEnums.UserPreferences.swSTLComponentsIntoOneFile, self._convertAssemblyIntoOnce)

            swExportSTLQualityBackup = options["app_instance"].GetUserPreferenceIntegerValue(SolidWorksEnums.swUserPreferenceIntegerValue_e.swExportSTLQuality)
            options["app_instance"].SetUserPreferenceIntegerValue(SolidWorksEnums.swUserPreferenceIntegerValue_e.swExportSTLQuality, SolidWorksEnums.swSTLQuality_e.swSTLQuality_Fine)
            
            # Changing the default unit for STLs to mm, which is expected by Cura
            swExportStlUnitsBackup = options["app_instance"].GetUserPreferenceIntegerValue(SolidWorksEnums.swUserPreferenceIntegerValue_e.swExportStlUnits)
            options["app_instance"].SetUserPreferenceIntegerValue(SolidWorksEnums.swUserPreferenceIntegerValue_e.swExportStlUnits, SolidWorksEnums.swLengthUnit_e.swMM)
            
            # Changing the output type temporary to binary
            swSTLBinaryFormatBackup = options["app_instance"].GetUserPreferenceToggle(SolidWorksEnums.swUserPreferenceToggle_e.swSTLBinaryFormat)
            options["app_instance"].SetUserPreferenceToggle(SolidWorksEnums.swUserPreferenceToggle_e.swSTLBinaryFormat, True)
        
        options["sw_model"].SaveAs(options["tempFile"])
        
        if options["tempType"] == "stl":
            # Restoring swSTLBinaryFormat
            options["app_instance"].SetUserPreferenceToggle(SolidWorksEnums.swUserPreferenceToggle_e.swSTLBinaryFormat, swSTLBinaryFormatBackup)
            
            # Restoring swExportStlUnits
            options["app_instance"].SetUserPreferenceIntegerValue(SolidWorksEnums.swUserPreferenceIntegerValue_e.swExportStlUnits, swExportStlUnitsBackup)
            
            # Restoring swSTLQuality_Fine
            options["app_instance"].SetUserPreferenceIntegerValue(SolidWorksEnums.swUserPreferenceIntegerValue_e.swExportSTLQuality, swExportSTLQualityBackup)
            
            if options["foreignFormat"].upper() == self._extension_assembly:
                # Restoring swSTLComponentsIntoOneFile
                options["app_instance"].SetUserPreferenceToggle(SolidWorksEnums.UserPreferences.swSTLComponentsIntoOneFile, swSTLComponentsIntoOneFileBackup)
    
    def closeForeignFile(self, **options):
        options["app_instance"].CloseDoc(options["foreignFile"])
    
    def areReadersAvailable(self):
        return bool(self._readerForFileformat)

    def nodePostProcessing(self, node):
        if self._revision_major == 24: # Known problem under SolidWorks 2016: Exported models are rotated by -90 degrees. This rotates it back!
            rotation = Quaternion.fromAngleAxis(math.radians(90), Vector.Unit_X)
            node.rotate(rotation)
        return node

    ## Decide if we need to use ascii or binary in order to read file
