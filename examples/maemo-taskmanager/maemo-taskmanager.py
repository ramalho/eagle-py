#!/usr/bin/python2.4


import os
import signal
from eagle import *

unit_map = {1: "B", 1024: "KB", 1024 ** 2: "MB", 1024 ** 3: "GB"}

def units(number):
    base = 1024
    multiplier = 1
    n = number
    while n >= base:
        n /= base
        multiplier *= base
    unit = unit_map.get(multiplier)
    if unit:
        return "%d %s" % (n, unit)
    else:
        return str(number)


class ProcessInfo(object):
    __slots__ = ("pid", "name", "state", "vmsize", "vmrss", "cpu", "old_cpu",
                 "cpu_diff", "cmdline", "priority", "nice", "n_threads",
                 "start_time")
    def __init__(self, pid):
        self.pid = pid
        self.cpu = 0
        self.vmsize = 0
        self.vmrss = 0
        self.update()


    def update(self):
        self.old_cpu = self.cpu

        try:
            f = open("/proc/%d/stat" % self.pid)
            line = f.read()
            f.close()
        except (OSError, IOError), e:
            return

        fields = line.split()

        self.name = fields[1][1 : -1] # remove "(" and ")"
        self.state = fields[2]
        self.cpu = sum([int(x) for x in fields[13 : 17]])
        self.priority = int(fields[17])
        self.nice = int(fields[18])
        self.n_threads = int(fields[19])
        self.start_time = int(fields[21])

        self.cpu_diff = self.cpu - self.old_cpu

        self.__load_cmdline__()
        self.__load_mem__()


    def __load_mem__(self):
        # get memory information from /proc/pid/status instead of stat
        # it get VmRSS right, while /proc/pid/stat doesn't :-(
        try:
            f = open("/proc/%d/status" % self.pid)
            lines = f.readlines()
            f.close()
        except (OSError, IOError), e:
            return

        for l in lines:
            if   l.startswith("VmSize"):
                self.vmsize = int(l[l.index(':') + 1 : -3]) * 1024
            elif l.startswith("VmRSS"):
                self.vmrss = int(l[l.index(':') + 1 : -3]) * 1024


    def __load_cmdline__(self):
        try:
            f = open("/proc/%d/cmdline" % self.pid)
            self.cmdline = f.read().replace('\x00', " ").strip()
            f.close()
        except (OSError, IOError), e:
            return


class System(object):
    blacklisted = ("/usr/bin/maemo-launcher",
                   "/usr/lib/sapwood/sapwood-server",
                   "/usr/bin/matchbox-window-manager",
                   "/usr/bin/hildon-input-method",
                   "/usr/bin/maemo_af_desktop",
                   "/usr/libexec/dbus-vfs-daemon",
                   "/usr/sbin/ke-recv",
                   "/usr/sbin/temp-reaper",
                   "/usr/bin/dbus-daemon-1",
                   "/usr/bin/osso-connectivity-ui-conndlgs",
                   "/usr/bin/osso-media-server",
                   "/usr/bin/clipboard-manager",
                   )
    __slots__ = ("processes", "uid", "cpu", "old_cpu", "cpu_diff",
                 "memtotal", "memfree")
    def __init__(self):
        self.uid = os.getuid()
        self.cpu = 0
        self.processes = dict()

        self.update()


    def is_blacklisted(self, process):
	cmdline = process.cmdline
	for b in self.blacklisted:
	    if cmdline.startswith(b):
		return True
	return False


    def update(self):
        self.update_global()

        pids = []
	use_blacklist = app["use_blacklist"]
        for p in os.listdir("/proc"):
            # just processes (pid numbers)
            if not p.isdigit():
                continue

	    if use_blacklist:
		# just user's processes
		try:
		    s = os.stat("/proc/%s" % p)
		except (OSError, IOError), e:
		    continue

		if s.st_uid != self.uid:
		    continue


            pid = int(p)
            pinfo = self.processes.get(pid)
            if pinfo:
		if use_blacklist and self.is_blacklisted(pinfo):
		    continue
		pinfo.update()
            else:
                pinfo = ProcessInfo(pid)
		if use_blacklist and self.is_blacklisted(pinfo):
		    continue

	    self.processes[pid] = pinfo
	    pids.append(pid)
        # end for p in os.listdir("/proc")

        # remove non-existent processes
        old_pids = self.processes.keys()
        for p in old_pids:
            if p not in pids:
                del self.processes[p]


    def update_global(self):
        self.old_cpu = self.cpu

        f = open("/proc/stat")
        line = f.readline()
        f.close()
        fields = line.split()

        self.cpu = sum([int(x) for x in fields[1 : 5]])
        self.cpu_diff = self.cpu - self.old_cpu


        f = open("/proc/meminfo")
        memtotal = f.readline()
        memfree  = f.readline()
        f.close()
        self.memtotal = int(memtotal[memtotal.index(":") + 1 : -3])
        self.memfree  = int(memfree[memfree.index(":") + 1 : -3])

        self.memtotal *= 1024
        self.memfree  *= 1024


    def cpu_usage(self, pid):
        i = self.processes.get(pid)
        if i:
            cpu_diff = self.cpu_diff or 1
            return min(i.cpu_diff * 100 / cpu_diff, 99)
        else:
            return 0


    def mem_usage(self, pid):
        i = self.processes.get(pid)
        if i:
            memtotal = self.memtotal or 1
            return min(i.vmrss * 100 / memtotal, 99)
        else:
            return 0


def kill(app, button):
    t = app["processes"]
    selected = t.selected()
    for idx, row in selected:
        pid = row[0]
        pinfo = app.system.processes.get(pid)
        if not pinfo:
            continue

        msg = "Do you really want to kill \"%s\" (%d)?" % (pinfo.name, pid)
        if confirm(msg):
            os.kill(pid, signal.SIGKILL)


def refresh(app):
    if not hasattr(app, "system"):
	# app has not loaded it's data yet, return
	return

    processes = app["processes"]
    refresh_processes(app, processes)
    refresh_info(app, app["info"], processes.selected())
    refresh_graphs(app)
    return True

states = {
    "R": "Running",
    "S": "Sleeping",
    "D": "Disk Sleep",
    "T": "Stopped",
    "Z": "Zombie",
    "X": "Dead",
    }
def refresh_info(app, table, processes_rows):
    if not processes_rows:
        return

    idx, (pid, cpu, mem, name, cmdline) = processes_rows[0]

    info = app.system.processes.get(pid)
    if not info:
        return

    table[0][1] = info.name
    table[1][1] = states.get(info.state, info.state)
    table[2][1] = units(info.vmsize)
    table[3][1] = units(info.vmrss)
    table[4][1] = info.cmdline
    table.columns_autosize()


def refresh_processes(app, table):
    system = app.system
    system.update()

    processes = system.processes

    app.cpu = cpu = dict()
    app.mem = mem = dict()
    max_cpu = 0
    max_mem = 0
    for p in processes:
        cpu[p] = c = system.cpu_usage(p)
        mem[p] = m = system.mem_usage(p)
        max_cpu = max(max_cpu, c)
        max_mem = max(max_mem, m)

    app.max_cpu = max_cpu
    app.max_mem = max_mem

    remove = []
    update = []

    # Update already existent
    for idx, (pid, c, m, name, cmdline) in enumerate(table):
        info = processes.get(pid)
        if not info:
            remove.append(idx)
            continue

        update.append(pid)
        table[idx][1] = cpu[pid]
        table[idx][2] = mem[pid]


    # Append new processes
    handled = remove + update
    for pid, info in processes.iteritems():
        if pid not in handled:
            table.append((pid,
                          cpu[pid],
                          mem[pid],
                          info.name,
                          info.cmdline,
                          ),
                         select=False)

    # Remove non-existent process
    remove.sort(reverse=True)
    for idx in remove:
        del table[idx]

    table.columns_autosize()


def draw_graph(canvas, samples, color):
    x = 0
    width = canvas.width / (len(samples) - 1)
    points = []
    base_height = canvas.height
    for height in samples:
        y = base_height - height
        points.append((x, y))
        x += width

    points += [(canvas.width, canvas.height - samples[-1]),
               (canvas.width, canvas.height),
               (0, canvas.height),
               (0, canvas.height - samples[0])]

    canvas.draw_polygon(points, color=color, size=0, fillcolor=color,
                        filled=True)


class Samples(object):
    def __init__(self, n_samples):
        self.samples = [0] * n_samples
        self.index = 0


    def append(self, value):
        if self.index >= len(self.samples):
            # Discard value as needed
            diff = self.index - len(self.samples) + 1
            self.samples = self.samples[diff :] + ([0] * diff)
            self.index -= diff

        self.samples[self.index] = value
        self.index += 1


    def __len__(self):
        return len(self.samples)


    def __getitem__(self, index):
        return self.samples[index]


    def __setitem__(self, index, value):
        self.samples[index] = value


def refresh_graph_cpu_load(app, canvas):
    # calculate current value
    used = sum(p.cpu_diff for p in app.system.processes.itervalues())
    used_scale = float(used) / float(app.system.cpu_diff or 1)
    used_height = int(used_scale * canvas.height)

    # Remember new value
    refresh_graph_cpu_load.samples.append(used_height)

    try:
        canvas.clear()
    except AttributeError, e:
        # Canvas may not be ready yet
        return

    # Draw it
    draw_graph(canvas, refresh_graph_cpu_load.samples, "red")
refresh_graph_cpu_load.samples = Samples(30)


def refresh_graph_memory_load(app, canvas):
    # calculate current value
    used = app.system.memtotal - app.system.memfree
    used_scale = float(used) / float(app.system.memtotal or 1)
    used_height = int(used_scale * canvas.height)

    # Remember new value
    refresh_graph_memory_load.samples.append(used_height)

    try:
        canvas.clear()
    except AttributeError, e:
        # Canvas may not be ready yet
        return

    # Draw it
    draw_graph(canvas, refresh_graph_memory_load.samples, "red")
refresh_graph_memory_load.samples = Samples(30)


def refresh_graphs(app):
    refresh_graph_cpu_load(app, app["cpu_load"])
    refresh_graph_memory_load(app, app["memory_load"])


def refresh_rate_changed(app, entry, value):
    try:
        id = app.refresh_id
    except AttributeError:
        pass
    else:
        app.remove_event_source(id)

    app.refresh_id = app.timeout_add(value * 1000, refresh)


def blacklist_changed(app, entry, value):
    refresh(app)


def show_info_changed(app, entry, is_show):
    info = app["info"]
    if is_show:
	info.show()
    else:
	info.hide()



def selected_process(app, info_table, rows):
    refresh_info(app, app["info"], rows)


def process_format(app, table, row, col, value):
    if col == 1 and value == app.max_cpu:
        return Table.CellFormat(bold=True, fgcolor="red")
    elif col == 2 and value == app.max_mem:
        return Table.CellFormat(bold=True, fgcolor="red")


processes_widgets = (
    Table(id="processes",
          label="Processes",
          headers=("ID", "C%", "M%", "Name", "Command Line"),
          types=(int, int, int, str, str),
          selection_callback=selected_process,
          cell_format_func=process_format,
          ),
    Table(id="info",
          label="Process Information",
          headers=("Property", "Value"),
          show_headers=False,
          types=(str, str),
          items=(("Name", ""),
                 ("State", ""),
                 ("Total Memory", ""),
                 ("Resident Memory", ""),
                 ("Command Line", ""),
                 ),
          ),
    Group(id="actions",
          border=None,
          horizontal=True,
          children=(Button(id="kill",
                           label="Kill Selected",
                           callback=kill,
                           ),
                    CheckBox(id="show-info",
                             label="Show process information",
                             value=True,
                             callback=show_info_changed,
                             ),
                    ),
          )
    )

statistics_widgets = (
    Group(id="statistics_graphs",
          horizontal=True,
          border=None,
          children=(Canvas(id="cpu_load",
                           label="Processor Load",
                           width=320,
                           height=200,
                           scrollbars=False,
                           ),
                    Canvas(id="memory_load",
                           label="Memory Load",
                           width=320,
                           height=200,
                           scrollbars=False,
                           ),
                    ),
          ),
    )



app = App(title="Task Manager",
          version="1.0",
          license="GPL",
          copyright="2006 - Gustavo Sverzut Barbieri, under GPL",
          author="Gustavo Sverzut Barbieri &lt;barbieri@gmail.com&gt;",
          description="""\
<i>Simple Task Manager for Maemo.</i>
<p>
This software allows you to monitor processes and their
resource usage.
</p>
""",
          help="""\
<p>
At top you can see the process list, with process identification number (PID),
CPU usage (C%), memory usage (M%), name and command line.
</p><p>
If <b>"Show process info"</b> is selected, a second table will show information
about the selected process (or the first selected process, if multiple).
</p><p>
If you want to finish some process, select it and click <b>"Kill Selected"</b>.
</p><p>
Use <b>"Preferences"</b> menu to change refresh rate and also disable use of
blacklist (that avoid show system process). However notice that if you show
every process it may slow down the system!
</p>
""",
          preferences=(UIntSpin(id="refresh-rate",
                                label="Refresh Rate (secs)",
                                value=5,
                                callback=refresh_rate_changed,
                                ),
                       CheckBox(id="use_blacklist",
                                label="Filter system process",
                                value=True,
                                callback=blacklist_changed,
                                ),
                       ),
          center=Tabs(id="tabs",
                      children=(Tabs.Page(id="page_processes",
                                          label="Processes",
                                          children=processes_widgets,
                                          ),
                                Tabs.Page(id="page_stats",
                                          label="Statistics",
                                          children=statistics_widgets,
                                          ),
                                ),
                      )
          )
app.system = System()
refresh(app)

app.refresh_id = app.timeout_add(app["refresh-rate"] * 1000, refresh)


run()
