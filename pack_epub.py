#!/usr/bin/env python3

from zipfile import ZipFile, Path, ZIP_DEFLATED
import argparse
import os

parser = argparse.ArgumentParser(description='This tool will package a directory as an epub (useful if you extracted an epub, modified it, and want to pack it back into an epub)')

parser.add_argument('indir', help='Path of the extracted epub')
parser.add_argument('outfile', help='Output path for the epub file')

args = parser.parse_args()
assert(os.path.isdir(args.indir))

# read epub directory
files = list()
for path, dirs, filenames in os.walk(args.indir):
	for file in filenames:
		files.append(os.path.join(path, file))

# write epub
with ZipFile(args.outfile, 'w') as outzip:
	# First write mimetype file
	relative_files = [f.removeprefix(args.indir) for f in files]
	if 'mimetype' in relative_files:
		mimeindex = relative_files.index('mimetype')
		outzip.write(files[mimeindex], files[mimeindex].removeprefix(args.indir))

	# Add remaining files
	for filename in files:
		if filename.endswith('/mimetype') or filename.endswith('/.DS_Store'):
			# We have already added mimetype file and we obviously don't want .ds_store
			continue
		outzip.write(filename, filename.removeprefix(args.indir), compress_type=ZIP_DEFLATED)
