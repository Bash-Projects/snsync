"""
    Note File (local file) functions/settings for snsync
"""
# pylint: disable=W0702
# pylint: disable=C0301

import sys
import os
import string
import hashlib
import time
import datetime
import re

class Note:
    """
        Main Note File (local file) object
    """

    def __init__(self, config, logger):
        """"
            Initial Notes Setup
        """

        self.log = logger
        self.config = config

        # create note dir if it does not exist - cfg_nt_path
        if not os.path.exists(self.config.get_config('cfg_nt_path')):
            try:
                os.mkdir(self.config.get_config('cfg_nt_path'))
                self.log.info("Creating directory %s", self.config.get_config('cfg_nt_path'))
            except:
                self.log.critical("Error creating directory %s", self.config.get_config('cfg_nt_path'))
                self.log.debug("Exception: %s", sys.exc_info()[1])
                sys.exit(1)

        # Try to create Recycle Bin (Trash) - cfg_nt_trashpath
        if not os.path.exists(self.config.get_config('cfg_nt_path') + "/" + self.config.get_config('cfg_nt_trashpath')):
            try:
                os.mkdir(self.config.get_config('cfg_nt_path') + "/" + self.config.get_config('cfg_nt_trashpath'))
                self.log.info("Creating directory %s", self.config.get_config('cfg_nt_path') + "/" + self.config.get_config('cfg_nt_trashpath'))
            except:
                self.log.critical("Error creating directory %s/%s", self.config.get_config('cfg_nt_path'), self.config.get_config('cfg_nt_trashpath'))
                self.log.debug("Exception: %s", sys.exc_info()[1])
                sys.exit(1)

    def new(self, note):
        """
            Create a new note file, returns filename
        """
        path = self.config.get_config('cfg_nt_path')
        filename = self.get_filename(note['content'])
        access_time = time.time()
        filetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")

        if filename:
            if os.path.isfile(path + "/" + filename):
                filename = filetime + "_" + filename  # Don't blast over files with same name, i.e. same first line.

            try:
                f = open(path + "/" + filename, 'w')
                f.write(note['content'])
                f.close()
                self.log.info("Writing %s", filename)

                os.utime(path + "/" + filename, (access_time, float(note['modifydate'])))

                return filename
            except:
                self.log.error("Error writing note: %s", note['key'])
                self.log.debug("Exception: %s", sys.exc_info()[1])
        else:
            self.log.error("Error generating filename for note: %s", note['key'])

        return False

    def get_filename(self, content):
        """
            Generate Safe Filename from Note Content
        """
        note_data = str.splitlines(content)
        line_one = note_data[0]
        file_ext = self.config.get_config('cfg_nt_ext')
        filename_len = int(self.config.get_config('cfg_nt_filenamelen'))

        # http://stackoverflow.com/a/295146
        try:
            safechars = string.ascii_letters + string.digits + " -_."
            safename = ''.join(c for c in line_one if c in safechars)

            if len(safename) >= filename_len: # truncate long names
                safename = safename[:filename_len]

            self.log.debug("Make Safe In: %s Out: %s", line_one, safename)
            filename = safename.strip() + "." + file_ext
            return filename
        except:
            self.log.debug("Exception: %s", sys.exc_info()[1])
            return False

    def gen_meta(self, filename):
        """
            Generate notefile meta from filename - returns dict
        """
        nf_meta = {}
        nf_meta['filename'] = filename
        nf_meta['deleted'] = 0

        # http://stackoverflow.com/a/5297483
        nf_meta['key'] = hashlib.md5(str(filename).encode('utf-8')).hexdigest()
        self.log.debug("Note File Meta Key: %s", nf_meta['key'])

        path = self.config.get_config('cfg_nt_path')

        # WARNING THIS IS PLATFORM SPECIFIC
        nf_meta['createdate'] = os.stat(path + "/" + filename).st_birthtime
        self.log.debug("Note File Meta Created: %s [%s]", nf_meta['createdate'], time.ctime(nf_meta['createdate']))

        nf_meta['modifydate'] = os.stat(path + "/" + filename).st_mtime
        self.log.debug("Note File Meta Modified: %s [%s]", nf_meta['modifydate'], time.ctime(nf_meta['modifydate']))

        return nf_meta

    def update(self, note, nf_meta):
        """
            Create a new note file, returns filename
        """
        path = self.config.get_config('cfg_nt_path')
        filename = nf_meta['filename']
        access_time = time.time()

        try:
            f = open(path + "/" + filename, 'w')
            f.write(note['content'])
            f.close()
            self.log.info("Writing %s", filename)

            os.utime(path + "/" + filename, (access_time, float(note['modifydate'])))

            return True
        except:
            self.log.error("Error writing note: %s", note['key'])
            self.log.debug("Exception: %s", sys.exc_info()[1])

        return False

    def open(self, filename):
        """
            Open a notefile, returns Dict: content & modifydate
        """
        notefile = {}
        path = self.config.get_config('cfg_nt_path')

        if os.path.isfile(path + "/" + filename):
            try:
                f = open(path + "/" + filename, 'r')
                notefile['content'] = f.read()
                f.close()
            except:
                self.log.error("Failed to OPEN/READ: %s", path + "/" + filename)
                self.log.debug("Exception: %s", sys.exc_info()[1])
                return False
        else:
            self.log.error("Notefile not found: %s", path + "/" + filename)
            return False

        notefile['modifydate'] = os.stat(path + "/" + filename).st_mtime
        self.log.debug("Note File Modified: %s [%s]", notefile['modifydate'], time.ctime(notefile['modifydate']))

        if re.match('darwin', sys.platform):
            # WARNING THIS IS PLATFORM SPECIFIC
            notefile['createdate'] = os.stat(path + "/" + filename).st_birthtime
            self.log.debug("Note File Created: %s [%s]", notefile['createdate'], time.ctime(notefile['createdate']))
        else:
            notefile['createdate'] = notefile['modifydate']
            self.log.debug("Using Modify Date for Birth/Create Date")

        return notefile
