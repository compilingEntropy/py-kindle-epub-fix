#!/usr/bin/env python3

from zipfile import ZipFile, Path, ZIP_DEFLATED
import argparse
import os, sys
import re
# import xml.etree.ElementTree as ET
# from lxml import etree as ET
from bs4 import BeautifulSoup
from pprint import pprint

parser = argparse.ArgumentParser(description='This tool will try to fix your EPUB by adding the UTF-8 specification to your EPUB.')

parser.add_argument('infile', help='Path of the epub')
parser.add_argument('outfile', help='Output path for the fixed epub file')
# either in-place or outfile, or output directory
# a quiet mode which changes return based on whether the files needed fixes applied or not
# assume language flag
# dryrun flag
args = parser.parse_args()

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

class EPUBBook:
	def __init__(self, infile, outfile):
		assert(os.path.isfile(infile))
		self.infile = infile
		self.outfile = outfile
		self.fixedProblems = list()

	def _basename(self, filename):
		return filename.split('/').pop()
		# return Path(self.infile, at=filename).name

	def _simplify_language(self, lang):
		return lang.split('-')[0].lower()

	def readEpub(self):
		with ZipFile(self.infile, 'r') as epub:
			self.entries = epub.namelist()
			self.files = dict()
			self.binary_files = dict()
			for filename in self.entries:
				file = Path(epub, filename)
				if file.is_dir():
					continue
				ext = file.suffix
				if file.name == 'mimetype' or ext in ['.html', '.xhtml', '.htm', '.xml', '.svg', '.css', '.opf', '.ncx']:
					self.files[filename] = file.read_text(encoding='utf-8')
				else:
					self.binary_files[filename] = file.read_bytes()

	# Fix linking to body ID showing up as unresolved hyperlink
	def fixBodyIdLink(self):
		bodyIDList = list()

		# Create list of ID tags of <body>
		for filename, html in self.files.items():
			ext = filename.split('.').pop()
			# ext = Path(self.infile, at=filename).suffix.lstrip('.')
			if ext in ['html', 'xhtml']:
				soup = BeautifulSoup(html, 'html.parser') #todo: test
				bodyID = soup.find('body').get('id')
				if bodyID is not None and len(bodyID) > 0:
					linkTarget = self._basename(filename) + '#' + bodyID
					bodyIDList.append((linkTarget, self._basename(filename)))

		# Replace all
		for filename, html in self.files.items():
			for src, target in bodyIDList:
				if src in html:
					self.files[filename] = html.replace(src, target)
					self.fixedProblems.append(f"Replaced link target {src} with {target} in file {filename}.")

	# Fix Language field not defined or not available
	def fixBookLanguage(self):
		# From https://kdp.amazon.com/en_US/help/topic/G200673300
		# Retrieved: 2022-Sep-13
		allowed_languages = [
			# ISO 639-1
			'af', 'gsw', 'ar', 'eu', 'nb', 'br', 'ca', 'zh', 'kw', 'co', 'da', 'nl', 'stq', 'en', 'fi', 'fr', 'fy', 'gl',
			'de', 'gu', 'hi', 'is', 'ga', 'it', 'ja', 'lb', 'mr', 'ml', 'gv', 'frr', 'nb', 'nn', 'pl', 'pt', 'oc', 'rm',
			'sco', 'gd', 'es', 'sv', 'ta', 'cy',

			# ISO 639-2
			'afr', 'ara', 'eus', 'baq', 'nob', 'bre', 'cat', 'zho', 'chi', 'cor', 'cos', 'dan', 'nld', 'dut', 'eng', 'fin',
			'fra', 'fre', 'fry', 'glg', 'deu', 'ger', 'guj', 'hin', 'isl', 'ice', 'gle', 'ita', 'jpn', 'ltz', 'mar', 'mal',
			'glv', 'nor', 'nno', 'por', 'oci', 'roh', 'gla', 'spa', 'swe', 'tam', 'cym', 'wel',
		]

		# Find OPF file
		if 'META-INF/container.xml' not in self.files:
			eprint('Cannot find META-INF/container.xml')
			return
		meta_inf_str = self.files['META-INF/container.xml']
		meta_inf = BeautifulSoup(meta_inf_str, 'xml')
		opf_filename = ''
		for rootfile in meta_inf.find_all('rootfile'):
			if rootfile.get('media-type') == 'application/oebps-package+xml':
				opf_filename = rootfile.get('full-path')

		# Read OPF file
		if opf_filename is None or opf_filename not in self.files:
			eprint('Cannot find OPF file!')
			return

		opf_str = self.files[opf_filename]
		try:
			opf = BeautifulSoup(opf_str, 'xml')
			language_tag = opf.find('dc:language')
			language = 'en'
			original_language = 'undefined'
			if language_tag is None:
				# language = input('E-book does not have a language tag. Please specify the language of the book in RFC 5646 format, e.g. en, fr, ja.')
				pass
			else:
				language = language_tag.text
				original_language = language
			if self._simplify_language(language) not in allowed_languages:
				# language = input(f"Language {language} is not supported by Kindle. Documents may fail to convert. Continue or specify new language of the book in RFC 5646 format, e.g. en, fr, ja.")
				pass
			if language_tag is None:
				language_tag = opf.new_tag('dc:language')
				language_tag.string = language
				opf.find('metadata').append(language_tag)
			else:
				language_tag.string = language
			if language != original_language:
				self.files[opf_filename] = str(opf)
				self.fixedProblems.push(f"Changed document language from {original_language} to {language}.")
		except Exception as e:
			eprint(e)
			eprint('Error trying to parse OPF file as XML.')

	def fixStrayIMG(self):
		for filename, html in self.files.items():
			ext = filename.split('.').pop()
			# ext = Path(self.infile, at=filename).suffix.lstrip('.')
			if ext in ['html', 'xhtml']:
				soup = BeautifulSoup(html, 'xml')
				strayImg = list()
				for img in soup.find_all('img'):
					if 'src' not in img.attrs:
						strayImg.append(img)
				if len(strayImg) > 0:
					for img in strayImg:
						img.decompose()
					self.fixedProblems.append('Removed stray image in ${filename}')
					self.files['filename'] = str(soup)

	# Add UTF-8 encoding declaration if missing
	def fixEncoding(self):
		encoding = '<?xml version="1.0" encoding="utf-8"?>'
		regex = r'''^<\?xml\s+version=["'][\d.]+["']\s+encoding=["'][a-zA-Z\d\-.]+["'].*?\?>'''

		for filename, html in self.files.items():
			ext = filename.split('.').pop()
			if ext in ['html', 'xhtml']:
				html = html.lstrip()
				if not re.match(regex, html, re.I):
					html = encoding + '\n' + html
					self.fixedProblems.append(f"Fixed encoding for file {filename}")
				self.files[filename] = html

	def writeEpub(self):
		with ZipFile(self.outfile, 'w') as outzip:
			# First write mimetype file
			if 'mimetype' in self.files:
				outzip.writestr('mimetype', self.files['mimetype'])

			# Add text file
			for filename, data in self.files.items():
				if filename == 'mimetype':
					# We have already added mimetype file
					continue
				outzip.writestr(filename, data, compress_type=ZIP_DEFLATED)

			# Add binary file
			for filename, data in self.binary_files.items():
				outzip.writestr(filename, data, compress_type=ZIP_DEFLATED)

epub = EPUBBook(args.infile, args.outfile)
epub.readEpub()
epub.fixBodyIdLink()
epub.fixBookLanguage()
epub.fixStrayIMG()
epub.fixEncoding()
epub.writeEpub()

pprint(epub.fixedProblems)
