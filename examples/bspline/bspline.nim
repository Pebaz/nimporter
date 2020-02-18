#[
https://www.codeproject.com/Articles/25237/Bezier-Curves-Made-Simple

To get the value from a B-Spline curve, simply provide it with the value of what
percentage of the key frame is done. For example, at 50% through a key frame
anim sequence (not an animation, a key frame anim sequence between 2 frames),
the B-Spline is also 50% through it's execution.
]#

import nimpy, glm

proc bspline(): Vec3f {.exportpy.} =
    return vec3f(1, 2, 3)
