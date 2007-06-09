#!/usr/bin/python

# Copyright 2007 Nilton Volpato <nilton dot volpato | gmail com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Reference:
# Adaptive Sampling of Parametric Curves
# Luiz Henrique de Figueiredo
# Graphic Gems V, page 173
# Academic Press 1995

import math
import random
import os

AUTO = 0
ALL  = 1


class Stats(object):
    def __init__(self, points):
        self.n = len(points)
        xlist = [ p.x for p in points ];
        self.xmin = min(xlist)
        self.xmax = max(xlist)

        ylist = [ p.y for p in points ]
        ylist.sort()
        self.q1_y = self.quartile(ylist, 1)
        self.q2_y = self.quartile(ylist, 2)
        self.q3_y = self.quartile(ylist, 3)
        self.iqr_y = self.q3_y - self.q1_y

        self.mild_min_y = self.q1_y - 1.5 * self.iqr_y
        self.mild_max_y = self.q3_y + 1.5 * self.iqr_y
        self.extreme_min_y = self.q1_y - 3.0 * self.iqr_y
        self.extreme_max_y = self.q3_y + 3.0 * self.iqr_y

        self.ymin = ylist[0]
        self.ymax = ylist[-1]

    def bbox(self):
        return self.xmax, self.xmin, self.ymax, self.ymin

    def bbox_auto(self, points):
        ymin = self.ymax
        ymax = self.ymin
        for p in points:
            if not self.is_extreme_outlier(p):
                ymin = min(ymin, p.y)
                ymax = max(ymax, p.y)
        return self.xmax, self.xmin, ymax, ymin

    def is_mild_outlier(self, p):
        return p.y < self.mild_min_y or p.y > self.mild_max_y

    def is_extreme_outlier(self, p):
        return p.y < self.extreme_min_y or p.y > self.extreme_max_y

    def quartile(self, lst, q):
        assert 1 <= q <= 3
        idx = self.n * q / 4.0
        is_int = (idx == int(idx))
        idx = int(idx)
        if is_int:
            return (lst[idx - 1] + lst[idx]) / 2.0
        else:
            return lst[idx]


class Point(object):
    __slots__ = ('t','x','y')
    def __init__(self, t, x, y):
        self.t = t
        self.x = x
        self.y = y

    def __repr__(self):
        return '<%s %s at 0x%x>' % (self.__class__.__name__,str(self),id(self))

    def __str__(self):
        return '%g:(%g,%g)' % (self.t, self.x, self.y)


class AdaptiveSampling(object):
    def __init__(self, tolerance=0.0000001, max_recursion=15):
        self.tol = tolerance
        self.maxrec = max_recursion

    def line(self, p, q):
        raise NotImplementedError('Abstract method')

    def sample(self, p, q, level=0):
        if level > self.maxrec: return
        s = 0.45 + 0.1 * random.random()
        t = p.t + s * (q.t - p.t)
        r = Point(t, *self.f(t))
        if level and self.flat(p, q, r):
            self.line(p, q)
        else:
            self.sample(p, r, level + 1)
            self.sample(r, q, level + 1)

    def flat(self, p, q, r):
        xp = p.x - r.x
        yp = p.y-r.y
        xq = q.x - r.x
        yq = q.y-r.y
        return (xp * yq - xq * yp) ** 2 < self.tol

    def adaptive_sampling(self, fun, a, b):
        self.f = fun
        p = Point(a, *fun(a))
        q = Point(b, *fun(b))
        self.sample(p, q)


class ASPointList(AdaptiveSampling):
    def adaptive_sampling(self, fun, a, b):
        self.points = []
        AdaptiveSampling.adaptive_sampling(self, fun, a, b)
        return self.points

    def line(self, p, q):
        if not self.points:
            self.points.append(p)
        self.points.append(q)


class ASPlotter(ASPointList):
    def __init__(self, plot_range=AUTO, default_width=15.,
                 aspect_ratio=0.618034, **kwargs):
        ASPointList.__init__(self, **kwargs)
        self.plot_range = plot_range
        self.default_width = default_width
        self.aspect_ratio = aspect_ratio

    def pyx_plotter(self):
        from pyx import canvas, path, color

        st = Stats(self.points)

        if self.plot_range == AUTO:
            xmax, xmin, ymax, ymin = st.bbox_auto(self.points)
        else:
            xmax, xmin, ymax, ymin = st.bbox()
        wd, ht = xmax - xmin, ymax - ymin

        sx = self.default_width / wd
        sy = self.aspect_ratio * self.default_width / ht
        #print 'WD:', wd, 'HT:', ht, sx, sy

        clip = canvas.clip(path.rect(sx * xmin, sy * ymin, sx * wd, sy * ht) )

        c = canvas.canvas([clip])
        #c.stroke(path.rect(sx*xmin, sy*ymin, sx*wd, sy*ht))

        pth = path.path()
        first_point = True

        for p in self.points:
            if first_point:
                pth.append(path.moveto(sx * p.x, sy * p.y))
                first_point = False
            else:
                pth.append(path.lineto(sx * p.x, sy * p.y))

        c.stroke(pth)

        for p in self.points:
            if st.is_extreme_outlier(p):
                c.fill(path.circle(sx * p.x, sy * p.y, 0.03), [color.rgb.red])
            else:
                c.fill(path.circle(sx * p.x, sy * p.y, 0.03))
        return c

    def write_eps(self, filename):
        c = self.pyx_plotter()
        c.writeEPSfile(filename)

    def write_pdf(self, filename):
        c = self.pyx_plotter()
        c.writePDFfile(filename)

    def write_to_file(self, filename):
        c = self.pyx_plotter()
        c.writetofile(filename)


if __name__ == '__main__':
    cases = [
        (lambda t: (5 * math.sin(t), 5 * math.cos(t)), 0., 2 * math.pi),
        (lambda t: (t, (t - 1) * (t - 3) * (t - 4)), 0.5, 4.5),
        (lambda t: (t, 1 / t), -1.0, 1.0),
        (lambda t: (5 * t, 5 * math.sin(1 / t)), -2.0, 2.0),
        (lambda t: (5 * math.cos(5 * t), 5 * math.sin(3 * t)), 0, 2 * math.pi),
        (lambda t: (t, t), -10, 10),
        (lambda t: (t, 3 ** (-t ** 2)), -5, 5),
        (lambda t: (t, math.exp(t)), -1, 5),
        (lambda t: ((1 + math.sin(5.0 * t) / 5.0) * math.cos(t),
                    (1 + math.sin(5.0 * t) / 5.0) * math.sin(t)), 0,
                    2 * math.pi),
        ]
    for i, c in enumerate(cases):
        p = ASPlotter()
        p.adaptive_sampling(*c)
        p.write_eps('plot_test%s' % i)
        os.system('gv plot_test%s.eps' % i)
