#!/usr/bin/python
# vim: set fileencoding=UTF-8 :

import gtk, glib
import pump

class PumpWindow(object):
        def __init__(self, port=0):
                self.pump = pump.Pump(port)

                self.builder = gtk.Builder()
                self.builder.add_from_file("pump.glade")
                self.builder.connect_signals(self)

                self.win = self.builder.get_object("main_window")
                self.win.connect('destroy', gtk.main_quit)
                self.range_store = self.builder.get_object('range_store')
                self.win.show_all()

                self.update_units()
                self.poll_status()
                diam = self.pump.get_diameter()
                self.builder.get_object('diameter').set_value(diam)
                rate = self.pump.get_flow_rate()
                self.builder.get_object('flow_rate').set_value(rate)

                glib.timeout_add_seconds(2, self.poll_status)

        def poll_status(self):
                messages = {
                        'running': ('gtk-forward', 'Running'),
                        'reverse': ('gtk-back', 'Running Reverse'),
                        'stalled': ('gtk-no', 'Stalled'),
                        'stopped': ('gtk-stop', 'Stopped') 
                }
                ranges = {
                        'uL/min': (u'μL', 'min'),
                        'mL/min': (u'mL', 'min'),
                        'uL/hr' : (u'μL', 'hr'),
                        'mL/hr' : (u'mL', 'hr')
                }

                vol_unit, t_unit = ranges[self.pump.get_range()]
                stock, msg = messages[self.pump.get_status()]
                self.builder.get_object('status_image').set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
                self.builder.get_object('status_label').set_text(msg)

                status = None
                img = 'gtk-no'
                try:
                        status = "Connected to %s" % self.pump.get_version()
                        img = 'gtk-yes'
                except:
                        status = "Not connected"

                self.builder.get_object('conn_status').set_text(status)
                self.builder.get_object('conn_status_img').set_from_stock(img, gtk.ICON_SIZE_BUTTON)

                vol = self.pump.get_volume_accum()
                self.builder.get_object('volume').set_text(str(vol))
                self.builder.get_object('volume_unit').set_text(vol_unit)

                rate = self.pump.get_flow_rate()
                self.builder.get_object('flow_rate_status').set_text(str(rate))
                self.builder.get_object('flow_rate_status_unit').set_text('%s/%s' % (vol_unit, t_unit))

                return True

        def direction_changed_cb(self, action, value):
                status = self.pump.get_status()
                if status == 'running' and value == -1 or \
                   status == 'reverse' and value == +1 or \
                   status == 'stalled':
                        self.pump.reverse()
                        
        def edit_diameter_action_activate_cb(self, action):
                diam = self.builder.get_object('diameter').get_value()
                self.pump.set_diameter(diam)

        def run_action_toggled_cb(self, action):
                if action.get_active():
                        dir = self.builder.get_object('dir_forward_action').get_current_value()
                        self.pump.start()
                        if dir < 0:
                                self.pump.reverse()

                else:
                        self.pump.stop()

                self.poll_status()

        def clear_volume_action_activate_cb(self, action):
                self.pump.clear_volume_accum()

        def target_enabled_action_toggled_cb(self, action):
                if action.get_active():
                        self.set_target_volume()
                else:
                        self.pump.clear_target()

        def set_target_volume(self):
                target = self.builder.get_object('volume_target').get_value()
                self.pump.set_target_volume(target)

        def range_changed_cb(self, combo):
                self.set_flow_rate()
                self.update_units()
                
        def update_units(self):
                iter = self.builder.get_object('range').get_active_iter()
                flow_unit = self.range_store.get_value(iter, 0)
                vol_unit = self.range_store.get_value(iter, 1)
                self.builder.get_object('flow_rate_unit').set_text(flow_unit)
                self.builder.get_object('target_volume_unit').set_text(vol_unit)

        def flow_rate_change_value_cb(self, spin_but):
                self.set_flow_rate()

        def set_flow_rate(self):
                iter = self.builder.get_object('range').get_active_iter()
                range = self.range_store.get_value(iter, 2)
                value = self.builder.get_object('flow_rate').get_value()
                self.pump.set_flow_rate(value, range)
                
win = PumpWindow('/dev/ttyS0')
gtk.main()
