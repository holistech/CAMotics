#!/usr/bin/env python3
#
# Extrahiert deterministische Kennzahlen aus einer STL-Datei (ASCII oder Binär).
#
# Zweck: Simulationsergebnisse von CAMotics (camsim) reproduzierbar testen, ohne
# die rohe STL byteweise zu vergleichen. Die Facetten-REIHENFOLGE variiert je nach
# Thread-Partitionierung; die hier berechneten Kennzahlen sind ordnungs- und
# (durch Rundung) FP-rausch-unabhaengig:
#
#   - facets:  Anzahl der Dreiecke
#   - bbox:    Bounding-Box (min/max je Achse), gerundet
#   - volume:  geschlossenes, vorzeichenbehaftetes Volumen (Summe der Tetraeder
#              zum Ursprung), gerundet
#   - area:    Gesamt-Oberflaeche, gerundet
#
# Aufruf: stl-metrics.py <datei.stl> [nachkommastellen]
#
import sys
import struct


def read_ascii(path):
    tris = []
    with open(path, 'r', errors='replace') as f:
        verts = []
        for line in f:
            line = line.strip()
            if line.startswith('vertex'):
                _, x, y, z = line.split()
                verts.append((float(x), float(y), float(z)))
                if len(verts) == 3:
                    tris.append(tuple(verts))
                    verts = []
    return tris


def read_binary(path):
    tris = []
    with open(path, 'rb') as f:
        f.read(80)                       # Header
        (count,) = struct.unpack('<I', f.read(4))
        for _ in range(count):
            data = f.read(50)            # 12 floats + 2 byte attribute
            if len(data) < 50:
                break
            vals = struct.unpack('<12f', data[:48])
            v1 = (vals[3], vals[4], vals[5])
            v2 = (vals[6], vals[7], vals[8])
            v3 = (vals[9], vals[10], vals[11])
            tris.append((v1, v2, v3))
    return tris


def is_ascii_stl(path):
    with open(path, 'rb') as f:
        head = f.read(5)
    return head == b'solid'


def signed_volume(a, b, c):
    # Vorzeichenbehaftetes Volumen des Tetraeders (Ursprung, a, b, c) * 6
    return (a[0]*(b[1]*c[2] - b[2]*c[1])
            - a[1]*(b[0]*c[2] - b[2]*c[0])
            + a[2]*(b[0]*c[1] - b[1]*c[0]))


def tri_area(a, b, c):
    ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
    vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
    cx = uy*vz - uz*vy
    cy = uz*vx - ux*vz
    cz = ux*vy - uy*vx
    return 0.5 * (cx*cx + cy*cy + cz*cz) ** 0.5


def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: stl-metrics.py <file.stl> [decimals]\n')
        return 2

    path = sys.argv[1]
    decimals = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    tris = read_ascii(path) if is_ascii_stl(path) else read_binary(path)

    n = len(tris)
    if n == 0:
        print('facets: 0')
        print('bbox: empty')
        print('volume: 0')
        print('area: 0')
        return 0

    vol6 = 0.0
    area = 0.0
    minv = [float('inf')] * 3
    maxv = [float('-inf')] * 3
    for a, b, c in tris:
        vol6 += signed_volume(a, b, c)
        area += tri_area(a, b, c)
        for v in (a, b, c):
            for i in range(3):
                if v[i] < minv[i]:
                    minv[i] = v[i]
                if v[i] > maxv[i]:
                    maxv[i] = v[i]

    volume = abs(vol6) / 6.0

    def r(x):
        return round(x, decimals)

    print('facets: %d' % n)
    print('bbox: [%s %s %s] [%s %s %s]' % (
        r(minv[0]), r(minv[1]), r(minv[2]),
        r(maxv[0]), r(maxv[1]), r(maxv[2])))
    print('volume: %s' % r(volume))
    print('area: %s' % r(area))
    return 0


if __name__ == '__main__':
    sys.exit(main())
