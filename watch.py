import sys
import time
import os
import logging
import sqlite3
from watchdog.observers import Observer
#from watchdog.events import LoggingEventHandler
from watchdog.events import PatternMatchingEventHandler
import argparse

parser = argparse.ArgumentParser(description='WatchDog')
parser.add_argument("--delay", default=60, metavar="60", help="How long to wait before running scraper", type=int)
parser.add_argument("--path", default='.', metavar="/path/to/watch", help="folder to monitor", type=str)
parser.add_argument("--verbose", default=True, metavar="True/False", help="notify user when files have been created/deleted", type=bool)

args = parser.parse_args()


class EventHandler(PatternMatchingEventHandler):
	info = []
	modifying_files = False
	def on_any_event(self, event):

		if not event.is_directory:
			self.conn = sqlite3.connect('/home/pi/pimame/pimame-menu/database/config.db')
			self.c = self.conn.cursor()
			self.modifying_files = True
			if event.event_type == 'created':
				self.info.append(self.c.execute('SELECT id FROM menu_items WHERE rom_path LIKE "{0}%"'.format(os.path.dirname(event.src_path))).fetchone()[0])
				if args.verbose: print 'new file found:', event.src_path
			if event.event_type == 'deleted':
				self.info.append(self.c.execute('SELECT id FROM menu_items WHERE rom_path LIKE "{0}%"'.format(os.path.dirname(event.src_path))).fetchone()[0])
				if args.verbose: print 'file deleted:', event.src_path

if __name__ == "__main__":
	path = args.path
	event_handler = EventHandler(ignore_patterns=['*.jpg', '*.png', '*.gif', '*.gitkeep'], case_sensitive=False)
	observer = Observer()
	observer.schedule(event_handler, path, recursive=True)
	observer.start()
	try:
		while True:
			time.sleep(args.delay)
			if event_handler.modifying_files:
				event_handler.modifying_files = False
			else:
				if event_handler.info: os.system('python /home/pi/pimame/pimame-menu/scraper/scrape_script.py --platform {0} --verbose {1}'.format(str(set(event_handler.info))[5:-2].replace(' ',''), args.verbose))
				event_handler.info = []
	except KeyboardInterrupt:
		observer.stop()
	observer.join()

