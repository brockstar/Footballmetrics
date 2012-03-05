The Pythagoreans module
=======================

This module is a Python implementation of the Pythagorean expectation,
originally developed by Bill James for application in baseball.
The formula predicts how often a team *should* have won, based on their own
points and their opponents points:

.. math::
	\mathrm{Wins} = \frac{\mathrm{PF}^x}{\mathrm{PF}^x + \mathrm{PA}^x}
	
:math:`\mathrm{PF}` notates the own points scored (*points for*) and :math:`\mathrm{PA}` notates the points scored
by the opposing team (*points against*).


Classes
--------

The Pythagoreans module contains the following classes:

.. toctree::
	:maxdepth: 2
	
	PythagoreanClass.rst
		
	PythagoreanExpectationClass.rst
	PythagenportClass.rst
	PythagenpatClass.rst