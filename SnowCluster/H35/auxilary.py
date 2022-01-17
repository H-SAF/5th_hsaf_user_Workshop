import sys
import yaml
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
import glob
import os
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import numpy as np


# region Progress defined to show the selected process
def progressbar(it, prefix="", size=60, file=sys.stdout):
    count = len(it)

    def show(j):
        x = int(size * j / count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#" * x, "." * (size - x), j, count))
        file.flush()

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)
    file.write("\n")
    file.flush()


# endregion

# region Widgets for Module 1
button = widgets.Button(description="Download")
output = widgets.Output()

w = widgets.Dropdown(
    options=['h10', 'h13', 'h34','h35'],
    description='Product:',
    disabled=False,
)

run_flag_widget = widgets.Dropdown(
    options=['Sample Data', 'Downloaded Data'],
    description='Analyses Run Mode',
    disabled=False,
)
indate = widgets.DatePicker(
    description='Start Date',
    disabled=False
)

outdate = widgets.DatePicker(
    description='End Date',
    disabled=False
)

username = widgets.Text(
    value='',
    placeholder='Meteoam username',
    description='Username:',
    disabled=False
)

password = widgets.Password(
    placeholder='Meteoam Password',
    description='Password:',
    disabled=False
)

# endregion

# region yaml configurations
CONFIGLOCATION = r"misc/config.yml"


def fill_and_update_options(product, start_date, end_date, run_flag='Downloaded Data', selected_date=None):
    if product == 'h10' or product == 'h34':
        ext = 'H5'
    else:
        ext = 'grib2'
    for f in glob.glob1('./' + product + "_data", "*.*"):
        os.remove(os.path.join('./' + product + "_data", f))
    # [os.remove(f) for row in glob.glob1(os.path.join(product, '_data'), "*.*")]
    if selected_date is None:
        selected_date = end_date
    data = dict(
        product=product,
        ext=ext,
        date_interval=dict(
            start_date=start_date,
            end_date=end_date
        ),
        selected_date=selected_date,
        run_flag=run_flag
    )
    with open(CONFIGLOCATION, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


def read_config():
    with open(CONFIGLOCATION, 'r') as ymlfile:
        return yaml.load(ymlfile)


#
# def temp_data_export():
#
# # endregion

# region

def manipulate(data, product):
    if product == 'H13':
        data = np.zeros((data.shape[0], data.shape[1]))
#         for i in range(0, data.shape[0]):
#             for j in range(0, data.shape[1]):
#                 if data[i][j] < 0:
#                     manipulated_data[i][j] = 0
#                 else:
#                     manipulated_data[i][j] = data[i][j]
#             manipulated_data = manipulated_data.astype(int)
        data = np.where(data == 0, 2, data)   # land - blue
        data = np.where(data == -1, 1, data)  # Sea - black
        data = np.where(data == -2, 0, data)  # noData - grey
        min = 0
        max = 255
        data = np.where((data == 1) | (data == 2), data, ((data - min)/(max - min))*255)
    else:
        data = data
    return data


def pal(product):
    if product == 'H10' or product == 'H34':
        viridis = cm.get_cmap('Paired', 256)
        newcolors = viridis(np.linspace(0, 1, 256))
        newcolors[:40, :] = np.array([255 / 256, 255 / 256, 255 / 256, 1.])
        newcolors[40:80, :] = np.array([0, 255 / 256, 255 / 256, 1.])
        newcolors[80:165, :] = np.array([0, 150 / 256, 0, 1.])
        newcolors[165:210, :] = np.array([0, 0, 256 / 256, 1.])
        newcolors[210:250, :] = np.array([40 / 256, 40 / 256, 40 / 256, 1.])
        newcolors[250:, :] = np.array([0, 0, 0, 1.])
        newcmp = ListedColormap(newcolors)
    else:
#         h13_palette = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
#                        (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 175),
#                        (0, 0, 175), (0, 0, 175), (0, 0, 175), (0, 0, 175), (0, 0, 223), (0, 0, 223), (0, 0, 223),
#                        (0, 0, 223), (0, 0, 223), (0, 0, 255), (0, 0, 255), (0, 0, 255), (0, 0, 255), (0, 0, 255),
#                        (0, 47, 255), (0, 47, 255), (0, 47, 255), (0, 47, 255), (0, 47, 255), (0, 95, 255),
#                        (0, 95, 255), (0, 95, 255), (0, 95, 255), (0, 95, 255), (0, 143, 255), (0, 143, 255),
#                        (0, 143, 255), (0, 143, 255), (0, 143, 255), (0, 175, 255), (0, 175, 255), (0, 175, 255),
#                        (0, 175, 255), (0, 175, 255), (0, 223, 255), (0, 223, 255), (0, 223, 255), (0, 223, 255),
#                        (0, 223, 255), (0, 255, 239), (0, 255, 239), (0, 255, 239), (0, 255, 239), (0, 255, 239),
#                        (47, 255, 207), (47, 255, 207), (47, 255, 207), (47, 255, 207), (47, 255, 207), (95, 255, 159),
#                        (95, 255, 159), (95, 255, 159), (95, 255, 159), (95, 255, 159), (143, 255, 111),
#                        (143, 255, 111), (143, 255, 111), (143, 255, 111), (143, 255, 111), (175, 255, 79),
#                        (175, 255, 79), (175, 255, 79), (175, 255, 79), (175, 255, 79), (223, 255, 31), (223, 255, 31),
#                        (223, 255, 31), (223, 255, 31), (223, 255, 31), (255, 239, 0), (255, 239, 0), (255, 239, 0),
#                        (255, 239, 0), (255, 239, 0), (255, 207, 0), (255, 207, 0), (255, 207, 0), (255, 207, 0),
#                        (255, 207, 0), (255, 159, 0), (255, 159, 0), (255, 159, 0), (255, 159, 0), (255, 159, 0),
#                        (255, 111, 0), (255, 111, 0), (255, 111, 0), (255, 111, 0), (255, 111, 0), (239, 0, 0),
#                        (239, 0, 0), (239, 0, 0), (239, 0, 0), (239, 0, 0), (207, 0, 0), (207, 0, 0), (207, 0, 0),
#                        (207, 0, 0), (207, 0, 0), (159, 0, 0), (159, 0, 0), (159, 0, 0), (159, 0, 0), (159, 0, 0),
#                        (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0),
#                        (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0),
#                        (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0), (127, 0, 0),
#                        (127, 0, 0), (127, 0, 0)]
        viridis = cm.get_cmap('jet', 256)
        newcolors = viridis(np.linspace(0, 1, 256))
        newcolors[2] = ([0. , 0.7 , 0.4, 1 ])
        newcolors[1] = ([0. , 0. , 0., 1 ])
        newcolors[0] = (192/255 , 192/255, 192/255, 1)
        newcmp = ListedColormap(newcolors)
#         h13_palette = np.asarray(h13_palette) / 255.0
#         newcmp = ListedColormap(h13_palette)

    return newcmp

# endregion


