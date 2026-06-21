# Regression test for K-2 (PyPtr copy ctor) and L-2 (PyJSON refcount leaks).
# A double DECREF / refcount underflow would crash these loops.
# Repeatedly triggers the toJSON paths (dict/list/nested).
import camotics, gc

gcode = "G21 G90\nG0 X0 Y0 Z0\nG1 X10 F100\nG1 Y10\nM2\n"
config = {
    "default-units": "metric",
    "max-vel": [1000, 1000, 500, 0, 0, 0, 0, 0, 0],
    "max-accel": [100000] * 9,
    "max-jerk": [50000000] * 9,
    "junction-accel": 200000,
    "nested": {"a": [1, 2, 3], "b": {"c": "deep"}},
}

for i in range(500):
    p = camotics.Planner()
    p.load_string(gcode, config)
    while p.has_more():
        p.next()
    del p

gc.collect()
print("OK")
