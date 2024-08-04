# Kindle EPUB Fix

Amazon Send-to-Kindle service has accepted EPUB, however, for historical reasons it still assumes ISO-8859-1 encoding if no encoding is specified. This creates weird formatting errors for special characters.

This python3 tool will try to fix your EPUB by adding the UTF-8 specification to your EPUB. That is its main purpose. Like the original tool, there are a few other small issues it attempts to fix:

- Certain invalid links
- Missing, invalid, or incompatible book language metadata
- img tags without a source

In this tool, I have performed a 1:1 translation of the code from javascript to python3. Structure, behavior, and even variable names have been maintained wherever possible. A python version of this tool is convenient because it allows easier integration of these fixes into your epub workflows. It also allows easy batch conversion with, for example, a simple bash for loop:

```
mkdir ./eBooks_Fixed/; for file in ./eBooks/*.epub; do echo "$file"; ~/bin/fix_epub.py "$file" "${file/eBooks/eBooks_Fixed}"; done | tee ./epubfix.log
```

There are a lot of opportunities for improvement with this tool:
- Incorporate additional fixes
- Add command line arguments (`--dry-run`, `--in-place`, `--language`, `--quiet`, etc)
- Allow specifying an output directory
- Improvements to the way fixes are printed to console
- Move to `xml.etree.ElementTree` instead of BeautifulSoup for improved speed and portability
- (Even just using `lxml` without BeautifulSoup would improve portability by removing a dependency)

I don't know when or if I will make those changes. For now, I'm committing this version because it is useful and has the same functionality and behavior as the original. PRs are welcome.

**Warning:** This tool come at no warranty. Please still keep your original EPUB.
There is no guarantee the resulting file will be valid EPUB file, but it should be.
