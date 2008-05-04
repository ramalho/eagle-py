#!/usr/bin/env python2

import setup

import sys
import shutil
import os
import time

site_packages = "usr/lib/python%s/site-packages" % sys.version[:3]
version = setup.__version__ + "maemo"



def mkdir(dirname):
    if not os.path.exists(dirname):
        mkdir(os.path.dirname(dirname))
        os.mkdir(dirname)

blacklist_start = ["."]
blacklist_end   = ["~"]

def recursive_files(directory, prefix=""):
    r = []
    for f in os.listdir(directory):
        dpath = directory + "/"
        dstdir = prefix + "/" + dpath

        fp = dpath + f

        for b in blacklist_start:
            if f.startswith(b):
                break
        else:
            for b in blacklist_end:
                if f.endswith(b):
                    break
            else:
                if os.path.isdir(fp):
                    r.extend(recursive_files(fp, prefix))
                else:
                    r.append((fp, dstdir + f))
    return r

def package(name, files, deps):
    tmpdir = "/tmp/%s-%d" % (sys.argv[0], time.time())

    mkdir(tmpdir)
    for src, dst in files:
        d = tmpdir + "/" + dst
        mkdir(os.path.dirname(d))
        shutil.copyfile(src, d)


    f = os.popen("du -sc %s" % tmpdir)
    c = f.readlines()
    f.close()
    c = c[-1]
    c = c.split()
    size = int(c[0])


    desc = ' '.join(setup.__description__.split('\n'))
    longdesc = setup.__long_description__.split('\n')
    for i, l in enumerate(longdesc):
        if l.strip():
            longdesc[i] = " " + l
        elif i < len(longdesc) - 1:
            longdesc[i] = " ."
    longdesc = '\n'.join(longdesc)

    values = {
        "name": name,
        "version": version,
        "size": size,
        "maintainer": setup.__author__,
        "maintainer_email": setup.__author_email__,
        "desc": desc,
        "longdesc": longdesc,
        "deps": ", ".join(list(deps or [])),
        }

    f = open("control", "w")
    f.write("""\
Package: %(name)s
Source: python-eagle
Version: %(version)s
Section: python
Priority: optional
Architecture: all
Depends: %(deps)s
Installed-Size: %(size)d
Maintainer: %(maintainer)s <%(maintainer_email)s>
Description: %(desc)s
%(longdesc)s
""" % values)
    f.close()

    f = open("debian-binary", "w")
    f.write("2.0\n")
    f.close()

    debfile = "python-%s_%s.deb" % (name, version)

    try:
        os.remove(debfile)
    except OSError:
        pass

    cwd = os.getcwd()
    os.chdir(tmpdir)
    os.system("tar czf %s/data.tar.gz *" % cwd)
    os.chdir(cwd)
    os.system("tar czf control.tar.gz control")
    os.system("ar q %s debian-binary control.tar.gz data.tar.gz" % debfile)

    for f in ("control.tar.gz", "data.tar.gz", "debian-binary"):
        os.remove(f)

    os.system("rm -fr %s" % tmpdir)


package("eagle",
         (("maemo/eagle.pyo", site_packages + "/eagle.pyo"),
           ),
         ("python2.4-gtk2", "python2.4-hildon")
         )

usr_share = "usr/share/doc/python-%s_%s/" % ("eagle-doc", version)
package("eagle-doc",
         recursive_files("docs", usr_share) +
         recursive_files("tests", usr_share) +
         recursive_files("examples", usr_share) +
         recursive_files("maemo/share/", usr_share),
         ("python-eagle",)
         )
