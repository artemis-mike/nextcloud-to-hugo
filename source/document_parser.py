import pypandoc
import logging
import os

class DocumentParser:
    @staticmethod
    def is_supported(filename):
        ext = os.path.splitext(filename)[1].lower()
        return ext in ['.docx', '.odt']

    @staticmethod
    def parse_to_markdown(filepath):
        """
        Parses a .docx or .odt file to Markdown using Pandoc.
        Returns the Markdown string.
        """
        try:
            logging.info(f"Converting {filepath} to Markdown")
            
            # Using pandoc to convert docx or odt to commonmark/markdown
            # We use commonmark to get standard markdown
            
            output = pypandoc.convert_file(
                filepath, 
                'markdown', 
                format=None, # auto-detect format from extension
                extra_args=['--wrap=none'] # prevent hard wrapping of text
            )
            logging.debug(f"Successfully converted {filepath}")
            return output
        except Exception as e:
            logging.error(f"Failed to convert {filepath}: {e}")
            return ""
