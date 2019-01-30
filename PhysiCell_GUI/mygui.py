# Rf  https://www.python.org/dev/peps/pep-0008/
import ipywidgets as widgets
import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
import os
import glob
import shutil
import datetime
import subprocess
from pathlib import Path
from basics import BasicsTab
from user_params import UserTab
from svg import SVGTab
from substrates import SubstrateTab

# join_our_list = "(Join/ask questions at https://groups.google.com/forum/#!forum/physicell-users)\n"

debug_view = widgets.Output(layout={'border': '1px solid black'})

constWidth = '180px'
tab_height = '500px'
tab_layout = widgets.Layout(width='950px',   # border='2px solid black',
                            height=tab_height, overflow_y='scroll',)

# create the tabs, but don't display yet
basics_tab = BasicsTab()
user_tab = UserTab()
svg = SVGTab()
sub = SubstrateTab()

main_xml_filename = 'test.xml'
full_xml_filename = os.path.abspath(main_xml_filename)
#print('full_xml_filename=',full_xml_filename)

tree = ET.parse(full_xml_filename)  # this file cannot be overwritten; part of tool distro
xml_root = tree.getroot()

nanoHUB_flag = "home/nanohub" in os.environ['HOME']  # True/False (running on nanoHUB or not)
#nanoHUB_flag = False

def read_config_cb(_b):
    with debug_view:
        print("read_config", read_config.value)
        # e.g.  "DEFAULT" -> read_config /Users/heiland/dev/pc4nanobio/data/nanobio_settings.xml
        #       "<time-stamp>" -> read_config /Users/heiland/.cache/pc4nanobio/pc4nanobio/59c60c0a402e4089b71b140689075f0b
        #       "t360.xml" -> read_config /Users/heiland/.local/share/pc4nanobio/t360.xml

    if read_config.value is None:  #rwh: happens when a Run just finishes and we update pulldown with the new cache dir??
        return

    if os.path.isdir(read_config.value):
        is_dir = True
#        config_file = os.path.join(read_config.value, 'config.xml')
        config_file = os.path.join(read_config.value, full_xml_filename)
    else:
        is_dir = False
        config_file = read_config.value

    fill_gui_params(config_file)  #rwh: should verify file exists!
    
    # update visualization tabs
    if is_dir:
        svg.update(read_config.value)
        sub.update(read_config.value)
    else:  # may want to distinguish "DEFAULT" from other saved .xml config files
        svg.update('')
        sub.update('')


def write_config_file(name):
    # Read in the default xml config file, just to get a valid 'root' to populate a new one
#    full_xml_filename = os.path.abspath('config.xml')
#    full_xml_filename = os.path.abspath(full_xml_filename)
    tree = ET.parse(full_xml_filename)  # this file cannot be overwritten; part of tool distro
    xml_root = tree.getroot()
    basics_tab.fill_xml(xml_root)
    user_tab.fill_xml(xml_root)
    tree.write(name)

def get_config_files():
#    cf = {'DEFAULT': os.path.abspath('data/nanobio_settings.xml')}
#    cf = {'DEFAULT': os.path.abspath('config.xml')}
    cf = {'DEFAULT': full_xml_filename}
    dirname = os.path.expanduser('~/.local/share/pc4nanobio')
    try:
        os.makedirs(dirname)
    except:
        pass
    files = glob.glob("%s/*.xml" % dirname)
    # dict.update() will append any new (key,value) pairs
    cf.update(dict(zip(list(map(os.path.basename, files)), files)))

    if nanoHUB_flag:
        full_path = os.path.expanduser("~/data/results/.submit_cache/pc4nanobio")
    else:
        # local cache
        try:
            cachedir = os.environ['CACHEDIR']
            full_path = os.path.join(cachedir, "pc4nanobio")
        except:
            print("Exception in get_config_files")
            return cf

    dirs = [os.path.join(full_path, f) for f in os.listdir(full_path) if f != '.cache_table']
    with debug_view:
        print(dirs)

    # Get a list of sorted dirs, according to creation timestamp (newest -> oldest)
    sorted_dirs = sorted(dirs, key=os.path.getctime, reverse=True)
    with debug_view:
        print(sorted_dirs)
    sorted_dirs_dates = [str(datetime.datetime.fromtimestamp(os.path.getctime(x))) for x in sorted_dirs]
    cached_file_dict = dict(zip(sorted_dirs_dates, sorted_dirs))
    cf.update(cached_file_dict)
    with debug_view:
        print(cf)
    return cf

def fill_gui_params(config_file):
    tree = ET.parse(config_file)
    xml_root = tree.getroot()
    basics_tab.fill_gui(xml_root)
    user_tab.fill_gui(xml_root)
    # cells.fill_gui(xml_root)

def update_plot_frames():
    max_frames = basics_tab.get_num_svg_frames()
    svg.update_max_frames_expected(max_frames)

    max_frames = basics_tab.get_num_substrate_frames()
    sub.update_max_frames_expected(max_frames)

def write_button_cb(s):
    with debug_view:
        print('write_button_cb')

#    new_config_file = "config.xml"
    new_config_file = full_xml_filename
    write_config_file(new_config_file)

write_button = widgets.Button(
    description='Write',
    button_style='success',  # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Write '+main_xml_filename,
)
write_button.on_click(write_button_cb)


def run_button_cb(s):
    with debug_view:
        print('run_button_cb')

#    new_config_file = "config.xml"
    new_config_file = full_xml_filename
    write_config_file(new_config_file)
#    subprocess.call(["biorobots", xml_file_out])
#    subprocess.call(["myproj", new_config_file])   # spews to shell, but not ctl-C'able
#    subprocess.call(["myproj", new_config_file], shell=True)  # no
    subprocess.Popen(["myproj", new_config_file])

run_button = widgets.Button(
    description='Run',
    button_style='success',  # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Update '+ main_xml_filename +' and run a simulation',
)
run_button.on_click(run_button_cb)

titles = ['Basics', 'User Params', 'Cell Plots', 'Substrate Plots']
tabs = widgets.Tab(children=[basics_tab.tab, user_tab.tab, svg.tab, sub.tab],
                   _titles={i: t for i, t in enumerate(titles)},
                   layout=tab_layout)

#gui = widgets.VBox(children=[tabs, write_button])
gui = widgets.VBox(children=[tabs, run_button])
fill_gui_params(full_xml_filename)

# pass in (relative) directory where output data is located
#svg.update(read_config.value)
output_dir = "output"   # for local desktop
if nanoHUB_flag:
    output_dir = "tmpdir"  # for nanoHUB?
svg.update(output_dir)
sub.update_dropdown_fields(output_dir)
sub.update(output_dir)
