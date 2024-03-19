//+
SetFactory("OpenCASCADE");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("Built-in");
//+
SetFactory("OpenCASCADE");
//+
Rectangle(1) = {0, 0, 0, 10, 5, 0};
//+
Rectangle(2) = {5, 5, 0, 2.5, 2.5, 0};
//+
Curve Loop(3) = {3, 4, 1, 2};
//+
Curve Loop(4) = {8, 5, 6, 7};
//+
Plane Surface(3) = {3, 4};
//+
Curve Loop(6) = {3, 4, 1, 2};
//+
Curve Loop(7) = {8, 5, 6, 7};
//+
Plane Surface(4) = {6, 7};
//+
Curve Loop(1) = {1};
//+
Plane Surface(1) = {1};
//+
SetFactory("OpenCASCADE");
//+
SetFactory("Built-in");
//+
SetFactory("OpenCASCADE");
//+
Rectangle(1) = {0, 0, 0, 1, 0.5, 0};
//+
Rectangle(2) = {0.2, 0.6, 0, 1, 0.5, 0};
//+
Curve Loop(3) = {3, 4, 1, 2};
//+
Curve Loop(4) = {5, 6, 7, 8};
//+
Plane Surface(3) = {3, 4};
//+
Point(1) = {-0.5, 1, 0, 1.0};
//+
Point(2) = {0.5, 2, 0, 1.0};
//+
Point(3) = {0.5, 1, 0, 1.0};
//+
Line(1) = {1, 2};
//+
Line(2) = {3, 2};
//+
Line(3) = {3, 1};
//+
Curve Loop(1) = {1, -2, 3};
//+
Plane Surface(1) = {1};
//+
SetFactory("OpenCASCADE");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("Built-in");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("OpenCASCADE");
//+
SetFactory("Built-in");
//+
Point(1) = {-1, -1, 0, 1.0};
//+
Point(2) = {0, -2, 0, 1.0};
//+
Point(3) = {-0, -1, 0, 1.0};
//+
Point(4) = {-0.8, -1.3, 0, 1.0};
//+
Line(1) = {4, 2};
//+
Line(2) = {2, 3};
//+
Line(3) = {3, 1};
//+
Line(4) = {1, 4};
//+
Line(5) = {3, 4};
//+
Curve Loop(1) = {1, 2, 5};
//+
Plane Surface(1) = {1};
//+
Curve Loop(2) = {5, -4, -3};
//+
Plane Surface(2) = {2};
//+
SetFactory("OpenCASCADE");
Sphere(1) = {-1.4, -1.7, 0, 0.5, -Pi/2, Pi/2, 2*Pi};
//+
Sphere(2) = {-2.2, -1.9, 0, 0.5, -Pi/2, Pi/2, 2*Pi};
//+
Point(2) = {-0, -0, 0, 1.0};
//+
Point(3) = {0, -1, 0, 1.0};
//+
Line(1) = {1, 2};
//+
Point(3) = {1, 1, 0, 1.0};
//+
Point(4) = {0, 1, 0, 1.0};
//+
Line(1) = {1, 2};
//+
Line(2) = {3, 4};
//+
Line(3) = {2, 3};
//+
Line(4) = {1, 4};
//+
Curve Loop(1) = {4, -2, -3, -1};
//+
Plane Surface(1) = {1};
//+
Physical Curve("sup: 111000", 5) = {3};
//+
Physical Curve("sup: 111111 fixed", 6) = {2};
//+
Physical Curve("sec: viga", 7) = {3};
//+
Physical Curve("sup: 111111 fixed", 6) += {1, 2, 3};
