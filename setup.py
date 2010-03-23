from distutils.core import setup

setup(name='harvard_syringe_pump',
      #version='1.0',
      description="Python interface to Harvard Apparatus OEM syringe pump modules",
      author="Ben Gamari",
      author_email="bgamari@physics.umass.edu",
      url="http://goldnerlab.physics.umass.edu/wiki",
      py_modules=['pump'],
      scripts=['pump_ui.py'],
      data_files=[
              ('share/harvard_syringe_pump', ['pump_ui.glade']),
      ],
     )
