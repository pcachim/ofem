# EurocodePy

EurocodePy is a Python package for calculating structures according to Eurocodes. It provides a collection of functions that enable engineers to design and analyze structures based on the Eurocode standards. In addition, it includes a database of materials commonly used in construction, which can be easily accessed and used in calculations.

EurocodePy is a Python package that provides a collection of functions for the calculation of structures using the Eurocodes. It includes a database of structural materials and steel profiles, making it easy to design and analyze structures according to Eurocode standards.

Here are some guide questions that will help you out:

What was your motivation? \
Why did you build this project? \
What problem does it solve? \
What did you learn? \
What makes your project stand out? \
If your project has a lot of features, consider adding a "Features" section and listing them here.

What your application does, \
Why you used the technologies you used, \
Some of the challenges you faced and features you hope to implement in the future.

## EurocodesCalc

EurocodesCalc is a Python package that provides a set of tools for the calculation and design of structures according to the Eurocodes. The package includes modules for structural analysis, steel design, concrete design, timber design, and geotechnical design.

In addition, EurocodesCalc comes with a built-in database of materials and steel profiles commonly used in construction, allowing you to easily select and specify the appropriate materials and profiles for your design.

## Installation

You can install EurocodePy using pip by running the following command::

pip install eurocodepy\

## Usage

EurocodePy provides a range of functions for designing and analyzing structures according to Eurocodes. Here are some examples:

from eurocodepy import ec2

## Calculate the resistance of a concrete section according to Eurocode 2
resistance = ec2.concrete_section_resistance(fck=30, b=0.2, h=0.4, d=0.35, fyk=500)

## Calculate the shear capacity of a reinforced concrete beam according to Eurocode 2
shear_capacity = ec2.shear_capacity_beam(b=0.3, d=0.4, as_=0.01, fck=30, fyk=500, vEd=50)

## Calculate the bending moment capacity of a reinforced concrete beam according to Eurocode 2
moment_capacity = ec2.bending_moment_capacity_beam(b=0.3, d=0.4, as_=0.01, fck=30, fyk=500)
In addition to the Eurocode 2 functions shown above, EurocodePy includes functions for Eurocodes 0, 1, 3, 4, 5, 6, 7, 8, 9, and EN 1992-1-1.

EurocodePy also includes a database of materials, which can be used in calculations. Here's an example:


from eurocodepy.materials import Material

# Create a material object for concrete
concrete = Material(name="C30/37", fck=30, fck_cube=37, fctm=2.6, Ecm=31000, G=11500)

# Create a material object for steel
steel = Material(name="S500", fyk=500, fuk=630, E=200000, G=77000)

# Use the concrete object in a Eurocode 2 calculation
resistance = ec2.concrete_section_resistance(b=0.2, h=0.4, d=0.35, material=concrete, gamma_c=1.5)

# Use the steel object in a Eurocode 3 calculation
section_class = ec3.section_classification(h=0.3, b=0.2, t=0.01, material=steel)
Contributing

Contributions are welcome! Please see the contributing guidelines for more information.

## Materials and Profiles Database

EurocodePy includes a database of structural materials and steel profiles. The database is stored in a CSV file and can be easily updated or extended. The materials database includes properties such as the density, modulus of elasticity, and Poisson's ratio, while the steel profiles database includes properties such as the cross-sectional area, moment of inertia, and section modulus.

## License

EurocodePy is licensed under the MIT License.

## Usage 2

EurocodePy is designed to be easy to use. Simply import the package and start using the functions. Here's an example of how to calculate the bending resistance of a steel beam:

```python
import eurocodepy as ec

beam = ec.SteelBeam('HEA200')
beam.check_bending_capacity(M=1000)
```

## Usage 3

Once installed, you can import EurocodesCalc modules and use them in your Python scripts or Jupyter notebooks. For example, to perform a structural analysis, you can import the `structural` module and use its functions to calculate the reactions, shear forces, and bending moments of a beam:

```python
from eurocodescalc import structural

L = 5  # length of beam in meters
q = 10  # uniform load in kN/m

reaction, shear, moment = structural.beam(L, q)

print(f"Reaction at support: {reaction:.2f} kN")
print(f"Maximum shear force: {max(shear):.2f} kN")
print(f"Maximum bending moment: {max(moment):.2f} kNm")
```

Make sure to save the file with the extension ".md" to ensure that it is recognized as a Markdown file.
