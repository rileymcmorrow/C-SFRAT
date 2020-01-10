#-----------------------------------------------------------------------------------#
# TODO:
# how will table data be entered?
#   ignore first line? only parse floats?
# make sure everything that needs to be is a np array, not list
# select hazard function
# MSE vs SSE?
# checking on other datasets
# using only a subset of metrics
# making UI easier to use for someone who doesn't understand the math
# status bar?
# options selected from menubar like in SFRAT
# protection levels
# graph should always be on same side (right)?
# setting status tips
# dialog asking if you want to quit?
# pay attention to how scaling/strecting works, minimum sizes for UI elements
# naming conventions for excel/csv
# less classes?
#   example: self._main.tabs.tab1.sideMenu.sheetSelect.addItems(self.data.sheetNames)
# figure out access modifiers, public/private variables, properties
# use logging object, removes matplotlib debug messages in debug mode
# changing sheets during calculations?
#   think the solution is to load the data once, and then continue using that same data
#   until calculations are completed
# change column header names if they don't have any
# numCovariates - property?
# do Model abstract peroperties do anything?
# figure out "if self.data.getData() is not None"
#   just need self.dataLoaded?
# more descriptions of what's happening as estimations are running (ComputeWidget)
# predict points? (commonWidgets)
# naming "hazard functions" instead of models
# fsolve doesn't return if converged, so it's not updated for models
#   should try other scipy functions
# make tab 2 like tab 1
#   side menu with plot/table on right
#   definitely need a side menu to select the hazard functions
# names of tabs in tab 2?
# self.viewType is never updated, we don't use updateUI()
# sometimes metric list doesn't load until interacted with
#------------------------------------------------------------------------------------#

# PyQt5 imports for UI elements
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QWidget, QTabWidget, \
                            QHBoxLayout, QVBoxLayout, QTableView, QLabel, \
                            QLineEdit, QGroupBox, QComboBox, QListWidget, \
                            QPushButton, QAction, QActionGroup, QAbstractItemView, \
                            QFileDialog, QCheckBox, QScrollArea, QGridLayout, \
                            QTableWidget, QTableWidgetItem, QAbstractScrollArea
from PyQt5.QtCore import pyqtSignal

# Matplotlib imports for graphs/plots
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# For handling debug output
import logging

# Local imports
from ui.commonWidgets import PlotWidget, PlotAndTable, ComputeWidget, TaskThread
from core.dataClass import Data
from core.graphSettings import PlotSettings
import models


class MainWindow(QMainWindow):
    # signals
    importFileSignal = pyqtSignal()

    # debug mode?
    def __init__(self, debug=False):
        """
        description to be created at a later time
        """
        super().__init__()

        # setup main window parameters
        self.title = "Covariate Tool"
        self.left = 100
        self.top = 100
        self.width = 1080
        self.height = 720
        self.minWidth = 800
        self.minHeight = 600
        self._main = MainWidget()
        self.setCentralWidget(self._main)

        # set debug mode?
        self.debug = debug

        # set data
        self.data = Data()
        self.plotSettings = PlotSettings()
        self.selectedModelNames = []

        # self.estimationResults
        # self.currentModel

        # flags
        self.dataLoaded = False
        self.estimationComplete = False

        # tab 1 plot and table
        self.ax = self._main.tabs.tab1.plotAndTable.figure.add_subplot(111)
        # tab 2 plot and table
        self.ax2 = self._main.tabs.tab2.plot.figure.add_subplot(111)

        # signal connections
        self.importFileSignal.connect(self.importFile)
        self._main.tabs.tab1.sideMenu.viewChangedSignal.connect(self.setDataView)
        self._main.tabs.tab1.sideMenu.runModelSignal.connect(self.runModels)    # run models when signal is received
        # self._main.tabs.tab1.sideMenu.runModelSignal.connect(self._main.tabs.tab2.sideMenu.addSelectedModels)    # fill tab 2 models group with selected models
        self._main.tabs.tab2.sideMenu.modelChangedSignal.connect(self.changePlot2)
        # connect tab2 list changed to refreshing tab 2 plot

        self.initUI()
        logging.info("UI loaded.")

    def closeEvent(self, event):
        """
        description to be created at a later time
        """
        logging.info("Covariate Tool application closed.")
        qApp.quit()

    def initUI(self):
        """
        description to be created at a later time
        """
        self.setupMenu()
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setMinimumSize(self.minWidth, self.minHeight)
        self.statusBar().showMessage("")
        self.viewType = "view"
        self.dataViewIndex = 0
        self.show()

    def runModels(self, modelDetails):
        """
        Run selected models using selected metrics

        Args:
            modelDetails : dictionary of models and metrics to use for calculations
        """
        modelsToRun = modelDetails["modelsToRun"]
        metricNames = modelDetails["metricNames"]
        if self.data:
            self.estimationComplete = False # estimation not complete since it just started running
            self._main.tabs.tab2.sideMenu.modelListWidget.clear()   # clear tab 2 list containing 
                                                                    # previously computed models,
                                                                    # only added when calculations complete
            self.computeWidget = ComputeWidget(modelsToRun, metricNames, self.data)
            # DON'T WANT TO DISPLAY RESULTS IN ANOTHER WINDOW
            # WANT TO DISPLAY ON TAB 2/3
            self.computeWidget.results.connect(self.onEstimationComplete)     # signal emitted when estimation complete

    def onEstimationComplete(self, results):
        """
        description to be created at a later time

        Args:
            results (dict): contains model objects
        """
        self.estimationComplete = True
        self.estimationResults = results
        self._main.tabs.tab1.sideMenu.runButton.setEnabled(True)    # re-enable button, can run another estimation
        # self.setDataView("view", self.dataViewIndex)
        self.updateUI()
        # set initial model selected
        # set plot

        names = []
        for key, model in results.items():
            if model.converged:
                names.append(key)

        self._main.tabs.tab2.sideMenu.addSelectedModels(names)  # add models to tab 2 list
                                                                # so they can be selected
        self._main.tabs.tab3.addResultsToTable(results)
        logging.info("Estimation results: {0}".format(results))

    def importFile(self):
        """
        Import selected file
        """
        self._main.tabs.tab1.sideMenu.sheetSelect.clear()   # clear sheet names from previous file
        self._main.tabs.tab1.sideMenu.sheetSelect.addItems(self.data.sheetNames)    # add sheet names from new file

        self.setDataView("view", self.dataViewIndex)
        # self.setMetricList()

    def changeSheet(self, index):
        """
        Change the current sheet displayed

        Args:
            index : index of the sheet
        """
        self.data.currentSheet = index      # store 
        self.setDataView("view", self.dataViewIndex)
        self._main.tabs.tab1.plotAndTable.figure.canvas.draw()
        self.setMetricList()

    def setMetricList(self):
        self._main.tabs.tab1.sideMenu.metricListWidget.clear()
        if self.dataLoaded:
            self._main.tabs.tab1.sideMenu.metricListWidget.addItems(self.data.metricNameCombinations)
            logging.info("{0} covariate metrics on this sheet: {1}".format(self.data.numCovariates,
                                                                    self.data.metricNames))

    def setDataView(self, viewType, index):
        """
        Set the data to be displayed. 
        Called whenever a menu item is changed

        Args:
            viewType: string that determines view
            index: index of the dataview list
        """
        if self.data.getData() is not None:
            if viewType == "view":
                self.setRawDataView(index)
                self.dataViewIndex = index  # was at the end of elif statements, but would change mvf/intensity view
                                            # unintentionally when changing sheets
            elif viewType == "trend":
                self.setTrendTest(index)
            elif viewType == "sheet":
                self.changeSheet(index)
            #self.viewType = viewType
                # removed since it would change the sheet displayed when changing display settings

    def setRawDataView(self, index):
        """
        Changes plot between MVF and intensity
        """
        self._main.tabs.tab1.plotAndTable.tableWidget.setModel(self.data.getDataModel())
        dataframe = self.data.getData()
        self.plotSettings.plotType = "step"

        if self.dataViewIndex == 0:     # changed from index to self.dataViewIndex
            # MVF
            self.createMVFPlot(dataframe)
        if self.dataViewIndex == 1:     # changed from index to self.dataViewIndex
            # Intensity
            self.createIntensityPlot(dataframe)

        # redraw figures
        self.ax2.legend()
        self._main.tabs.tab1.plotAndTable.figure.canvas.draw()
        self._main.tabs.tab2.plot.figure.canvas.draw()

    def createMVFPlot(self, dataframe):
        """
        called by setDataView
        """
        self.ax = self.plotSettings.generatePlot(self.ax, dataframe.iloc[:, 0], dataframe["Cumulative"], title="MVF", xLabel="time", yLabel="failures")
        if self.estimationComplete:
            self.ax2 = self.plotSettings.generatePlot(self.ax2, dataframe.iloc[:, 0], dataframe["Cumulative"], title="MVF", xLabel="time", yLabel="failures")
            self.plotSettings.plotType = "plot"
            # for model in self.estimationResults.values():
            #     # add line for model if selected
            #     if model.name in self.selectedModelNames:
            #         self.plotSettings.addLine(self.ax2, model.t, model.mvfList, model.name)



            for modelName in self.selectedModelNames:
                # add line for model if selected
                model = self.estimationResults[modelName]
                self.plotSettings.addLine(self.ax2, model.t, model.mvfList, model.name)

    def createIntensityPlot(self, dataframe):
        """
        called by setDataView
        """
        self.ax = self.plotSettings.generatePlot(self.ax, dataframe.iloc[:, 0], dataframe.iloc[:, 1], title="Intensity", xLabel="time", yLabel="failures")
        if self.estimationComplete:
            self.ax2 = self.plotSettings.generatePlot(self.ax2, dataframe.iloc[:, 0], dataframe.iloc[:, 1], title="Intensity", xLabel="time", yLabel="failures")
            self.plotSettings.plotType = "plot"
            # for model in self.estimationResults.values():
            #     # add line for model if selected
            #     if model.name in self.selectedModelNames:
            #         self.plotSettings.addLine(self.ax2, model.t, model.intensityList, model.name)

            for modelName in self.selectedModelNames:
                # add line for model if selected
                model = self.estimationResults[modelName]
                self.plotSettings.addLine(self.ax2, model.t, model.intensityList, model.name)

    def changePlot2(self, selectedModels):
        self.selectedModelNames = selectedModels
        self.updateUI()


    def setTrendTest(self, index):
        """
        description to be created at a later time
        """
        pass

    def setPlotStyle(self, style='-o', plotType="step"):
        """
        description to be created at a later time
        """
        self.plotSettings.style = style
        self.plotSettings.plotType = plotType
        self.updateUI()
        # self.setDataView("view", self.dataViewIndex)

    def updateUI(self):
        """
        Change Plot, Table and SideMenu
        when the state of the Data object changes

        Should be called explicitly
        """
        self.setDataView(self.viewType, self.dataViewIndex)

    def setupMenu(self):
        """
        description to be created at a later time
        """
        self.menu = self.menuBar()      # initialize menu bar

        # ---- File menu
        fileMenu = self.menu.addMenu("File")
        # open
        openFile = QAction("Open", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip("Import Data File")
        openFile.triggered.connect(self.fileOpened)
        # exit
        exitApp = QAction("Exit", self)
        exitApp.setShortcut("Ctrl+Q")
        exitApp.setStatusTip("Close application")
        exitApp.triggered.connect(self.closeEvent)
        # add actions to file menu
        fileMenu.addAction(openFile)
        fileMenu.addSeparator()
        fileMenu.addAction(exitApp)

        # ---- View menu
        viewMenu = self.menu.addMenu("View")
        # -- plotting style
        # maybe want a submenu?
        viewStyle = QActionGroup(viewMenu)
        # points
        viewPoints = QAction("Show Points", self, checkable=True)
        viewPoints.setShortcut("Ctrl+P")
        viewPoints.setStatusTip("Data shown as points on graphs")
        viewPoints.triggered.connect(self.setPointsView)
        viewStyle.addAction(viewPoints)
        # lines
        viewLines = QAction("Show Lines", self, checkable=True)
        viewLines.setShortcut("Ctrl+L")
        viewLines.setStatusTip("Data shown as lines on graphs")
        viewLines.triggered.connect(self.setLineView)
        viewStyle.addAction(viewLines)
        # points and lines
        viewBoth = QAction("Show Points and Lines", self, checkable=True)
        viewBoth.setShortcut("Ctrl+B")
        viewBoth.setStatusTip("Data shown as points and lines on graphs")
        viewBoth.setChecked(True)
        viewBoth.triggered.connect(self.setLineAndPointsView)
        viewStyle.addAction(viewBoth)
        # add actions to view menu
        viewMenu.addActions(viewStyle.actions())
        # -- graph display
        graphStyle = QActionGroup(viewMenu)
        # MVF
        mvf = QAction("MVF Graph", self, checkable=True)
        mvf.setShortcut("Ctrl+M")
        mvf.setStatusTip("Graphs display MVF of data")
        mvf.setChecked(True)
        mvf.triggered.connect(self.setMVFView)
        graphStyle.addAction(mvf)
        # intensity
        intensity = QAction("Intensity Graph", self, checkable=True)
        intensity.setShortcut("Ctrl+I")
        intensity.setStatusTip("Graphs display failure intensity")
        intensity.triggered.connect(self.setIntensityView)
        graphStyle.addAction(intensity)
        # add actions to view menu
        viewMenu.addSeparator()
        viewMenu.addActions(graphStyle.actions())

    #region Menu actions
    def fileOpened(self):
        files = QFileDialog.getOpenFileName(self, "Open profile", "", filter=("Data Files (*.csv *.xls *.xlsx)"))
        # if a file was loaded
        if files[0]:
            self.data.importFile(files[0])      # imports loaded file
            self.dataLoaded = True
            logging.info("Data loaded from {0}".format(files[0]))
            self.importFileSignal.emit()            # emits signal that file was imported successfully

    def setLineView(self):
        self.setPlotStyle(style='-')
        logging.info("Plot style set to line view.")

    def setPointsView(self):
        self.setPlotStyle(style='o', plotType='plot')
        logging.info("Plot style set to points view.")
    
    def setLineAndPointsView(self):
        self.setPlotStyle(style='-o')
        logging.info("Plot style set to line and points view.")

    def setMVFView(self):
        self.dataViewIndex = 0
        logging.info("Data plots set to MVF view.")
        if self.dataLoaded:
            self.setRawDataView(self.dataViewIndex)

    def setIntensityView(self):
        self.dataViewIndex = 1
        logging.info("Data plots set to intensity view.")
        if self.dataLoaded:
            self.setRawDataView(self.dataViewIndex)
    #endregion


class MainWidget(QWidget):
    """
    description to be created at a later time
    """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.tabs = Tabs()
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

class Tabs(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setupTabs()

    def setupTabs(self):
        self.tab1 = Tab1()
        self.addTab(self.tab1, "Data Upload and Model Selection")

        self.tab2 = Tab2()
        self.addTab(self.tab2, "Model Results and Predictions")

        self.tab3 = Tab3()
        self.addTab(self.tab3, "Model Comparison")

        self.tab4 = Tab4()
        self.addTab(self.tab4, "Effort Allocation")

        self.resize(300, 200)

#region Tab 1
class Tab1(QWidget):
    def __init__(self):
        super().__init__()
        self.setupTab1()

    def setupTab1(self):
        self.horizontalLayout = QHBoxLayout()       # main layout

        self.sideMenu = SideMenu1()
        self.horizontalLayout.addLayout(self.sideMenu, 25)
        self.plotAndTable = PlotAndTable("Plot", "Table")
        self.horizontalLayout.addWidget(self.plotAndTable, 75)

        self.setLayout(self.horizontalLayout)

class SideMenu1(QVBoxLayout):
    """
    Side menu for tab 1
    """

    # signals
    viewChangedSignal = pyqtSignal(str, int)    # should this be before init?
    runModelSignal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setupSideMenu()

    def setupSideMenu(self):
        self.sheetGroup = QGroupBox("Select Sheet")
        self.sheetGroup.setLayout(self.setupSheetGroup())
        self.addWidget(self.sheetGroup)

        self.modelsGroup = QGroupBox("Select Model(s)")
        self.modelsGroup.setLayout(self.setupModelsGroup())
        self.addWidget(self.modelsGroup)

        self.metricsGroup = QGroupBox("Select Metric(s)")
        self.metricsGroup.setLayout(self.setupMetricsGroup())
        self.addWidget(self.metricsGroup)

        self.runButton = QPushButton("Run Estimation")
        self.runButton.clicked.connect(self.emitRunModelsSignal)
        self.addWidget(self.runButton)

        self.addStretch(1)

        # signals
        self.sheetSelect.currentIndexChanged.connect(self.emitSheetChangedSignal)

    def setupSheetGroup(self):
        sheetGroupLayout = QVBoxLayout()
        # sheetGroupLayout.addWidget(QLabel("Select sheet"))

        self.sheetSelect = QComboBox()
        sheetGroupLayout.addWidget(self.sheetSelect)

        return sheetGroupLayout

    def setupModelsGroup(self):
        modelGroupLayout = QVBoxLayout()
        self.modelListWidget = QListWidget()
        loadedModels = [model.name for model in models.modelList.values()]
        self.modelListWidget.addItems(loadedModels)
        logging.info("{0} model(s) loaded: {1}".format(len(loadedModels), loadedModels))
        self.modelListWidget.setSelectionMode(QAbstractItemView.MultiSelection)       # able to select multiple models
        modelGroupLayout.addWidget(self.modelListWidget)

        return modelGroupLayout

    def setupMetricsGroup(self):
        metricsGroupLayout = QVBoxLayout()
        self.metricListWidget = QListWidget()   # metric names added dynamically from data when loaded
        self.metricListWidget.setSelectionMode(QAbstractItemView.MultiSelection)     # able to select multiple metrics
        metricsGroupLayout.addWidget(self.metricListWidget)

        buttonLayout = QHBoxLayout()
        self.selectAllButton = QPushButton("Select All")
        self.clearAllButton = QPushButton("Clear All")
        self.selectAllButton.clicked.connect(self.selectAll)
        self.clearAllButton.clicked.connect(self.clearAll)
        buttonLayout.addWidget(self.selectAllButton, 50)
        buttonLayout.addWidget(self.clearAllButton, 50)
        metricsGroupLayout.addLayout(buttonLayout)

        return metricsGroupLayout
    
    def selectAll(self):
        self.metricListWidget.selectAll()
        self.metricListWidget.repaint()

    def clearAll(self):
        self.metricListWidget.clearSelection()
        self.metricListWidget.repaint()

    def emitRunModelsSignal(self):
        """
        Method called when Run Estimation button pressed.
        Signal that tells models to run (runModelSignal) is
        only emitted if at least one model and at least one
        metric is selected.
        """
        logging.info("Run button pressed.")
        # get model names as strings
        
        selectedModelNames = [item.text() for item in self.modelListWidget.selectedItems()]
        # get model classes from models folder
        modelsToRun = [model for model in models.modelList.values() if model.name in selectedModelNames]
        # get selected metric names (IMPORTANT: returned in order they were clicked)
        selectedMetricNames = [item.text().split(", ") for item in self.metricListWidget.selectedItems()]
            # split combinations
        # sorts metric names in their order from the data file (left to right)
        #metricNames = [self.metricListWidget.item(i).text() for i in range(self.metricListWidget.count()) if self.metricListWidget.item(i).text() in selectedMetricNames]
        # only emit the run signal if at least one model and at least one metric chosen
        if selectedModelNames and selectedMetricNames:
            self.runButton.setEnabled(False)    # disable button until estimation complete
            self.runModelSignal.emit({"modelsToRun": modelsToRun,
                                      "metricNames": selectedMetricNames})
                                      #"metricNames": metricNames})
                                      
            logging.info("Run models signal emitted. Models = {0}, metrics = {1}".format(selectedModelNames, selectedMetricNames))
        elif self.modelListWidget.count() > 0 and self.metricListWidget.count() > 0:
            # data loaded but not selected
            logging.warning("Must select at least one model.")
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Model not selected")
            msgBox.setInformativeText("Please select at least one model.")
            msgBox.setWindowTitle("Warning")
            msgBox.exec_()
        else:
            logging.warning("No data found. Data must be loaded in CSV or Excel format.")
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("No data found")
            msgBox.setInformativeText("Please load failure data as a .csv file or an Excel workbook (.xls, xlsx).")
            msgBox.setWindowTitle("Warning")
            msgBox.exec_()

    def emitSheetChangedSignal(self):
        self.viewChangedSignal.emit("sheet", self.sheetSelect.currentIndex())
#endregion

#region Tab 2
class Tab2(QWidget):
    def __init__(self):
        super().__init__()
        self.setupTab2()

    def setupTab2(self):
        self.horizontalLayout = QHBoxLayout()       # main layout
        self.sideMenu = SideMenu2()
        self.horizontalLayout.addLayout(self.sideMenu, 25)
        self.plot = PlotWidget()
        self.horizontalLayout.addWidget(self.plot, 75)
        self.setLayout(self.horizontalLayout)

class SideMenu2(QVBoxLayout):
    """
    Side menu for tab 2
    """

    # signals
    modelChangedSignal = pyqtSignal(list)    # changes based on selection of models in tab 2

    def __init__(self):
        super().__init__()
        self.setupSideMenu()

    def setupSideMenu(self):
        self.modelsGroup = QGroupBox("Select Model Results")
        self.modelsGroup.setLayout(self.setupModelsGroup())
        self.addWidget(self.modelsGroup)

        self.addStretch(1)

        # signals
        # self.sheetSelect.currentIndexChanged.connect(self.emitSheetChangedSignal)

    def setupModelsGroup(self):
        modelGroupLayout = QVBoxLayout()
        self.modelListWidget = QListWidget()
        modelGroupLayout.addWidget(self.modelListWidget)
        self.modelListWidget.setSelectionMode(QAbstractItemView.MultiSelection)       # able to select multiple models
        self.modelListWidget.itemSelectionChanged.connect(self.emitModelChangedSignal)

        return modelGroupLayout

    def addSelectedModels(self, modelNames):
        """


        Args:
            modelNames (list): list of strings, name of each model
        """

        #self.modelListWidget.clear()
        # modelsRan = modelDetails["modelsToRun"]
        # metricNames = modelDetails["metricNames"]

        # loadedModels = [model.name for model in modelsRan]
        # self.modelListWidget.addItems(loadedModels)

        self.modelListWidget.addItems(modelNames)

    def emitModelChangedSignal(self):
        selectedModelNames = [item.text() for item in self.modelListWidget.selectedItems()]
        logging.info("Selected models: {0}".format(selectedModelNames))
        self.modelChangedSignal.emit(selectedModelNames)

#endregion

#region Tab 3
class Tab3(QWidget):
    def __init__(self):
        super().__init__()
        self.setupTab3()

    def setupTab3(self):
        self.horizontalLayout = QHBoxLayout()       # main layout
        self.setupTable()
        self.horizontalLayout.addWidget(self.table)
        self.setLayout(self.horizontalLayout)

    def setupTable(self):
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)     # make cells unable to be edited
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
                                                                    # column width fit to contents
        self.table.setRowCount(1)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Model Name", "Log-Likelihood", "AIC", "BIC", "SSE"])
        self.table.move(0,0)

    def addResultsToTable(self, results):
        self.table.setSortingEnabled(False) # disable sorting while editing contents
        self.table.clear()
        self.table.setHorizontalHeaderLabels(["Model Name", "Log-Likelihood", "AIC", "BIC", "SSE"])
        self.table.setRowCount(len(results))    # set row count to include all model results, 
                                                # even if not converged
        i = 0   # number of converged models
        for key, model in results.items():
            if model.converged:
                self.table.setItem(i, 0, QTableWidgetItem(model.name))
                self.table.setItem(i, 1, QTableWidgetItem(str(model.llfVal)))
                self.table.setItem(i, 2, QTableWidgetItem(str(model.aicVal)))
                self.table.setItem(i, 3, QTableWidgetItem(str(model.bicVal)))
                self.table.setItem(i, 4, QTableWidgetItem(str(model.sseVal)))
                i += 1
        self.table.setRowCount(i)   # set row count to only include converged models
        self.table.resizeColumnsToContents()    # resize column width after table is edited
        self.table.setSortingEnabled(True)          # re-enable sorting after table is edited


# from https://stackoverflow.com/questions/28660287/sort-qtableview-in-pyqt5
#   can try to adapt to fit our data

# class PandasModel(QAbstractTableModel):

#     def __init__(self, data, parent=None):
#         """

#         :param data: a pandas dataframe
#         :param parent: 
#         """
#         QAbstractTableModel.__init__(self, parent)
#         self._data = data
#         # self.headerdata = data.columns


#     def rowCount(self, parent=None):
#         return len(self._data.values)

#     def columnCount(self, parent=None):
#         return self._data.columns.size

#     def data(self, index, role=QtCore.Qt.DisplayRole):
#         if index.isValid():
#             if role == QtCore.Qt.DisplayRole:
#                 return str(self._data.values[index.row()][index.column()])
#         return None

#     def headerData(self, rowcol, orientation, role):
#         # print(self._data.columns[rowcol])
#         # print(self._data.index[rowcol])
#         if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
#             return self._data.columns[rowcol]
#         if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
#             return self._data.index[rowcol]
#         return None

#     def flags(self, index):
#         flags = super(self.__class__, self).flags(index)
#         flags |= QtCore.Qt.ItemIsEditable
#         flags |= QtCore.Qt.ItemIsSelectable
#         flags |= QtCore.Qt.ItemIsEnabled
#         flags |= QtCore.Qt.ItemIsDragEnabled
#         flags |= QtCore.Qt.ItemIsDropEnabled
#         return flags

#     def sort(self, Ncol, order):
#         """Sort table by given column number.
#         """
#         try:
#             self.layoutAboutToBeChanged.emit()
#             self._data = self._data.sort_values(self._data.columns[Ncol], ascending=not order)
#             self.layoutChanged.emit()
#         except Exception as e:
#             print(e)

#endregion

#region tab4_test
class Tab4(QWidget):
    def __init__(self):
        super().__init__()
        self.setupTab4()

    def setupTab4(self):
        self.mainLayout = QHBoxLayout() # main tab layout
        self.scrollArea = QScrollArea() # allows dynamic number of rows depending on number of covariates
        self.scrollWidget = QWidget()

        self.setupLayouts(3)   # create initial number of rows  

        self.gridLayout.addWidget(QLabel("Metric"), 0, 0)
        self.gridLayout.addWidget(QLabel("Cost"), 0, 1)
        self.gridLayout.addWidget(QLabel("Allocation"), 0, 2)
        self.gridLayout.addWidget(QLabel("%"), 0, 3)
        self.gridLayout.addWidget(QLabel("Total"), 0, 4)

    def setupLayouts(self, numCovariates):
        """
        Creates effort allocation layout and elements depending
        on the number of covariates in data.
        """
        self.gridLayout = QGridLayout() 

        self.covLabels = [0 for i in range(numCovariates)]
        self.costLineEdits = [0 for i in range(numCovariates)]
        self.allocationCheckBoxes = [0 for i in range(numCovariates)]
        self.percentageLineEdits = [0 for i in range(numCovariates)]
        self.totalLineEdits = [0 for i in range(numCovariates)]

        for i in range(numCovariates):
            self.addRow(i)

        self.scrollWidget.setLayout(self.gridLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)

    def addRow(self, i):
        self.covLabels[i] = QLabel("C{0}".format(i))
        self.costLineEdits[i] = QLineEdit()
        self.allocationCheckBoxes[i] = QCheckBox()
        self.percentageLineEdits[i] = QLineEdit()
        self.totalLineEdits[i] = QLineEdit()

        # starts at second row, first is for labels
        self.gridLayout.addWidget(self.covLabels[i], i + 1, 0)              # column 1
        self.gridLayout.addWidget(self.costLineEdits[i], i + 1, 1)          # column 2
        self.gridLayout.addWidget(self.allocationCheckBoxes[i], i + 1, 2)   # column 3
        self.gridLayout.addWidget(self.percentageLineEdits[i], i + 1, 3)    # column 4
        self.gridLayout.addWidget(self.totalLineEdits[i], i + 1, 4)         # column 5

#endregion