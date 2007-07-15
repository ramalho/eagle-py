#!/usr/bin/python

from eagle import *
import urllib
import sys
import os
import shlex
import threading
from subprocess import Popen
import logging as log

BATCH_SIZE = 10

try:
    from xml.etree import ElementTree
except ImportError:
    try:
        from cElementTree import ElementTree
    except ImportError:
        from elementtree import ElementTree

def menu_quit(app, item):
    quit()


def menu_preferences(app, item):
    app.show_preferences_dialog()


def menu_about(app, item):
    app.show_about_dialog()


def menu_help(app, item):
    app.show_help_dialog()


def fetch_channel_list(app, *a):
    url = app["channel_list"]
    f =  urllib.urlopen(url)
    return f


def process_channel_list(xml):
    channels = ElementTree().parse(xml)
    return channels


def node_name(node):
    return node.attrib["en"].strip() or node.text.strip()


def show_group(app, group):
    if group:
        group_name = group.attrib["en"].strip() or group.text.strip()
        channel_list = group.findall("./channel")
    else:
        group_name = "All"
        channel_list = app.xml.findall(".//channel")

    sid = app.status_message("List channels from group %s" % group_name)
    tab_channels = app["channels"]
    tab_channels.set_label("Channels from group '%s'" % group_name)
    tab_channels.clear()
    app.processing_channels = True

    def process_channel_batch(app, index):
        for channel in channel_list[index: index + BATCH_SIZE]:
            name = node_name(channel.find("./name"))
            cls = node_name(channel.find("./class"))
            region = node_name(channel.find("./region"))
            users = int(channel.findtext("./user_count"))
            bandwidth = int(channel.findtext("./kbps"))
            url = channel.findtext("./sop_address/item")
            tab_channels.append((name, cls, region, users, bandwidth, url),
                                select=False, autosize=False)

        index += BATCH_SIZE
        if index < len(channel_list):
            app.idle_add(process_channel_batch, index)
        else:
            app.processing_channels = False
            app.remove_status_message(sid)
            tab_channels.columns_autosize()
        return False
    process_channel_batch(app, 0)


def refresh_channel_list(app, *a):
    sid = app.status_message("Fetch and process channel list...")
    def fetch_and_process():
        try:
            xml = process_channel_list(fetch_channel_list(app))
            app.idle_add(process_fetched_list, xml, sid)
        except (IOError, OSError), e:
            def show_error(app):
                app.remove_status_message(sid)
                error("Could not download channel list\n%s" % e)
                return False
            app.idle_add(show_error)
            log.error("Could not fetch and process URL %s" % e)

    t = threading.Thread(target=fetch_and_process)
    t.start()


def process_fetched_list(app, xml, status_msg_id):
    app.remove_status_message(status_msg_id)
    app.xml = xml

    tab_group = app["groups"]
    tab_channels = app["channels"]

    tab_group.clear()
    tab_channels.clear()

    sid = app.status_message("List groups...")
    tab_group.append(("All", "All channels", None))
    group_list = xml.findall(".//group")
    app.processing_groups = True

    def process_group_batch(app, index):
        for group in group_list[index: index + BATCH_SIZE]:
            name = node_name(group)
            tab_group.append((name, group.attrib["description"], group),
                             select=False, autosize=False)

        index += BATCH_SIZE
        if index < len(group_list):
            app.idle_add(process_group_batch, index)
        else:
            app.processing_groups = False
            app.remove_status_message(sid)
            tab_group.columns_autosize()
            if len(tab_group) > 0:
                show_group(app, tab_group[0][2])
        return False

    process_group_batch(app, 0)


def group_selected(app, tab_group, contents):
    if app.processing_groups:
        return
    if not contents:
        return
    index, row = contents[0]
    show_group(app, row[2])


def channel_selected(app, tab_channels, contents):
    if app.processing_channels:
        return
    if not contents:
        app["play_button"].disable()
        return
    index, row = contents[0]
    app["play_button"].enable()


def list_replace_or_append(lst, old, new):
    i = lst.index(old)
    if i < 0:
        lst.append(new)
    else:
        lst[i] = new


def check_processes_running(app):
    if not app.player or not app.spsc:
        stop_channel(app)
        return False

    if app.player.poll() != None:
        log.warning("Player process died with code %d" %
                    app.player.returncode)
        start_player(app)

    if app.spsc.poll() != None:
        log.warning("SP-SC process died with code %d" %
                    app.spsc.returncode)
        stop_channel(app)
        return False

    return True

def start_player(app):
    cmd = shlex.split(app["player_cmd"])
    list_replace_or_append(cmd, "@url",
                           "http://localhost:%d/" % app["video_port"])
    log.debug("Player: %s" % " ".join(cmd))
    player = Popen(cmd)
    app.player = player


def delayed_start_player(app, channel_name):
    start_player(app)
    app.timeout_add(1000, check_processes_running)
    app["play_button"].disable()
    app["stop_button"].enable()
    app["now_playing"] = "Playing channel %s" % channel_name
    return False


def play_channel(app, button):
    tab_channels = app["channels"]
    selected = tab_channels.selected()
    if not selected:
        return
    idx, row = selected[0]
    channel_url = row[5]

    stop_channel(app)

    cmd = shlex.split(app["spsc_cmd"])
    list_replace_or_append(cmd, "@url", channel_url)
    list_replace_or_append(cmd, "@local_port", str(app["local_port"]))
    list_replace_or_append(cmd, "@video_port", str(app["video_port"]))
    log.debug("SP-SC: %s" % " ".join(cmd))
    spsc = Popen(cmd)
    app.spsc = spsc

    if spsc.returncode != None:
        log.error("SP-SC returned with code %d" % spsc.returncode)
        stop_channel(app)
        return

    app.timeout_add(5000, delayed_start_player, row[0])


def stop_channel(app, *a):
    if app.player:
        try:
            os.kill(app.player.pid, 15)
        except OSError, e:
            log.warning("Could not kill player (pid=%d): %s" %
                        (app.player.pid, e))
        app.player = None

    if app.spsc:
        try:
            os.kill(app.spsc.pid, 15)
        except OSError, e:
            log.warning("Could not kill sp-sc (pid=%d): %s" %
                        (app.spsc.pid, e))
        app.spsc = None

    app["now_playing"] = ""
    app["stop_button"].disable()


app = App(title="SopCast - Peer-to-Peer TV!",
          author="Gustavo Sverzut Barbieri",
          description="""\
<p>SopCast is a simple, free way to broadcast video and audio or watch
the video and listen to radio on the Internet. Adopting P2P(Peer-to-Peer)
technology, It is very efficient and easy to use. Let anyone become a
broadcaster without the costs of a powerful server and vast bandwidth.</p>

<p><a href="http://www.sopcast.org/">http://www.sopcast.org/</a></p>

<p>This is a simple frontend for the UNIX command line tool "sp-sc"
provided at their <a href="http://www.sopcast.org/download/">website</a>,
it allows you to browse channel list and launch your favorite player to
watch the stream.</p>
""",
          help="""\
<p>In order to this application work, you need sp-sc (or sp-sc-auth) at
least version 1.1.1, which can be downloaded at
<a href="http://www.sopcast.org/download/">http://www.sopcast.org/download/</a>.</p>

<p>At the top is the <b>"Groups"</b> table, with every existent group of
channels, including <b>All</b>, which will list all categories.</p>

<p>Right below <b>"Groups"</b> you'll find <b>"Channels"</b> for the
selected group.</p>

<p>Both lists can be re-ordered by clicking column header, but you can
also search for terms in the first column just typing when the widget
has the focus, a little box on the right-bottom corner will show current
search phrase.</p>

<p>When channels are selected, <b>Play</b> button will be enabled,
clicking it will start "sp-sc" utility to communicate with p2p-network
and provide a stream at http://localhost:<p>video_port</b>, also
launching configured video player on this URL.</p>

<p>Clicking on <b>Stop</b> will kill both "sp-sc" and player.</p>
""",
          statusbar=True,
          preferences=(UIntSpin(id="local_port",
                               label="Local Port",
                               value=9000),
                       UIntSpin(id="video_port",
                                label="Video Port",
                                value=9001),
                       Entry(id="channel_list",
                             label="Channel List",
                             value="http://www.sopcast.com/chlist.xml",
                             ),
                       Entry(id="spsc_cmd",
                             label="Sp-sc command",
                             value="/usr/bin/sp-sc-auth @url @local_port @video_port",
                             ),
                       Entry(id="player_cmd",
                             label="Player command",
                             value="/usr/bin/mplayer @url",
                             ),
                       ),
          menu=(Menu.Submenu(label="File",
                             subitems=(Menu.Item(label="Quit",
                                                 callback=menu_quit),
                                       ),
                             ),
                Menu.Submenu(label="Edit",
                             subitems=(Menu.Item(label="Preferences",
                                                 callback=menu_preferences),
                                       ),
                             ),
                Menu.Submenu(label="Help",
                             subitems=(Menu.Item(label="Help",
                                                 callback=menu_help),
                                       Menu.Item(label="About",
                                                 callback=menu_about),
                                       ),
                             )
                ),
          center=(Table(id="groups",
                        label="Groups",
                        types=(str, str, object),
                        headers=("Name", "Description", "Object"),
                        hidden_columns_indexes=2,
                        expand_columns_indexes=1,
                        selection_callback=group_selected,
                        ),

                  Table(id="channels",
                        label="Channels from Group",
                        types=(str, str, str, int, int, str),
                        headers=("Name", "Class", "Region", "Users", "Bandwidth", "address"),
                        hidden_columns_indexes=5,
                        expand_columns_indexes=0,
                        selection_callback=channel_selected,
                        ),
                  ),
          bottom=(Button(id="refresh",
                         stock="refresh",
                         callback=refresh_channel_list,
                         ),
                  VSeparator(),
                  Button(id="play_button",
                         stock="media:play",
                         callback=play_channel,
                         ),
                  Button(id="stop_button",
                         stock="media:stop",
                         callback=stop_channel,
                         ),
                  Label(id="now_playing",
                        label="",
                        ),
                  ),
          )
app.xml = None
app.spsc = None
app.player = None
app.processing_groups = False
app.processing_channels = False
app["play_button"].disable()
app["stop_button"].disable()
app.idle_add(refresh_channel_list)

log.basicConfig(level=log.DEBUG,
                format='%(asctime)s %(levelname)s: %(message)s')

run()

stop_channel(app)
