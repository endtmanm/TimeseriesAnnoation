import numpy as np
import matplotlib
from matplotlib.dates import date2num, num2date
from matplotlib.collections import PolyCollection
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from PyQt5 import QtWidgets, QtCore, Qt
import sys
import re
from pandas import read_csv
from datetime import datetime as dt

matplotlib.use('Qt5Agg')
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
        ax1.set_title('Start by importing a CSV File -->')
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

        self.import_layout = QtWidgets.QHBoxLayout()
        self.checkbox_layout = QtWidgets.QVBoxLayout()
        self.import_button = QtWidgets.QPushButton(self.main_widget)
        self.import_button.setText("Import Timeseries!")
        self.import_button.clicked.connect(self.load_timeseries)
        self.import_layout.addWidget(self.import_button)
        self.import_layout.addLayout(self.checkbox_layout)
        self.skip_col_checkbox = QtWidgets.QCheckBox(self.main_widget)
        self.skip_col_checkbox.setText("Skip First Column")
        self.skip_col_checkbox.setChecked(True)
        self.checkbox_layout.addWidget(self.skip_col_checkbox)
        self.skip_row_checkbox = QtWidgets.QCheckBox(self.main_widget)
        self.skip_row_checkbox.setText("Skip First Row")
        self.checkbox_layout.addWidget(self.skip_row_checkbox)

        self.list_widget = QtWidgets.QListWidget(self.main_widget)
        self.list_layout = QtWidgets.QVBoxLayout()
        self.list_widget.setLayout(self.list_layout)
        self.list_widget.installEventFilter(self)
        self.list_widget.itemSelectionChanged.connect(self.color_change)

        self.export_button = QtWidgets.QPushButton(self.main_widget)
        self.export_button.setText("Export Annotations!")
        self.export_button.clicked.connect(self.export_list)
        self.button_layout.addLayout(self.import_layout)

        self.button_layout.addWidget(self.list_widget)
        self.button_layout.addWidget(self.export_button)

        # Add to main widget
        main_horizontal.addLayout(plot_vertical_widget, 4)
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
            header = [0]
            parse_dates = [0]
            self.use_dates = True
            indices = 0
            usecols = [i for i in range(ncols)]
            if self.skip_col_checkbox.isChecked():
                header = 0
            if self.skip_row_checkbox.isChecked():
                parse_dates = False
                self.use_dates = False
                usecols = [i for i in range(1, ncols)]
                indices = False
            series = read_csv(file_name, header=header, parse_dates=parse_dates, usecols=usecols, index_col=indices,
                              squeeze=True)
            self.plot_timeseries(series, file_name)
            self.list_widget.clear()

    def plot_timeseries(self, data, file_name):
        ax1.clear()
        ax2.clear()
        ax1.set_title(file_name)
        self.x = data.index.values
        self.y = data.values
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
        beginning = np.min(verts[:, 0])
        end = np.max(verts[:, 0])
        # print(beginning, end)
        indmin, indmax = 0, 0
        if self.use_dates:
            indmin, indmax = self.get_index_from_datetime(beginning, end)
        else:
            indmin, indmax = np.searchsorted(self.x, (int(beginning), int(end)))
            indmax = min(len(self.x) - 1, indmax)

        thisx = self.x[indmin:indmax]
        thisy = self.y[indmin:indmax]
        self.line2.set_data(thisx, thisy)
        ax2.set_xlim(thisx[0], thisx[-1])
        ax2.set_ylim(thisy.min(), thisy.max())

    def export_list(self):
        print("Export!")
        annotations = []
        for item in self.iterAllItems(self.list_widget):
            fill_area = item.data(1)
            paths = fill_area.get_paths()
            verts = paths[0].vertices
            beginning = int(np.min(verts[:, 0]))
            end = int(np.max(verts[:, 0]))
            annotations.append((beginning, end))
        print(annotations)
        np.savetxt(self.filename + " - annotations.csv", np.asarray(annotations, dtype=int), fmt="%f,%f", delimiter=",")
        return True

    def onselect(self, xmin, xmax):
        # print(xmin, xmax)
        indmin, indmax = 0, 0
        if self.use_dates:
            xmin, xmax = xmin//1, xmax//1
            indmin, indmax = self.get_index_from_datetime(xmin, xmax)
        else:
            indmin, indmax = np.searchsorted(self.x, (xmin, xmax))
            indmax = min(len(self.x) - 1, indmax)

        thisx = self.x[indmin:indmax]
        thisy = self.y[indmin:indmax]
        poly_collection = ax1.fill_between(thisx, self.y_upper_lim, self.y_lower_lim, color="r", alpha=0.25)
        self.line2.set_data(thisx, thisy)
        ax2.set_xlim(thisx[0], thisx[-1])
        ax2.set_ylim(thisy.min(), thisy.max())

        begin_str, end_str = "", ""
        if self.use_dates:
            # Formatting Date String from ISO to German Notation
            begin_str = re.sub(':', ' ', np.datetime_as_string(thisx[0], unit='s'))
            end_str = re.sub(':', ' ', np.datetime_as_string(thisx[-1], unit='s'))
            begin_str = dt.strptime(begin_str, '%Y-%m-%dT%H %M %S').strftime('%d.%m.%Y, %H:%M:%S')
            end_str = dt.strptime(end_str, '%Y-%m-%dT%H %M %S').strftime('%d.%m.%Y, %H:%M:%S')
        else:
            begin_str = str(indmin)
            end_str = str(indmax)

        list_item = QtWidgets.QListWidgetItem(begin_str + " - " + end_str)
        list_item.setData(1, poly_collection)
        self.list_widget.addItem(list_item)
        self.canvas.draw()

    def get_index_from_datetime(self, xmin, xmax):
        d_min = np.datetime64(num2date(xmin))
        d_max = np.datetime64(num2date(xmax))
        closest_date_to_d_min = min(self.x, key=lambda x: abs(x - d_min))
        closest_date_to_d_max = min(self.x, key=lambda x: abs(x - d_max))
        ind_one = next((i for i, o in enumerate(self.x) if o == closest_date_to_d_min))
        ind_two = next((i for i, o in enumerate(self.x) if o == closest_date_to_d_max))
        # indmax = min(len(self.x) - 1, indmax)
        indmin = min(ind_one, ind_two)
        indmax = max(ind_one, ind_two)
        return indmin, indmax

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
plt.subplots_adjust(left=0.05, right=0.985, top=0.92, bottom=0.055)
ax1.set(facecolor='#FFFFCC')
a = ScrollableWindow(fig)
