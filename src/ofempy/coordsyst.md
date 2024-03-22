# Specifiation of local coordinate systems

The FEMIX coordinate system is a right-handed Cartesian coordinate system. The x-axis is directed to the right, the y-axis is directed upwards, and the z-axis is directed out of the screen.

$v_1$ is the unit vector in the x-direction, \
$v_2$ is the unit vector in the y-direction, and \
$v_3$ is the unit vector in the z-direction.

## FEMIX coordinate system

### Bar elements

$v_1$ is the unit vector in the direction of the frame element \
$v_3$ is defined as:\
if  $v_1$ is parallel to the z-axis (0,0,1) then:\
$\qquad v_3 = v_1 \times (1,0,0)$ \
else:\
$\qquad v_3 = v_1 \times (0,1,1)$\
$v_2 = v_3 \times v_1$

### Shell elements

$v_3$ is the unit vector normal to the area element\
$v_3$ is defined as:\
if  $v_1$ is parallel to the y-axis (0,1,0) then:\
$\qquad v_1 = v_3 \times (1,0,0)$ \
else:\
$\qquad v_1 = (0,1,0) \times v_1$\
$v_2 = v_3 \times v_1$

## SAP2000 coordinate system

### Frame elements

$v_1$ is the unit vector in the direction of the frame element \
$v_3$ is defined as:\
if  $v_1$ is parallel to the z-axis (0,0,1) then:\
$\qquad v_2 = (0,1,0)$ \
else:\
$\qquad v_2 = v_1 \times (0,0,-1)$\
$v_3 = v_1 \times v_2$

### Area elements

$v_3$ is the unit vector normal to the area element\
$v_3$ is defined as:\
if  $v_3$ is parallel to the z-axis (0,0,1) then:\
$\qquad v_1 = (1,0,0)$ \
else:\
$\qquad v_1 = (0,0,1) \times v_3$\
$v_2 = v_3 \times v_1$
