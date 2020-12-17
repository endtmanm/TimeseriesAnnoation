import numpy as np
import re
import matplotlib
from matplotlib.collections import PolyCollection
import matplotlib.pyplot as plt

matplotlib.use('Qt5Agg')
from matplotlib.widgets import SpanSelector
from PyQt5 import QtWidgets, QtCore, Qt
import sys

# Fixing random state for reproducibility
np.random.seed(19680801)

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar


class ScrollableWindow(QtWidgets.QMainWindow):
    def __init__(self, fig):
        self.qapp = QtWidgets.QApplication([])

        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Main Window")
        # initial Plot
        self.x = np.arange(0.0, 5.0, 0.01)
        self.y = np.sin(2 * np.pi * self.x) + 0.5 * np.random.randn(len(self.x))
        self.y_upper_lim = np.max(self.y)
        self.y_lower_lim = np.min(self.y)
        ax1.set_ylim(-2, 2)
        ax1.set_title('Press left mouse button and drag to test')
        ax2.set(facecolor='#FFFFCC')
        self.span_selector = SpanSelector(ax1, self.onselect, 'horizontal', useblit=True,
                                          rectprops=dict(alpha=0.5, facecolor='red'))
        # Plot end

        # Right Area Creation
        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        main_horizontal = QtWidgets.QHBoxLayout(self.main_widget)

        plot_vertical_widget = QtWidgets.QVBoxLayout(self.main_widget)
        self.fig = fig
        self.canvas = FigureCanvas(self.fig)
        self.canvas.draw()

        self.nav = NavigationToolbar(self.canvas, self.main_widget)
        plot_vertical_widget.addWidget(self.canvas)
        plot_vertical_widget.addWidget(self.nav)

        # Left Area Creation
        self.button_layout = QtWidgets.QVBoxLayout()
        self.import_button = QtWidgets.QPushButton(self.main_widget)
        self.import_button.setText("Import Timeseries!")
        self.import_button.clicked.connect(self.load_timeseries)
        self.list_widget = QtWidgets.QListWidget(self.main_widget)
        self.list_layout = QtWidgets.QVBoxLayout()
        self.list_widget.setLayout(self.list_layout)
        self.list_widget.installEventFilter(self)
        self.list_widget.itemSelectionChanged.connect(self.color_change)
        self.export_button = QtWidgets.QPushButton(self.main_widget)
        self.export_button.setText("Export Annotations!")
        self.export_button.clicked.connect(self.export_list)
        self.button_layout.addWidget(self.import_button)
        self.button_layout.addWidget(self.list_widget)
        self.button_layout.addWidget(self.export_button)

        # Add to main widget
        main_horizontal.addLayout(plot_vertical_widget, 5)
        main_horizontal.addLayout(self.button_layout, 1)

        self.show()
        sys.exit(self.qapp.exec_())

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.ContextMenu and source is self.list_widget):
            menu = QtWidgets.QMenu()
            menu.addAction('Delete Entry')
            if menu.exec_(event.globalPos()):
                item = source.itemAt(event.pos())
                if item:
                    print(item.text())
                    item.data(1).remove()
                    self.canvas.draw()
                    self.list_widget.takeItem(self.list_widget.row(item))
            return True
        return super(ScrollableWindow, self).eventFilter(source, event)

    def iterAllItems(self, qt_list):
        for i in range(qt_list.count()):
            yield qt_list.item(i)

    def load_timeseries(self):
        print("Open file!")
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a Timeseries", "",
                                                             "CSV Files (*.csv)", options=options)
        if file_name:
            self.filename = re.sub(".csv", "", file_name)
            print(file_name)
            with open(file_name) as f:
                ncols = len(f.readline().split(','))
            data = np.loadtxt(file_name, delimiter=',', skiprows=1, usecols=range(1, ncols))
            self.plot_timeseries(data)
            self.list_widget.clear()

    def plot_timeseries(self, data):
        # print("Plot Timeseries")
        # print(data)
        ax1.clear()
        ax2.clear()
        self.x = range(0, len(data))
        self.y = data
        self.y_upper_lim = np.max(self.y)
        self.y_lower_lim = np.min(self.y)
        ax1.plot(self.x, self.y, '-')
        ax1.set_ylim(self.y_lower_lim, self.y_upper_lim)
        self.line2, = ax2.plot(self.x, self.y, '-')
        self.span_selector = SpanSelector(ax1, self.onselect, 'horizontal', useblit=True,
                                          rectprops=dict(alpha=0.5, facecolor='red'))
        self.canvas.draw()

    def zoom_in_area(self, fill_area: PolyCollection):
        paths = fill_area.get_paths()
        verts = paths[0].vertices
        beginning = int(np.min(verts[:, 0]))
        end = int(np.max(verts[:, 0]))
        thisx = self.x[beginning:end+1]
        thisy = self.y[beginning:end+1]
        self.line2.set_data(thisx, thisy)
        ax2.set_xlim(thisx[0], thisx[-1])
        ax2.set_ylim(thisy.min(), thisy.max())

    def export_list(self):
        print("Export!")
        annotations = []
        for item in self.iterAllItems(self.list_widget):
            length_list = []
            for position in item.text().split(" - "):
                length_list.append(int(position))
            annotations.append(length_list)
            # annotations.append(item.data(1).get_offset_position())
        print(annotations)
        np.savetxt(self.filename+" - annotations.csv", np.asarray(annotations, dtype=int), fmt="%i,%i", delimiter=",")
        return True

    def onselect(self, xmin, xmax):
        indmin, indmax = np.searchsorted(self.x, (xmin, xmax))
        indmax = min(len(self.x) - 1, indmax)

        thisx = self.x[indmin:indmax]
        thisy = self.y[indmin:indmax]
        print((thisx[0], thisx[-1]))
        poly_collection = ax1.fill_between(thisx, self.y_upper_lim, self.y_lower_lim, color="r", alpha=0.25)

        self.line2.set_data(thisx, thisy)
        ax2.set_xlim(thisx[0], thisx[-1])
        ax2.set_ylim(thisy.min(), thisy.max())
        list_item = QtWidgets.QListWidgetItem(str(thisx[0]) + " - " + str(thisx[-1]))

        # self.list_dict[list_item] = poly_collection
        list_item.setData(1, poly_collection)
        self.list_widget.addItem(list_item)
        self.canvas.draw()

    def color_change(self):
        if len(self.list_widget.selectedItems()) > 0:
            for item in self.iterAllItems(self.list_widget):
                if item.isSelected():
                    item.data(1).set_color("b")
                    self.zoom_in_area(item.data(1))
                else:
                    item.data(1).set_color("r")

            self.canvas.draw()


fig, (ax1, ax2) = plt.subplots(2)
ax1.set(facecolor='#FFFFCC')
a = ScrollableWindow(fig)
