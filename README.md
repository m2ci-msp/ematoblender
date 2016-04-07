## Synopsis

Watch your tongue! Ematoblender is a Python package intended to be run in Blender, and utilises either a static data file or a live connection to the NDI Wave EMA machine to visualise articulographic data.
It's currently supporting watching the coil objects move from the WAVE or static data.

For version 1.0 the system has the ability to do live-control of a human-like face in Blender.
For version 1.1 the system can also include a multilinear tongue model. More details to come.

## Installation
Cross-platform installation is easy! Just clone the this repository, and in the root directory run:

  *   ``./gradlew setup`` if you're using Linux/OSX in the terminal, or
  *   ``gradlew setup`` at the command prompt if you're a Windows user.

Installation has been tested on recent versions of OSX and Ubuntu, as well as Windows 7.

There are several dependencies in this package:

1. Blender (2.74+)
2. Python (3.3+)
3. Pip
4. Numpy
5. Mathutils

The installation script will check your versions, and warn you if you need to update.
It will also notify you if certain packages are not installed (such as mathutils) and give you OS-specific advice about
how to rectify this. Therefore don't be shy about reading the terminal output if the build fails!

For the C++ utilities, you need the additional dependencies:

6. armadillo (http://arma.sourceforge.net/)
7. Insight Segmentation and Registration Toolkit (http://www.itk.org/)
8. Asio library (http://think-async.com/)

Right now, these dependencies are not checcked by the gradle script.


## Execution
The execution of this package is made significantly easier with gradle:

Just run ``gradlew run`` or ``gradle runFromWave`` (remember to add the ``./`` prefix on UNIX)
to run the static-data streaming system or the WAVE-interfacing system respectively.

Alternatively, Windows users can also use the appropriately-named BAT files in the top directory.
To execute these, double-click on the icon, or if there is a problem, right-click and choose ``Run as administrator``

These scripts use gradle to launch the dataserver and gameserver with GUIs enabled.

All that is left is to run Blender (the package's menu should be loaded on startup) and set up your scene,
as described below.

Alternatively you can run these scripts manually for more control:
This involves:

1. Running the static server ``python ematoblender/dataserver.py`` (various CL options)
1. Running the game server ``python ematoblender/gameserver.py`` (various CL options)

1. If you want to eschew the Blender options, you can load the initial coil positions using the ``run_bpy.py`` script
in a blend file saved in the repository's root directory. Else just use the menu in Blender.

## Configuring Blender

You can find the Ematoblender options on the Properties panel (press ``N`` and scroll to the end.
To configure a scene that will stream data that moves a face I recommend you open the blend file in ``ematoblender/DEMO_MODEL.blend``
You will need to manually adjust the position of the head around your data, and re-parent any wayward coil objects.

Alternatively you can construct a scene from scratch using the Ematoblender options.
1. Load the gamemaster (this handles the logic)
2. Load the game assets (this loads menus etc) **TODO**
4. Load the face mesh (pre-rigged) ** TODO**
5. Load the tongue model **TODO**
6. Load the palate model **TODO **

3. Request some head-corrected data from the gameserver (this will give a rough estimate of where the assets need to be
placed to be controlled by the data. **TODO**
8. Ensure that you have performed a biteplate recording for head-correction
7. Adapt the palate model by performing a palate trace. **TODO**

9. Save the blend file.

10. Press ``P`` with your cursor over the 3D viewport to begin the game in the viewport. Press ``Q`` to quit.


## Architecture

It has a three-part architecture:

1. The real-time server as either:

    1.  the Wave native software on port 3030 (search in code for 'localhost' and set to your IP address that is hosting the Wave machine)
    2.  locally, by running `run_rtserver.py` in the terminal with the command line arguments telling it about the datafile and whether to loop. This will run until you kill it.
     Inspect the code for information about how to best enter the command line arguments.
     Also be aware that the game engine later looks for an audio file to match this data file, so it works best if you give it an absolute path. Audio files should be in the same directory or a sister directory.

2. The game server.

    The most basic way to access the 'server' is using the script ``run_gameserver`` which interfaces with the real-time server and saves its responses in queues.
    This acts as a UDP server, and streams the information to Blender when requested.
    This server can also save the WAV and TSV files streamed, and perform head-correction/other data manipulations.
    There are plans to later develop a GUI for this component.

3. The Blender game loop.

    This is run in Blender on every nth tick, and gathers user input, sends requests for and receives the information needed from game server,
    updates the state of the game. On its conclusion, the Game Engine renders this new state into fancy graphics.
    Input is basically keypresses from the user. Use ``P`` to run the game in the Blender window, ``Q`` to stop the game loop (you can also use ``Esc`` but that won't kill the game server and will cause you problems as it continues streaming.''
    [ONGOING] In the future the game loop should be runnable as a standalone, for now it is only available within Blender proper.

    &nbsp;

    There are two additional components:

    &nbsp;

4. The Blender Scene construction scripts
    You can run ``run_bpy.py`` in the Blender Text Editor viewport to build the game scene from scratch:
    1. Check that all the relevant scripts are available and that your ``.blend'' is saved appropriately.
    2. Create the basic objects and logic bricks to make the game engine work.
    3. Append external assets like rigged lips/tongues/palate traces etc, and game menus etc.
    4. Initialise the game server and get one frame of locational information to set an initial position for the coils.
    5. [ONGOING] Scale the assets so they fit the initial data shape and link them to the game's objects.

    Also, there is [ONGOING] work to fit these functions into an add-on, so that instead of running the script, this can be done at the click of a button.

    &nbsp;

5. Properties and JSON files
    1. The ``scripts.ema_shared.properties.py`` file contains various constants that are accessed from either (or both!) of the Blender game loop or the Blender scene construction routines.
    These generally refer to the names and locations of assets (these names are very important as they the main way of accessing objects in Blender), or of external files that need to be imported/accessed.
    2. The properties file needs access to a JSON file with information about which sensor lies where on the subject.
     The standard file is ``scripts.ema_shared.sensor_info.json`` but you can change this reference if needed (keep the structure the same though!).
      These help determine which sensors should be updated every tick, or used for head-correction etc.

## Directory Structure

The directory structure should be fairly self-explanatory:

  * The root directory holds most of the gradle files and directories used to run the package.
  * The package content is within the ``ematoblender`` subdirectory.

 Within the ``ematoblender/scripts`` directory, the ``startup`` folder holds scripts automatically launched by Blender.
 Other modules are imported as normal. They can be basically separated as follows:

 1.  ``ema_io`` handles the real-time server and gameserver's behaviour, ie all of the behaviour that deals with decoding different EMA data formats, representing them as ``DataFrame`` or ``Component`` objects, (un)packing them to/from binary, responding to commands like a WAVE would.
 2.  ``ema_shared`` handles the Blender-wide information, like properties, sensor information, persistent Blender objects, as well as game-server-level bevaviour like head-correction or smoothing.
 3.  ``ema_bge`` contains the main game loop (``bge_emareadin``) and other functionality broken out into theme-based modules.
 4.  ``ema_bpy`` contains the main building loop (``bpy_emareadin``) and other functionality broken out into theme-based modules.

The assets to be imported should (but don't have to) be in the sub-folder ``./blender_objects``, and unless the default directory is changed, ``.tsv`` outputs of the streamed data are written into the ``./output`` folder with their timestamp.

## Motivation

This project is for a Masters Thesis, aiming to create a real-time 3D visualisation of EMA data.
It is envisioned that the final project will support a symbolic representation of the tongue and lips, with future extensions adding more passive articulators and making the behaviour appear more natural.
The architecture allows for manipulations (such as delays) at the game server level that would be ideal for researching different conditions of visual feedback by manipulating the live or static data before it is visualised.
Additionally, the customisability of Blender allows for additions into the game-scene such as targets etc.


## Installation

Install Blender from the [Blender website](http://www.blender.org/download/). If you use Windows (which is necessary for interfacing with the NDI WAVE), ensure you have the 32-bit installation.
The application was developed on Blender version 2.74/5.
Blender comes with an installation of Python, but you will require an external installation in order to run the real-time server in the terminal of your choice.


In ./scripts/ema_shared/properties you should set the variable ``abspath_to_repo`` with the location of the downloaded repository. This helps Blender find the pre-made assets.
At the moment you can build a .blend file on your own, but a pre-built scene are being finalised and will be available online soon!

## Tests

Diagnostic tests still to come. In the meantime, running the server externally with some data and ``run_bpy`` within Blender should result in a working demo.

## Contributors

Kristy James (Saarland University, University of Groningen)

## License

This program is distributed under the terms of the GNU General Public License version 3.
