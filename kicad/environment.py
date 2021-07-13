''' Automatic linker to pcbnew GUI and pcbnew python package
    Use this one time to create the link.

    Copy-paste the argument from pcbnew terminal.

    1. Run this in pcbnew's terminal window::

    print('link_kicad_python_to_pcbnew', pcbnew.__file__, pcbnew.GetKicadConfigPath())

    Copy the output. It should look something like::

    link_kicad_python_to_pcbnew /usr/lib/python3/dist-packages/pcbnew.py /home/atait/.config/kicad

    2. Paste and run what you copied into command line from an environment where you have installed this package
'''
import os, sys
import argparse



# Tells this package where to find pcbnew module
pcbnew_path_store = os.path.join(os.path.dirname(__file__), '.path_to_pcbnew_module')


def get_pcbnew_path_from_file():
    if not os.path.isfile(pcbnew_path_store):
        return None
    with open(pcbnew_path_store) as fx:
        return fx.read().strip()


def get_pcbnew_path():
    # Look for the real pcbnew from environment and then file
    pcbnew_swig_path = os.environ.get('PCBNEW_PATH', get_pcbnew_path_from_file())
    if pcbnew_swig_path:
        # Validate
        if os.path.basename(pcbnew_swig_path) != 'pcbnew.py':
            raise EnvironmentError(
                'Incorrect location for \'PCBNEW_PATH\' ({}).'
                ' It should point to a file called pcbnew.py'.format(pcbnew_swig_path))
        if not os.path.isfile(pcbnew_swig_path):
            raise EnvironmentError(
                'Incorrect location for \'PCBNEW_PATH\' ({}).'
                ' File does not exist'.format(pcbnew_swig_path))
    return pcbnew_swig_path


def get_pcbnew_module():
    try:
        return __import__('pcbnew')  # If this works, we are probably in the pcbnew application, and we're done.
    except ImportError:
        pass

    pcbnew_swig_path = get_pcbnew_path()
    if pcbnew_swig_path:
        sys.path.insert(0, os.path.dirname(pcbnew_swig_path))
        try:
            pcbnew_bare = __import__('pcbnew')
        except ImportError as err:
            if err.args[0].startswith('dynamic module does not define'):
                print('You are likely using Mac or Windows,'
                      ' which means kicad does not yet support python 3 on your system.'
                      ' You will be able to use kicad-python within the pcbnew application,'
                      ' but not as a standalone.')
            else:
                print('Warning: pcbnew.py was located but could not be imported. It might be a python 2/3 issue:\n')
                print(err)
            pcbnew_bare = None
    else:
        # special case for documentation without pcbnew at all
        spoofing_for_documentation = os.environ.get('KICAD_PYTHON_IN_SPHINX_GENERATION', '0')
        if spoofing_for_documentation == '1':
            class SphinxEnumPhony:
                def __getattr__(self, attr):
                    return 0
            pcbnew_bare = SphinxEnumPhony()
        else:
            # failed to find pcbnew
            print(
                'pcbnew is required by kicad-python.'
                ' It gets installed when you install the kicad application, but not necessarily on your python path.'
                '\nSee instructions for how to link them at https://github.com/atait/kicad-python'
            )
            pcbnew_bare = None
    return pcbnew_bare

try:
        get_pcbnew_path()
    except ImportError as err:
        if err.args[0].startswith('dynamic module does not define'):
            print('You are likely using Mac or Windows,'
                  ' which means kicad does not yet support python 3 on your system.'
                  ' You will be able to use kicad-python in the pcbnew application,'
                  ' but not outside of it for batch processing.')
        else:
            raise
    else:
        print('Successfully linked kicad-python with pcbnew')


# Tells pcbnew application where to find this package
startup_script = """### Auto generated kicad-python initialization for pcbnew console
import sys, pcbnew
sys.path.append("{}")
from kicad.pcbnew.board import Board
pcb = Board.from_editor()
"""

plugin_script = """### Auto generated kicad-python initialization for pcbnew action plugins
import sys
sys.path.append("{}")
"""


def create_link(pcbnew_module_path, kicad_config_path):
    # Determine what to put in the startup script
    my_package_path = os.path.dirname(__file__)
    my_search_path = os.path.dirname(my_package_path)
    startup_contents = startup_script.format(my_search_path)
    # Determine where to put the startup script
    startup_file = os.path.join(kicad_config_path.strip(), 'PyShell_pcbnew_startup.py')
    # Check that we are not overwriting something
    write_is_safe = True
    if os.path.isfile(startup_file):
        with open(startup_file) as fx:
            line = fx.readline()
        if line.startswith('### DEFAULT STARTUP FILE'):
            pass
        elif line.startswith('### Auto generated kicad-python'):
            pass
        else:
            write_is_safe = False

    # Write the startup script
    if write_is_safe:
        print('1. Writing console startup script,', startup_file)
        with open(startup_file, 'w') as fx:
            fx.write(startup_contents)
    else:
        print('Warning: Startup file is not empty:\n', startup_file)
        print('It is safer to do this manually by inserting these lines into that file:\n\n', startup_script)

    # Write the plugin importer
    plugin_dir = os.path.join(kicad_config_path.strip(), 'scripting', 'plugins')
    os.makedirs(plugin_dir, exist_ok=True)
    plugin_file = os.path.join(plugin_dir, 'initialize_kicad_python_plugin.py')
    plugin_contents = plugin_script.format(my_search_path)
    print('2. Writing plugin importer,', plugin_file)
    with open(plugin_file, 'w') as fx:
        fx.write(plugin_contents)

    # Store the location of pcbnew module
    print('3. Writing pcbnew path,', pcbnew_path_store)
    with open(pcbnew_path_store, 'w') as fx:
        fx.write(pcbnew_module_path.strip())

    # Try it
    get_pcbnew_path()
    print('Successfully linked kicad-python with pcbnew')


help_msg = """
Create bidirectional link between kicad-python and pcbnew.
To get the arguments correct, copy this and run it in pcbnew application console:

  import pcbnew; print('link_kicad_python_to_pcbnew ' + pcbnew.__file__ + ' ' + pcbnew.GetKicadConfigPath())

Copy the output of that and paste it back into this console.
"""
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=help_msg)
parser.add_argument('pcbnew_module_path', type=str)
parser.add_argument('kicad_config_path', type=str)

def cl_main():
    args = parser.parse_args()
    create_link(args.pcbnew_module_path, args.kicad_config_path)
